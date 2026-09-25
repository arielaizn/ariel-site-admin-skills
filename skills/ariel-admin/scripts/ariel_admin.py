#!/usr/bin/env python3
"""
ariel_admin.py: command line for the admin data of arielaizenshtat.com.

Two doors, both explained in skills/ariel-admin/SKILL.md:

  1. Convex HTTP API (query / mutate / overview / analytics / upload / content-*):
     every admin function of the site's Convex deployment, called with the server secret
     (env ARIEL_ADMIN_API_SECRET = the deployment's ADMIN_API_SECRET). Full read and write.

  2. Admin session (login / logout / act / export-leads / export-list / record-voice):
     the Next.js admin routes, with the admin password (env ARIEL_ADMIN_PASSWORD) and a cookie jar.
     For the few things only the Next server does: CSV exports, Jarvis's assistant API (which also
     refreshes the site's caches), re-recording a voice line.

Python 3.9+, standard library only. Output is JSON on stdout. Errors are JSON on stderr with a
non-zero exit code: 1 = the server refused or the call failed, 2 = bad usage, 3 = missing config.
The secret and the password never appear in the output: every error text is redacted.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import re
import ssl
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

VERSION = "1.0.0"

PROD_CONVEX_URL = "https://affable-kiwi-408.eu-west-1.convex.cloud"
DEV_CONVEX_URL = "https://moonlit-shepherd-589.eu-west-1.convex.cloud"
DEFAULT_SITE_URL = "https://arielaizenshtat-site.vercel.app"
DEFAULT_SITE_REPO = "/Users/a1234/ariel aizenshtat-website"
DEFAULT_ENV_FILE = Path.home() / ".config" / "ariel-admin" / ".env"
COOKIE_NAME = "jarvis_admin"

DAY_MS = 24 * 60 * 60 * 1000
CONTENT_PATH_RE = re.compile(r"^(?:[a-z0-9-]+\.md|work/[a-z0-9-]+\.md)$")
CONTENT_MAX_CHARS = 200_000
LINE_ID_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)*$")
CONVEX_ID_RE = re.compile(r"^[a-z0-9]{10,64}$", re.I)

# ─── Which mutations need an explicit --yes, and which a skill must never call ───────────────────

ALWAYS_YES = {
    "leads:deleteLead": "deletes the lead, its guide history and its mailing-list rows",
    "leads:setMarketingConsent": "changes a legal consent (moves the person on or off the mailing lists)",
    "messages:deleteMessage": "deletes a contact message for good",
    "adminGuides:deleteGuide": "deletes a guide, its files and its events",
    "adminGuides:setGuideFiles": "replaces the guide's files; files no longer referenced are deleted from storage",
    "content:deleteContentFile": "hides a content file from the site",
    "content:restoreContentFile": "drops the admin override; the repo version shows again (a file that exists only in the admin disappears)",
    "media:deleteMedia": "deletes a media file from storage",
    "voice:deleteVoiceLine": "deletes an admin recording; the repo take plays again",
    "voice:saveVoiceLine": "replaces the stored take of a Jarvis line",
    "lists:deleteList": "deletes a list, its members, its campaigns and their deliveries",
    "lists:removeMember": "removes a member from a list",
    "lists:unsubscribe": "unsubscribes an address and withdraws the lead's marketing consent",
    "campaigns:deleteCampaign": "deletes a draft or failed campaign",
    "categories:deleteCategory": "deletes a category",
    "categories:updateCategory": "renames or re-kinds a category (a rename moves every guide that carries it)",
    "files:deleteFile": "deletes a stored file that nothing references",
}

NEVER_CALL = {
    "analytics:ingest": "the site's own event pipeline writes here; fabricated events corrupt the analytics",
    "campaigns:markSending": "the send runs inside the Next server (lib/mailing/send.ts); press Send in /admin/campaigns/<id>",
    "campaigns:recordDeliveries": "written by the send loop only",
    "campaigns:markSent": "written by the send loop only",
    "campaigns:markFailed": "written by the send loop only",
    "campaigns:markTestSent": "written by the test send only",
    "leads:recordGuideEvent": "written by the site when an unlocked visitor reads or downloads",
    "leads:upsertLead": "the sign-up gate's own path (it records an unlock event); a manual member goes through lists:addMember",
    "lists:enrollLead": "called by the sign-up gate after leads:upsertLead",
    "messages:createMessage": "the contact form's own path; the admin does not write messages",
}


def conditional_yes(path: str, args: dict) -> Optional[str]:
    """Mutations that are destructive only with certain arguments."""
    if path in ("adminGuides:setGuidePublished", "adminGuides:setBundlePublished") and args.get("published") is False:
        return "takes a guide or a bundle off the site"
    if path == "settings:setSetting":
        key = args.get("key")
        value = args.get("value")
        if key == "guidesGate" and isinstance(value, dict) and value.get("enabled") is False:
            return "opens every full guide to visitors without a sign-up"
        if key == "mailing.autoEnroll" and value == "all":
            return "makes sign-ups without the marketing tick mailable (Ariel's legal call)"
    return None


# ─── Config ─────────────────────────────────────────────────────────────────────────────────────


def load_env_file(path: Path) -> int:
    """KEY=VALUE lines (quotes optional, # comments). Keys already in the environment win."""
    if not path.is_file():
        return 0
    loaded = 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value
            loaded += 1
    return loaded


class Config:
    def __init__(self, ns: argparse.Namespace):
        env_file = Path(ns.env_file) if getattr(ns, "env_file", None) else Path(os.environ.get("ARIEL_ENV_FILE", str(DEFAULT_ENV_FILE)))
        self.env_file = env_file
        load_env_file(env_file)
        self.dev = bool(getattr(ns, "dev", False))
        if self.dev:
            self.convex_url = os.environ.get("ARIEL_CONVEX_URL_DEV", DEV_CONVEX_URL).rstrip("/")
        else:
            self.convex_url = os.environ.get("ARIEL_CONVEX_URL", PROD_CONVEX_URL).rstrip("/")
        self.site_url = (getattr(ns, "site", None) or os.environ.get("ARIEL_SITE_URL", DEFAULT_SITE_URL)).rstrip("/")
        self.secret = (os.environ.get("ARIEL_ADMIN_API_SECRET") or os.environ.get("ADMIN_API_SECRET") or "").strip()
        self.password = (os.environ.get("ARIEL_ADMIN_PASSWORD") or os.environ.get("ADMIN_PASSWORD") or "").strip()
        self.site_repo = Path(os.environ.get("ARIEL_SITE_REPO", DEFAULT_SITE_REPO))
        host = urllib.parse.urlparse(self.site_url).netloc.replace(":", "_")
        self.cookie_jar = Path(os.environ.get("ARIEL_ADMIN_COOKIE_JAR", str(Path.home() / ".cache" / "ariel-admin" / f"cookies-{host}.txt")))

    def redact(self, text: str) -> str:
        for value in (self.secret, self.password):
            if value:
                text = text.replace(value, "***")
        return text


# ─── HTTP ───────────────────────────────────────────────────────────────────────────────────────


def ssl_context() -> ssl.SSLContext:
    """A verified context that also works with a python.org build that never ran Install Certificates."""
    candidates = [os.environ.get("SSL_CERT_FILE")]
    try:
        import certifi  # type: ignore

        candidates.append(certifi.where())
    except Exception:
        pass
    candidates += ["/etc/ssl/cert.pem", "/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt"]
    for cafile in candidates:
        if cafile and os.path.isfile(cafile):
            return ssl.create_default_context(cafile=cafile)
    return ssl.create_default_context()


_CTX = None


def ctx() -> ssl.SSLContext:
    global _CTX
    if _CTX is None:
        _CTX = ssl_context()
    return _CTX


class HttpResult:
    def __init__(self, status: int, headers: Any, body: bytes):
        self.status = status
        self.headers = headers
        self.body = body

    def json(self) -> Any:
        try:
            return json.loads(self.body.decode("utf-8"))
        except Exception:
            return None

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


def fetch(method: str, url: str, *, body: Optional[bytes] = None, headers: Optional[dict] = None, jar: Optional[http.cookiejar.CookieJar] = None, timeout: int = 60) -> HttpResult:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    req.add_header("User-Agent", f"ariel-admin-cli/{VERSION}")
    handlers: list = [urllib.request.HTTPSHandler(context=ctx())]
    if jar is not None:
        handlers.append(urllib.request.HTTPCookieProcessor(jar))
    opener = urllib.request.build_opener(*handlers)
    try:
        with opener.open(req, timeout=timeout) as res:
            return HttpResult(res.status, res.headers, res.read())
    except urllib.error.HTTPError as e:
        return HttpResult(e.code, e.headers, e.read())


# ─── Errors and output ───────────────────────────────────────────────────────────────────────────


class CliError(Exception):
    def __init__(self, message: str, code: int = 1, **extra: Any):
        super().__init__(message)
        self.code = code
        self.extra = extra


def tidy(value: Any) -> Any:
    """Convex's JSON format writes every number as a float (880.0). Integral floats become ints."""
    if isinstance(value, float) and value.is_integer() and abs(value) < 2**53:
        return int(value)
    if isinstance(value, list):
        return [tidy(v) for v in value]
    if isinstance(value, dict):
        return {k: tidy(v) for k, v in value.items()}
    return value


def emit(value: Any, compact: bool = False) -> None:
    text = json.dumps(tidy(value), ensure_ascii=False, indent=None if compact else 2)
    sys.stdout.write(text + "\n")


def now_ms() -> int:
    return int(time.time() * 1000)


def parse_json_arg(text: Optional[str]) -> dict:
    if not text or not text.strip():
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError as e:
        raise CliError(f"--args is not valid JSON: {e}", 2)
    if not isinstance(value, dict):
        raise CliError("--args must be a JSON object", 2)
    return value


# ─── Convex ─────────────────────────────────────────────────────────────────────────────────────


def convex(cfg: Config, kind: str, path: str, args: dict, *, with_secret: bool = True) -> Any:
    if with_secret and not cfg.secret:
        raise CliError("ARIEL_ADMIN_API_SECRET is not set (the Convex deployment's ADMIN_API_SECRET). See README.", 3)
    payload = {"path": path, "args": ({**args, "secret": cfg.secret} if with_secret else args), "format": "json"}
    res = fetch("POST", f"{cfg.convex_url}/api/{kind}", body=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
    data = res.json()
    if not isinstance(data, dict):
        raise CliError(cfg.redact(f"Convex returned HTTP {res.status} without JSON: {res.text()[:300]}"), 1, http=res.status)
    if data.get("status") == "success":
        return data.get("value")
    message = cfg.redact(str(data.get("errorMessage") or data.get("message") or data))
    error_data = data.get("errorData")
    if error_data == "forbidden":
        raise CliError("Convex refused the secret (forbidden): ARIEL_ADMIN_API_SECRET does not match this deployment.", 1, errorData=error_data, deployment=cfg.convex_url)
    if "Could not find public function" in message:
        raise CliError(f"no such function: {path}", 1, hint="see references/convex-functions.md")
    raise CliError(message.strip(), 1, errorData=cfg.redact(json.dumps(error_data, ensure_ascii=False)) if error_data is not None else None)


def paginate_all(cfg: Config, path: str, args: dict, max_items: int) -> Any:
    opts = dict(args.get("paginationOpts") or {"numItems": 200, "cursor": None})
    opts.setdefault("numItems", 200)
    opts["cursor"] = opts.get("cursor")
    items: list = []
    pages = 0
    while True:
        result = convex(cfg, "query", path, {**args, "paginationOpts": opts})
        if not isinstance(result, dict) or "page" not in result:
            return result
        items.extend(result["page"])
        pages += 1
        if result.get("isDone") or len(items) >= max_items:
            return {"page": items[:max_items], "isDone": bool(result.get("isDone")), "pages": pages, "count": min(len(items), max_items)}
        opts = {**opts, "cursor": result.get("continueCursor")}


# ─── Admin session ───────────────────────────────────────────────────────────────────────────────


def load_jar(cfg: Config) -> http.cookiejar.MozillaCookieJar:
    jar = http.cookiejar.MozillaCookieJar(str(cfg.cookie_jar))
    if cfg.cookie_jar.is_file():
        try:
            jar.load(ignore_discard=True, ignore_expires=True)
        except Exception:
            pass
    return jar


def save_jar(cfg: Config, jar: http.cookiejar.MozillaCookieJar) -> None:
    cfg.cookie_jar.parent.mkdir(parents=True, exist_ok=True)
    jar.save(ignore_discard=True, ignore_expires=True)
    try:
        os.chmod(cfg.cookie_jar, 0o600)
    except Exception:
        pass


def session_expiry(jar: http.cookiejar.CookieJar) -> Optional[int]:
    """The session cookie is v1.<expiresAtMs>.<nonce>.<hmac>; the expiry is readable without the secret."""
    for cookie in jar:
        if cookie.name == COOKIE_NAME and cookie.value:
            parts = cookie.value.split(".")
            if len(parts) == 4 and parts[0] == "v1" and parts[1].isdigit():
                return int(parts[1])
    return None


def login(cfg: Config) -> dict:
    if not cfg.password:
        raise CliError("ARIEL_ADMIN_PASSWORD is not set (the site's ADMIN_PASSWORD). See README.", 3)
    jar = http.cookiejar.MozillaCookieJar(str(cfg.cookie_jar))
    res = fetch("POST", f"{cfg.site_url}/api/admin/login", body=json.dumps({"password": cfg.password}).encode("utf-8"), headers={"Content-Type": "application/json"}, jar=jar)
    data = res.json() or {}
    if res.status == 200 and data.get("ok"):
        save_jar(cfg, jar)
        expires = session_expiry(jar)
        return {"ok": True, "site": cfg.site_url, "expiresAt": expires, "expiresInHours": round((expires - now_ms()) / 3_600_000, 1) if expires else None, "cookieJar": str(cfg.cookie_jar)}
    error = data.get("error") or f"http {res.status}"
    hints = {
        "wrong_password": "the password does not match the site's ADMIN_PASSWORD. Do not retry blindly: 5 failures per 15 minutes lock the IP.",
        "rate_limited": f"too many attempts; wait {data.get('retryAfterSec')} seconds",
        "not_configured": "the site has no ADMIN_PASSWORD / ADMIN_SESSION_SECRET set",
        "forbidden": "the request looked cross-site (an Origin header?)",
    }
    raise CliError(f"login failed: {error}", 1, hint=hints.get(error), status=res.status)


def ensure_session(cfg: Config) -> http.cookiejar.MozillaCookieJar:
    jar = load_jar(cfg)
    expires = session_expiry(jar)
    if expires and expires - now_ms() > 60_000:
        return jar
    if cfg.password:
        login(cfg)
        return load_jar(cfg)
    raise CliError("no admin session: run `login` (needs ARIEL_ADMIN_PASSWORD)", 3)


def admin_request(cfg: Config, method: str, path: str, *, body: Optional[dict] = None, timeout: int = 60) -> HttpResult:
    jar = ensure_session(cfg)
    headers = {"Accept": "application/json, text/csv"}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    res = fetch(method, f"{cfg.site_url}{path}", body=data, headers=headers, jar=jar, timeout=timeout)
    if res.status == 401:
        raise CliError("the admin session is not valid any more: run `login` again", 1, status=401)
    if res.status == 403:
        raise CliError("forbidden: the site treated the request as cross-site", 1, status=403)
    return res


# ─── Image dimensions (for media rows and posters) ───────────────────────────────────────────────


def image_size(data: bytes) -> Optional[tuple]:
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            return struct.unpack(">II", data[16:24])
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return struct.unpack("<HH", data[6:10])
        if data[:2] == b"\xff\xd8":
            i = 2
            while i < len(data) - 9:
                if data[i] != 0xFF:
                    i += 1
                    continue
                marker = data[i + 1]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                    i += 2
                    continue
                length = struct.unpack(">H", data[i + 2 : i + 4])[0]
                if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    height, width = struct.unpack(">HH", data[i + 5 : i + 9])
                    return (width, height)
                i += 2 + length
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            chunk = data[12:16]
            if chunk == b"VP8X":
                w = 1 + int.from_bytes(data[24:27], "little")
                h = 1 + int.from_bytes(data[27:30], "little")
                return (w, h)
            if chunk == b"VP8 ":
                w = struct.unpack("<H", data[26:28])[0] & 0x3FFF
                h = struct.unpack("<H", data[28:30])[0] & 0x3FFF
                return (w, h)
            if chunk == b"VP8L":
                b = data[21:25]
                w = 1 + (b[0] | ((b[1] & 0x3F) << 8))
                h = 1 + ((b[1] >> 6) | (b[2] << 2) | ((b[3] & 0x0F) << 10))
                return (w, h)
    except Exception:
        return None
    return None


MIME_BY_EXT = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif", ".avif": "image/avif", ".svg": "image/svg+xml",
    ".mp4": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".ogg": "audio/ogg",
    ".pdf": "application/pdf", ".zip": "application/zip", ".json": "application/json", ".txt": "text/plain", ".md": "text/markdown", ".csv": "text/csv",
}


def kind_of(mime: str) -> str:
    if mime.startswith("image/"):
        return "image"
    if mime.startswith("video/"):
        return "video"
    if mime.startswith("audio/"):
        return "audio"
    if mime == "application/pdf":
        return "pdf"
    return "other"


# ─── Commands ───────────────────────────────────────────────────────────────────────────────────


def cmd_query(cfg: Config, ns: argparse.Namespace) -> Any:
    args = parse_json_arg(ns.args)
    if ns.all:
        return paginate_all(cfg, ns.path, args, ns.max)
    return convex(cfg, "query", ns.path, args)


def cmd_mutate(cfg: Config, ns: argparse.Namespace) -> Any:
    args = parse_json_arg(ns.args)
    path = ns.path
    if path in NEVER_CALL and not ns.force:
        raise CliError(f"{path} is not for the admin CLI: {NEVER_CALL[path]}", 2, hint="--force overrides, at your own risk")
    reason = ALWAYS_YES.get(path) or conditional_yes(path, args)
    if reason and not ns.yes:
        raise CliError(f"{path} needs --yes: it {reason}. Read back to Ariel exactly what will happen, get his yes, then add --yes.", 2)
    result = convex(cfg, "mutation", path, args)
    return {"ok": True, "path": path, "result": result}


def summary_period(ns: argparse.Namespace) -> dict:
    to = now_ms()
    if getattr(ns, "from_day", None) or getattr(ns, "to_day", None):
        if not (ns.from_day and ns.to_day):
            raise CliError("--from and --to go together (YYYY-MM-DD, UTC)", 2)
        frm = int(time.mktime(time.strptime(ns.from_day, "%Y-%m-%d")) - time.timezone) * 1000
        to = int(time.mktime(time.strptime(ns.to_day, "%Y-%m-%d")) - time.timezone) * 1000 + DAY_MS
        days = max(1, round((to - frm) / DAY_MS))
    else:
        days = max(1, min(400, int(ns.days)))
        frm = ((to - (days - 1) * DAY_MS) // DAY_MS) * DAY_MS
    return {"from": frm, "to": to, "days": days, "fromIso": time.strftime("%Y-%m-%d", time.gmtime(frm / 1000)), "toIso": time.strftime("%Y-%m-%d", time.gmtime((to - 1) / 1000))}


def brief_summary(s: dict) -> dict:
    top = lambda rows, n=5: [{"key": r["key"], "count": r["count"]} for r in rows[:n]]  # noqa: E731
    return {
        "capped": s.get("capped"),
        "pageviews": s.get("pageviews"), "visitors": s.get("visitors"), "sessions": s.get("sessions"), "bounces": s.get("bounces"), "dailyIps": s.get("dailyIps"),
        "topPages": top(s.get("topPages", [])), "devices": top(s.get("devices", [])), "countries": top(s.get("countries", [])), "referrers": top(s.get("referrers", [])), "utmSources": top(s.get("utmSources", [])),
        "commands": {"total": s["commands"]["total"], "fastpath": s["commands"]["fastpath"], "llm": s["commands"]["llm"], "topIntents": top(s["commands"]["byIntent"]), "bySource": top(s["commands"]["bySource"]), "unknown": s["commands"]["unknown"][:10]},
        "voice": s.get("voice"), "clap": s.get("clap"), "holo": s.get("holo"), "jarvis": s.get("jarvis"),
        "guides": {k: v for k, v in s.get("guides", {}).items() if k != "byGuide"}, "guidesByGuide": s.get("guides", {}).get("byGuide", [])[:10],
        "contact": s.get("contact"), "media": s.get("media"), "errors": top(s.get("errors", []), 10),
        "latency": s.get("latency"),
    }


def cmd_analytics(cfg: Config, ns: argparse.Namespace) -> Any:
    period = summary_period(ns)
    summary = convex(cfg, "query", "analytics:summary", {"from": period["from"], "to": period["to"]})
    body = brief_summary(summary) if ns.brief else summary
    if ns.section:
        if ns.section not in summary:
            raise CliError(f"unknown section {ns.section}; top-level keys: {', '.join(sorted(summary.keys()))}", 2)
        body = {ns.section: summary[ns.section]}
    return {"period": period, "deployment": cfg.convex_url, "summary": body}


def settle(fn):
    try:
        return fn(), None
    except CliError as e:
        return None, str(e)
    except Exception as e:  # network etc.
        return None, str(e)


def cmd_overview(cfg: Config, ns: argparse.Namespace) -> Any:
    out: dict = {"at": now_ms(), "deployment": cfg.convex_url, "errors": {}}

    def part(name, fn):
        value, err = settle(fn)
        if err:
            out["errors"][name] = cfg.redact(err)
        return value

    leads = part("leads", lambda: convex(cfg, "query", "leads:leadStats", {}))
    messages = part("messages", lambda: convex(cfg, "query", "messages:messageStats", {}))
    guides = part("guides", lambda: convex(cfg, "query", "adminGuides:listAllGuides", {}))
    bundles = part("bundles", lambda: convex(cfg, "query", "adminGuides:listAllBundles", {}))
    media = part("media", lambda: convex(cfg, "query", "media:mediaStats", {}))
    members = part("mailing", lambda: convex(cfg, "query", "lists:memberStats", {}))
    campaigns = part("campaigns", lambda: convex(cfg, "query", "campaigns:listCampaigns", {}))
    categories = part("categories", lambda: convex(cfg, "query", "categories:listCategories", {}))
    gate = part("gate", lambda: convex(cfg, "query", "settings:getSetting", {"key": "guidesGate"}))
    content = part("content", lambda: convex(cfg, "query", "content:listContentFiles", {}))
    log = part("log", lambda: convex(cfg, "query", "adminLog:listLog", {"limit": 5}))
    to = now_ms()
    frm = ((to - 6 * DAY_MS) // DAY_MS) * DAY_MS
    analytics = part("analytics", lambda: convex(cfg, "query", "analytics:summary", {"from": frm, "to": to}))

    today = time.strftime("%Y-%m-%d", time.gmtime())
    out["leads"] = {"total": leads["total"], "last7d": leads["last7d"], "consented": leads["consented"], "topGuides": leads["topGuides"][:5]} if leads else None
    out["messages"] = messages
    out["guides"] = {"published": sum(1 for g in guides if g["published"]), "drafts": sum(1 for g in guides if not g["published"]), "bundles": len(bundles or []), "list": [{"slug": g["slug"], "title": g["title"], "published": g["published"], "category": g["category"]} for g in guides]} if guides is not None else None
    out["media"] = media["total"] if media else None
    out["mailing"] = members
    out["campaigns"] = {"total": len(campaigns), "byStatus": {s: sum(1 for c in campaigns if c["status"] == s) for s in ("draft", "sending", "sent", "failed")}} if campaigns is not None else None
    out["categories"] = len(categories) if categories is not None else None
    out["gate"] = (gate is None) or (isinstance(gate.get("value"), dict) and gate["value"].get("enabled") is not False) if "gate" not in out["errors"] else None
    out["contentOverrides"] = [{"path": f["path"], "deleted": f["deleted"], "updatedAt": f["updatedAt"]} for f in content] if content is not None else None
    out["analytics7d"] = {
        "pageviewsToday": next((d["count"] for d in analytics["pageviewsByDay"] if d["day"] == today), 0),
        "pageviews": analytics["pageviews"], "visitors": analytics["visitors"], "sessions": analytics["sessions"], "commands": analytics["commands"]["total"],
        "unknownIntents": len(analytics["commands"]["unknown"]), "voiceSessions": analytics["voice"]["started"], "errors": analytics["errors"][:5], "capped": analytics["capped"],
    } if analytics else None
    out["recentLog"] = log
    if not out["errors"]:
        del out["errors"]
    return out


def cmd_login(cfg: Config, ns: argparse.Namespace) -> Any:
    return login(cfg)


def cmd_logout(cfg: Config, ns: argparse.Namespace) -> Any:
    jar = load_jar(cfg)
    fetch("POST", f"{cfg.site_url}/api/admin/logout", headers={"Content-Type": "application/json"}, body=b"{}", jar=jar)
    if cfg.cookie_jar.is_file():
        cfg.cookie_jar.unlink()
    return {"ok": True}


def cmd_act(cfg: Config, ns: argparse.Namespace) -> Any:
    body = {"name": ns.name, "kind": ns.kind, "args": parse_json_arg(ns.args), "confirmed": bool(ns.confirmed)}
    res = admin_request(cfg, "POST", "/api/admin/assistant/act", body=body)
    data = res.json()
    if data is None:
        raise CliError(cfg.redact(f"the assistant API answered HTTP {res.status} without JSON: {res.text()[:300]}"), 1)
    if res.status == 409:
        raise CliError("this act is destructive: read it back to Ariel, get an explicit yes, then repeat with --confirmed", 1, response=data)
    if res.status >= 400 or data.get("ok") is False:
        raise CliError(cfg.redact(str(data.get("error") or f"http {res.status}")), 1, response=data)
    data.pop("display", None)
    return data


def write_output(ns: argparse.Namespace, body: bytes, default_name: str) -> dict:
    target = getattr(ns, "output", None)
    if target == "-":
        sys.stdout.write(body.decode("utf-8-sig"))
        return {"ok": True, "bytes": len(body), "to": "stdout"}
    path = Path(target) if target else Path.cwd() / default_name
    path.write_bytes(body)
    return {"ok": True, "bytes": len(body), "file": str(path), "rows": max(0, body.decode("utf-8-sig").count("\n") - 1)}


def cmd_export_leads(cfg: Config, ns: argparse.Namespace) -> Any:
    query = "?consent=1" if ns.consent else ""
    res = admin_request(cfg, "GET", f"/api/admin/leads/export{query}")
    if res.status != 200:
        raise CliError(cfg.redact(f"export failed: http {res.status} {res.text()[:200]}"), 1)
    day = time.strftime("%Y-%m-%d")
    return write_output(ns, res.body, f"leads{'-consent' if ns.consent else ''}-{day}.csv")


def cmd_export_list(cfg: Config, ns: argparse.Namespace) -> Any:
    if not CONVEX_ID_RE.match(ns.list_id):
        raise CliError("listId must be a Convex id (query lists:listLists shows them)", 2)
    res = admin_request(cfg, "GET", f"/api/admin/lists/{ns.list_id}/export")
    if res.status != 200:
        raise CliError(cfg.redact(f"export failed: http {res.status} {res.text()[:200]}"), 1)
    return write_output(ns, res.body, f"list-{ns.list_id[:8]}-{time.strftime('%Y-%m-%d')}.csv")


def cmd_record_voice(cfg: Config, ns: argparse.Namespace) -> Any:
    if not LINE_ID_RE.match(ns.line_id) or len(ns.line_id) > 80:
        raise CliError("lineId looks like control.stop or boot.greeting", 2)
    res = admin_request(cfg, "POST", "/api/admin/voice/record", body={"lineId": ns.line_id}, timeout=120)
    data = res.json() or {"raw": res.text()[:400]}
    if res.status != 200:
        raise CliError(cfg.redact(f"recording failed: http {res.status} {data.get('error', '')}"), 1, response=data)
    return data


def cmd_upload(cfg: Config, ns: argparse.Namespace) -> Any:
    path = Path(ns.file)
    if not path.is_file():
        raise CliError(f"no such file: {path}", 2)
    data = path.read_bytes()
    mime = (ns.mime or MIME_BY_EXT.get(path.suffix.lower()) or "application/octet-stream").split(";")[0].strip().lower()
    upload_url = convex(cfg, "mutation", "files:generateUploadUrl", {})
    res = fetch("POST", upload_url, body=data, headers={"Content-Type": mime}, timeout=600)
    payload = res.json() or {}
    storage_id = payload.get("storageId")
    if res.status != 200 or not storage_id:
        raise CliError(cfg.redact(f"upload failed: http {res.status} {res.text()[:200]}"), 1)
    out: dict = {"storageId": storage_id, "mime": mime, "bytes": len(data)}
    size = image_size(data) if mime.startswith("image/") else None
    if size:
        out["width"], out["height"] = size
    if ns.no_register:
        out["url"] = convex(cfg, "query", "files:getFileUrl", {"storageId": storage_id})
        out["registered"] = False
        return out
    args = {"storageId": storage_id, "name": ns.name or path.name, "kind": ns.kind or kind_of(mime), "mime": mime, "size": len(data)}
    if size:
        args["width"], args["height"] = size
    if ns.alt:
        args["alt"] = ns.alt
    row = convex(cfg, "mutation", "media:createMedia", args)
    out["registered"] = True
    out["media"] = row
    out["url"] = row.get("url") if isinstance(row, dict) else None
    return out


def repo_content_file(cfg: Config, rel: str) -> Optional[str]:
    file = cfg.site_repo / "content" / rel
    return file.read_text(encoding="utf-8") if file.is_file() else None


def cmd_content_get(cfg: Config, ns: argparse.Namespace) -> Any:
    rel = ns.path
    if not CONTENT_PATH_RE.match(rel):
        raise CliError("path looks like about.md or work/<slug>.md", 2)
    row = None if ns.source == "repo" else convex(cfg, "query", "content:getContentFile", {"path": rel})
    if row and not row.get("deleted") and ns.source != "repo":
        body, source, updated = row["body"], "override", row["updatedAt"]
    elif row and row.get("deleted") and ns.source == "auto":
        body, source, updated = None, "deleted", row["updatedAt"]
    else:
        text = repo_content_file(cfg, rel)
        body, source, updated = text, ("repo" if text is not None else "missing"), None
    if ns.output and body is not None:
        Path(ns.output).write_text(body, encoding="utf-8")
    if ns.raw:
        if body is None:
            raise CliError(f"{rel}: {source}", 1)
        sys.stdout.write(body)
        return None
    return {"path": rel, "source": source, "updatedAt": updated, "repoAvailable": (cfg.site_repo / "content").is_dir(), "chars": len(body) if body else 0, **({} if ns.output or body is None else {"body": body}), **({"file": ns.output} if ns.output and body is not None else {})}


CHECK_SCRIPT = """import { readFileSync } from 'node:fs';
import { checkContentFile } from './lib/content';
const [file, raw] = [process.argv[2], readFileSync(process.argv[3], 'utf8')];
const res = checkContentFile(file, raw);
process.stdout.write(JSON.stringify({ ok: res.ok, issues: res.issues ?? [] }));
"""


def run_site_checker(cfg: Config, rel: str, text: str) -> Optional[dict]:
    """checkContentFile() from the site repo, the same parser the admin editor refuses on. None when unavailable."""
    repo = cfg.site_repo
    if not (repo / "lib" / "content" / "index.ts").is_file() or not (repo / "node_modules").is_dir():
        return None
    script = repo / ".ariel-admin-check.tmp.ts"
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as tmp:
        tmp.write(text)
        tmp_path = tmp.name
    try:
        script.write_text(CHECK_SCRIPT, encoding="utf-8")
        proc = subprocess.run(["npx", "tsx", "--conditions=react-server", str(script), rel, tmp_path], cwd=str(repo), capture_output=True, text=True, timeout=180)
        if proc.returncode != 0:
            return {"ok": None, "error": (proc.stderr or proc.stdout)[-800:]}
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as e:
        return {"ok": None, "error": str(e)}
    finally:
        for p in (script, Path(tmp_path)):
            try:
                p.unlink()
            except Exception:
                pass


def cmd_content_check(cfg: Config, ns: argparse.Namespace) -> Any:
    if not CONTENT_PATH_RE.match(ns.path):
        raise CliError("path looks like about.md or work/<slug>.md", 2)
    text = Path(ns.file).read_text(encoding="utf-8")
    result = run_site_checker(cfg, ns.path, text)
    if result is None:
        raise CliError(f"the site checker needs the repo with node_modules at {cfg.site_repo} (ARIEL_SITE_REPO)", 3)
    return {"path": ns.path, "chars": len(text), **result}


def cmd_content_save(cfg: Config, ns: argparse.Namespace) -> Any:
    rel = ns.path
    if not CONTENT_PATH_RE.match(rel):
        raise CliError("path looks like about.md or work/<slug>.md", 2)
    text = Path(ns.file).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if len(text) > CONTENT_MAX_CHARS:
        raise CliError(f"the file is longer than {CONTENT_MAX_CHARS} characters", 2)
    check: Optional[dict] = None
    if not ns.no_check:
        check = run_site_checker(cfg, rel, text)
        if check is None:
            sys.stderr.write(json.dumps({"warning": f"site checker unavailable (no repo at {cfg.site_repo}); saving unchecked"}) + "\n")
        elif check.get("ok") is False:
            raise CliError("the site could not read this file; nothing was saved", 1, issues=check.get("issues"))
        elif check.get("ok") is None:
            raise CliError("the site checker failed to run; use --no-check to save anyway", 1, error=check.get("error"))
    updated = convex(cfg, "mutation", "content:saveContentFile", {"path": rel, "body": text})
    return {"ok": True, "path": rel, "updatedAt": updated, "chars": len(text), "checked": bool(check and check.get("ok")), "refresh": "pages read the new text within 5 minutes (CONTENT_REVALIDATE); Jarvis's brain within a further minute. An admin save in /admin/content refreshes at once."}


def cmd_doctor(cfg: Config, ns: argparse.Namespace) -> Any:
    report: dict = {
        "envFile": {"path": str(cfg.env_file), "found": cfg.env_file.is_file()},
        "convex": {"url": cfg.convex_url, "target": "dev" if cfg.dev else "prod", "secretSet": bool(cfg.secret)},
        "site": {"url": cfg.site_url, "passwordSet": bool(cfg.password), "cookieJar": str(cfg.cookie_jar)},
        "siteRepo": {"path": str(cfg.site_repo), "found": (cfg.site_repo / "content").is_dir(), "nodeModules": (cfg.site_repo / "node_modules").is_dir()},
    }
    value, err = settle(lambda: convex(cfg, "query", "guides:listPublished", {}, with_secret=False))
    report["convex"]["reachable"] = err is None
    report["convex"]["publishedGuides"] = len(value) if isinstance(value, list) else None
    if err:
        report["convex"]["error"] = cfg.redact(err)
    if cfg.secret:
        value, err = settle(lambda: convex(cfg, "query", "settings:listSettings", {}))
        report["convex"]["secretValid"] = err is None
        if err:
            report["convex"]["secretError"] = cfg.redact(err)
    value, err = settle(lambda: fetch("GET", f"{cfg.site_url}/api/voice/manifest", timeout=30))
    report["site"]["reachable"] = err is None and value is not None and value.status == 200
    jar = load_jar(cfg)
    expires = session_expiry(jar)
    report["site"]["session"] = {"present": expires is not None, "expiresAt": expires, "valid": bool(expires and expires > now_ms())}
    if report["site"]["session"]["valid"]:
        value, err = settle(lambda: admin_request(cfg, "POST", "/api/admin/assistant/act", body={"name": "query", "kind": "settings", "args": {}}))
        report["site"]["session"]["accepted"] = err is None and value is not None and value.status == 200
    report["ok"] = bool(report["convex"].get("reachable") and report["convex"].get("secretValid", False))
    return report


# ─── Argument parser ─────────────────────────────────────────────────────────────────────────────


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ariel_admin.py", description="Admin data of arielaizenshtat.com: Convex functions + the admin session.")
    p.add_argument("--dev", action="store_true", help="use the dev Convex deployment (ARIEL_CONVEX_URL_DEV) instead of production")
    p.add_argument("--site", help="site origin for session commands (default ARIEL_SITE_URL or the Vercel production URL)")
    p.add_argument("--env-file", help="KEY=VALUE file to load first (default ARIEL_ENV_FILE or ~/.config/ariel-admin/.env)")
    p.add_argument("--compact", action="store_true", help="one-line JSON output")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="command", required=True)

    q = sub.add_parser("query", help="run a Convex query (the secret is added)")
    q.add_argument("path", help="module:function, e.g. leads:leadStats")
    q.add_argument("--args", help="JSON object of arguments")
    q.add_argument("--all", action="store_true", help="follow paginationOpts cursors and return every row")
    q.add_argument("--max", type=int, default=20000, help="row cap for --all (default 20000)")
    q.set_defaults(fn=cmd_query)

    m = sub.add_parser("mutate", help="run a Convex mutation (the secret is added; destructive ones need --yes)")
    m.add_argument("path")
    m.add_argument("--args", help="JSON object of arguments")
    m.add_argument("--yes", action="store_true", help="confirm a destructive mutation after Ariel said yes")
    m.add_argument("--force", action="store_true", help="run a function the CLI normally refuses")
    m.set_defaults(fn=cmd_mutate)

    o = sub.add_parser("overview", help="every admin number at once (leads, messages, guides, media, mailing, analytics 7d, gate, overrides, log)")
    o.set_defaults(fn=cmd_overview)

    a = sub.add_parser("analytics", help="analytics:summary for a period")
    a.add_argument("--days", type=int, default=30, help="last N days including today (default 30)")
    a.add_argument("--from", dest="from_day", help="YYYY-MM-DD (UTC), with --to")
    a.add_argument("--to", dest="to_day", help="YYYY-MM-DD (UTC, inclusive), with --from")
    a.add_argument("--brief", action="store_true", help="the headline numbers only")
    a.add_argument("--section", help="one top-level section only (commands, guides, latency, ...)")
    a.set_defaults(fn=cmd_analytics)

    sub.add_parser("login", help="sign in to the admin (ARIEL_ADMIN_PASSWORD) and keep the cookie").set_defaults(fn=cmd_login)
    sub.add_parser("logout", help="end the admin session and delete the cookie").set_defaults(fn=cmd_logout)

    ac = sub.add_parser("act", help="POST /api/admin/assistant/act: Jarvis's admin tools (session)")
    ac.add_argument("name", choices=["query", "act"])
    ac.add_argument("kind", help="a query kind (overview, leads, ...) or an act kind (guide_publish, ...)")
    ac.add_argument("--args", help="JSON object: n, q, consentOnly, id, email, status, slug, title, direction, mediaKind, days, lineId, path")
    ac.add_argument("--confirmed", action="store_true", help="destructive acts, after Ariel's explicit yes")
    ac.set_defaults(fn=cmd_act)

    el = sub.add_parser("export-leads", help="CSV of every lead (session; logged in the admin log)")
    el.add_argument("--consent", action="store_true", help="only leads who agreed to marketing email")
    el.add_argument("-o", "--output", help="file path, or - for stdout (default leads-<date>.csv)")
    el.set_defaults(fn=cmd_export_leads)

    ex = sub.add_parser("export-list", help="CSV of one mailing list's members (session)")
    ex.add_argument("list_id")
    ex.add_argument("-o", "--output", help="file path, or - for stdout")
    ex.set_defaults(fn=cmd_export_list)

    rv = sub.add_parser("record-voice", help="re-record one Jarvis line through Gemini Live on the server (session)")
    rv.add_argument("line_id")
    rv.set_defaults(fn=cmd_record_voice)

    up = sub.add_parser("upload", help="upload a file to Convex storage and register it in the media library")
    up.add_argument("file")
    up.add_argument("--name", help="display name (default: the file name)")
    up.add_argument("--alt", help="alt text (images)")
    up.add_argument("--mime", help="bare MIME type (default from the extension)")
    up.add_argument("--kind", choices=["image", "video", "audio", "pdf", "other"], help="override the kind derived from the MIME type")
    up.add_argument("--no-register", action="store_true", help="storage only (a guide page image or PDF), no media row")
    up.set_defaults(fn=cmd_upload)

    cg = sub.add_parser("content-get", help="a content file: the admin override, else the repo file")
    cg.add_argument("path", help="about.md, site.md, work/<slug>.md, jarvis-lines.md ...")
    cg.add_argument("--source", choices=["auto", "override", "repo"], default="auto")
    cg.add_argument("-o", "--output", help="write the text to this file")
    cg.add_argument("--raw", action="store_true", help="print the text itself instead of JSON")
    cg.set_defaults(fn=cmd_content_get)

    cc = sub.add_parser("content-check", help="run the site's own parser on a local file (needs the site repo)")
    cc.add_argument("path")
    cc.add_argument("file")
    cc.set_defaults(fn=cmd_content_check)

    cs = sub.add_parser("content-save", help="save a local file as the content override (checked with the site's parser when the repo is available)")
    cs.add_argument("path")
    cs.add_argument("file")
    cs.add_argument("--no-check", action="store_true", help="skip the site parser (when no repo is available)")
    cs.set_defaults(fn=cmd_content_save)

    sub.add_parser("doctor", help="check the configuration, the secret, the site and the session").set_defaults(fn=cmd_doctor)
    return p


def main(argv: Optional[list] = None) -> int:
    ns = build_parser().parse_args(argv)
    cfg = Config(ns)
    try:
        result = ns.fn(cfg, ns)
        if result is not None:
            emit(result, compact=ns.compact)
        return 0
    except CliError as e:
        payload = {"ok": False, "error": cfg.redact(str(e)), **{k: (cfg.redact(v) if isinstance(v, str) else v) for k, v in e.extra.items() if v is not None}}
        sys.stderr.write(json.dumps(tidy(payload), ensure_ascii=False, indent=2) + "\n")
        return e.code
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        sys.stderr.write(json.dumps({"ok": False, "error": cfg.redact(f"network: {e}")}, ensure_ascii=False) + "\n")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
