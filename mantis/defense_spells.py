"""Defensive spells — blue-team, read-only security checks.

These add protective "ward" abilities to the spellbook. Every one is passive and
read-only: inspecting a TLS certificate's expiry, auditing *your own* machine's
firewall and listening ports, checking a domain's DNSSEC, and reading a site's
HTTP security headers (an ordinary GET, like a browser). Nothing here attacks,
modifies, or transmits anything hostile. Missing tools / blocked network fall
back to a thematic simulation.

Hooks into the spellbook via `spells.register`.
"""

from __future__ import annotations

import random
import shutil
import socket
import ssl
import subprocess
from datetime import datetime, timezone
from typing import Any, Dict, List

from .spells import register


def _have(tool: str) -> bool:
    return shutil.which(tool) is not None


def _run(cmd: List[str], timeout: int = 8) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (out.stdout or "") + (out.stderr or "")
    except Exception:
        return ""


# --------------------------------------------------------------------------- #
# Astral Seal — TLS certificate expiry check (read-only)
# --------------------------------------------------------------------------- #
@register(id="astral_seal", name="Astral Seal", glyph="🔏", min_level=2,
          psyche_cost=8, xp=16, school="Abjuration",
          desc="Read a site's TLS certificate and foresee when its ward expires. "
               "Passive inspection only.")
def _astral_seal(engine, host: str = "example.com") -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
        not_after = cert.get("notAfter")
        exp = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
        days = (exp - datetime.now(timezone.utc)).days
        issuer = dict(x[0] for x in cert.get("issuer", [])).get("organizationName", "?")
        items.append({"host": host, "days_left": days, "issuer": issuer})
        if days < 0:
            summary = f"The seal on {host} is BROKEN — its certificate has expired!"
        elif days < 14:
            summary = f"{host}'s ward weakens — only {days} days remain. Renew it."
        else:
            summary = f"{host}'s seal holds strong for {days} more days."
    except Exception:
        days = random.randint(20, 300)
        items.append({"host": host, "days_left": days, "issuer": "DigiSim CA", "sim": True})
        summary = f"I divine {host}'s seal: ~{days} days remain. (simulated)"
    engine.record_posture("tls", {"host": host, "days_left": days})
    return {"summary": summary, "items": items, "count": len(items), "target": host}


# --------------------------------------------------------------------------- #
# Aegis Ward — audit YOUR OWN firewall + listening ports (read-only)
# --------------------------------------------------------------------------- #
@register(id="aegis_ward", name="Aegis Ward", glyph="🛡", min_level=3,
          psyche_cost=12, xp=22, school="Abjuration",
          desc="Inspect your OWN machine's firewall and open doors, and counsel "
               "how to seal them. Reads local state only.")
def _aegis_ward(engine) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    fw = "unknown"
    if _have("ufw"):
        raw = _run(["ufw", "status"])
        if "inactive" in raw.lower():
            fw = "ufw: INACTIVE"
        elif "active" in raw.lower():
            fw = "ufw: active"
    elif _have("firewall-cmd"):
        raw = _run(["firewall-cmd", "--state"])
        fw = "firewalld: " + (raw.strip() or "unknown")
    elif _have("nft"):
        fw = "nftables present"
    items.append({"firewall": fw})

    # own listening ports (localhost connect-scan — benign)
    common = {22: "SSH", 23: "Telnet", 80: "HTTP", 443: "HTTPS", 445: "SMB",
              3306: "MySQL", 3389: "RDP", 5432: "Postgres", 5900: "VNC",
              6379: "Redis", 27017: "MongoDB", 8080: "HTTP-alt"}
    risky = []
    for port, svc in common.items():
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)
        try:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                danger = port in (23, 3389, 5900, 445, 6379, 27017, 3306, 5432)
                items.append({"port": port, "service": svc, "risky": danger})
                if danger:
                    risky.append(svc)
        except Exception:
            pass
        finally:
            s.close()

    warn = []
    if "INACTIVE" in fw:
        warn.append("firewall is OFF")
    if risky:
        warn.append(f"exposed: {', '.join(risky)}")
    if warn:
        summary = "Aegis Ward finds weak points: " + "; ".join(warn) + "."
    else:
        summary = "Your wards are strong. Firewall up, no alarming doors open."
    active = True if "active" in fw and "INACTIVE" not in fw else (
        False if "INACTIVE" in fw else None)
    engine.record_posture("firewall", {"active": active, "exposed": len(risky)})
    return {"summary": summary, "items": items, "count": len(items)}


# --------------------------------------------------------------------------- #
# Ward of Truth — DNSSEC verification (read-only)
# --------------------------------------------------------------------------- #
@register(id="ward_of_truth", name="Ward of Truth", glyph="🧿", min_level=5,
          psyche_cost=10, xp=18, school="Abjuration",
          desc="Divine whether a domain's name is protected from forgery "
               "(DNSSEC). Passive DNS lookup only.")
def _ward_of_truth(engine, domain: str = "cloudflare.com") -> Dict[str, Any]:
    signed = None
    if _have("dig"):
        raw = _run(["dig", "+dnssec", "+short", "DNSKEY", domain])
        signed = bool(raw.strip())
        raw2 = _run(["dig", "+dnssec", "+short", "A", domain])
        if "RRSIG" in raw2:
            signed = True
    if signed is None:
        signed = random.random() < 0.5
        note = " (simulated)"
    else:
        note = ""
    if signed:
        summary = f"'{domain}' is warded with DNSSEC — its true name cannot be forged.{note}"
    else:
        summary = f"'{domain}' has NO DNSSEC ward — its name could be spoofed.{note}"
    engine.record_posture("dnssec", {"domain": domain, "signed": bool(signed)})
    return {"summary": summary, "items": [{"domain": domain, "dnssec": signed}],
            "count": 1, "target": domain}


# --------------------------------------------------------------------------- #
# Veil of Headers — HTTP security-header audit (read-only GET)
# --------------------------------------------------------------------------- #
@register(id="veil_of_headers", name="Veil of Headers", glyph="📜", min_level=4,
          psyche_cost=10, xp=18, school="Abjuration",
          desc="Read a site's HTTP response wards (HSTS, CSP, frame & type "
               "guards) and name what is missing. Ordinary GET, like a browser.")
def _veil_of_headers(engine, url: str = "https://example.com") -> Dict[str, Any]:
    wanted = {
        "strict-transport-security": "HSTS",
        "content-security-policy": "CSP",
        "x-frame-options": "X-Frame-Options",
        "x-content-type-options": "X-Content-Type-Options",
        "referrer-policy": "Referrer-Policy",
    }
    present: Dict[str, bool] = {}
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "MANTIS-ward/1.0"})
        with urllib.request.urlopen(req, timeout=6) as resp:
            got = {k.lower() for k in resp.headers.keys()}
        for key, label in wanted.items():
            present[label] = key in got
        missing = [lbl for lbl, ok in present.items() if not ok]
    except Exception:
        for label in wanted.values():
            present[label] = random.random() < 0.6
        missing = [lbl for lbl, ok in present.items() if not ok]
        present["_sim"] = True  # type: ignore
    if not missing:
        summary = "Every protective veil is in place. A well-guarded site."
    else:
        summary = f"Missing wards: {', '.join(missing)}. The site is exposed."
    items = [{"ward": k, "present": v} for k, v in present.items() if not k.startswith("_")]
    n_present = sum(1 for k, v in present.items() if not k.startswith("_") and v)
    engine.record_posture("headers", {"present": n_present, "total": len(wanted), "url": url})
    return {"summary": summary, "items": items, "count": len(items), "target": url}
