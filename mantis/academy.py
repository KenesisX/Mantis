"""The Academy — an in-app cybersecurity curriculum.

MANTIS teaches you the real concept behind each themed spell/stage as you play,
from absolute beginner ("Script Kiddie") up a cert-aligned ladder toward
professional mastery. Every lesson has a short, accurate explanation, a practical
tip, and a multiple-choice quiz that awards KNOWLEDGE when you answer correctly.

The tier names reference well-known industry certifications only as learning
milestones / study tracks — this is educational framing, not an endorsement or
a substitute for the real exams.

Strong theme throughout: this is WHITE-HAT education. Authorization, legality and
ethics are taught as the foundation, not an afterthought.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

LESSONS: List[Dict[str, Any]] = []


def _L(lid, tier, topic, title, body, tip, q, choices, answer, explain,
       xp=15, spell=None):
    LESSONS.append({
        "id": lid, "tier": tier, "topic": topic, "title": title,
        "body": body, "tip": tip,
        "quiz": {"q": q, "choices": choices, "answer": answer, "explain": explain},
        "xp": xp, "spell": spell,
    })


# ---- Tier 0: ethics first -------------------------------------------------- #
_L("ethics", 0, "Ethics", "Authorization First",
   "Security work is legal only with explicit permission on systems you own or "
   "are authorized to test. The exact same action can be research or a crime — "
   "the difference is consent and scope.",
   "Always get written authorization (a 'rules of engagement' document) before "
   "touching anything you don't own.",
   "What makes a security test legal?",
   ["Using a VPN", "Explicit written authorization and defined scope",
    "Doing it at night", "Only scanning, not exploiting"],
   1, "Permission and scope are what separate authorized testing from a crime — "
      "tools and intent are secondary.", xp=20)

# ---- Tier 1: the basics (Script Kiddie -> Newcomer) ------------------------ #
_L("recon", 1, "Recon", "Passive vs Active Recon",
   "Reconnaissance is gathering information about a target. PASSIVE recon only "
   "observes (listening to broadcasts, public records) and is low-risk; ACTIVE "
   "recon sends packets to the target and can be detected.",
   "Start passive. You learn a lot just by listening before you ever touch a target.",
   "Which is PASSIVE reconnaissance?",
   ["Port scanning a server", "Listening to Wi-Fi beacon frames already in the air",
    "Brute-forcing a login", "Sending ARP requests"],
   1, "Listening to beacons the AP already broadcasts observes without interacting "
      "— that's passive.", spell="mind_reading")
_L("wifi", 1, "Wireless", "How Wi-Fi Identifies Networks",
   "Access points broadcast an SSID (network name) on a channel. Security types "
   "matter: OPEN has no encryption, WPA2 is common, WPA3 is current best practice.",
   "An 'OPEN' network offers no encryption — treat anything you send on it as public.",
   "Which Wi-Fi security is strongest today?",
   ["WEP", "OPEN", "WPA2", "WPA3"], 3,
   "WPA3 is the current standard; WEP is broken and OPEN is unencrypted.",
   spell="mind_reading")
_L("ipnet", 1, "Networking", "IP Addresses & Subnets",
   "Devices on a local network share a subnet (e.g. 192.168.1.0/24). Host "
   "discovery finds which addresses are alive — the basis of a network map.",
   "A /24 subnet holds 254 usable host addresses (.1 to .254).",
   "What does a /24 subnet mask give you?",
   ["254 usable hosts", "2 hosts", "65k hosts", "Unlimited"],
   0, "/24 = 256 addresses, minus network and broadcast = 254 usable hosts.",
   spell="clairvoyance")
_L("ports", 1, "Networking", "Ports & Services",
   "A server listens on numbered ports (22=SSH, 80=HTTP, 443=HTTPS). Every open "
   "port is a door — fewer open doors means a smaller attack surface.",
   "Audit your OWN machine and close ports you don't need. Least exposure wins.",
   "Which port is HTTPS?",
   ["21", "22", "443", "3389"], 2,
   "443 is HTTPS; 22 is SSH, 21 is FTP, 3389 is RDP.", spell="the_veil")

# ---- Tier 2: fundamentals (ITF+/Security+ intro) --------------------------- #
_L("cia", 2, "Concepts", "The CIA Triad",
   "Security protects three things: Confidentiality (secrecy), Integrity "
   "(not tampered), and Availability (it works when needed). Every control maps "
   "to one or more of these.",
   "When you evaluate a risk, ask which of C, I, or A it threatens.",
   "Encrypting data at rest primarily protects…",
   ["Availability", "Confidentiality", "Integrity", "Performance"],
   1, "Encryption keeps data secret — that's Confidentiality.", xp=18)
_L("tls", 2, "Crypto/PKI", "TLS & Certificates",
   "HTTPS uses TLS certificates issued by a Certificate Authority to prove a "
   "site's identity and encrypt traffic. Certs expire and must be renewed, or "
   "browsers warn users.",
   "Monitor cert expiry — an expired cert breaks trust and often takes sites down.",
   "What does a valid TLS certificate prove?",
   ["The site is bug-free", "The server's identity + enables encryption",
    "The site is fast", "The owner is a company"],
   1, "A cert binds a public key to an identity and enables encrypted sessions.",
   spell="astral_seal")
_L("dns", 2, "Networking", "DNS Resolution",
   "DNS translates names (example.com) into IP addresses. It's the phone book of "
   "the internet — and because it's often unauthenticated, it can be spoofed.",
   "DNS problems look like 'the internet is down' — check resolution early.",
   "DNS translates…",
   ["Ports to services", "Names to IP addresses", "IPs to MACs", "Files to blocks"],
   1, "DNS maps human names to IP addresses.", spell="hydroquartz")
_L("dnssec", 2, "Networking", "DNSSEC",
   "DNSSEC adds cryptographic signatures to DNS records so a resolver can verify "
   "the answer wasn't forged, defending against DNS spoofing/cache poisoning.",
   "DNSSEC protects integrity of DNS answers — it does NOT encrypt them.",
   "DNSSEC primarily provides…",
   ["Encryption of DNS", "Authenticity/integrity of DNS answers",
    "Faster lookups", "Ad blocking"],
   1, "DNSSEC signs records to prove they're authentic; it doesn't encrypt.",
   spell="ward_of_truth")
_L("headers", 2, "Web", "HTTP Security Headers",
   "Response headers harden web apps: HSTS forces HTTPS, CSP limits what scripts "
   "run (anti-XSS), X-Frame-Options stops clickjacking, X-Content-Type-Options "
   "stops MIME sniffing.",
   "A missing CSP is a common, high-impact gap — it's your main anti-XSS control.",
   "Which header most helps prevent cross-site scripting (XSS)?",
   ["Server", "Content-Security-Policy", "Date", "Cache-Control"],
   1, "CSP restricts script sources, the primary defense-in-depth against XSS.",
   spell="veil_of_headers")
_L("firewall", 2, "Defense", "Host Firewalls & Least Exposure",
   "A firewall allows/denies traffic by rules. The principle of least exposure "
   "says: only open what you must, deny by default.",
   "Default-deny inbound, allow only required services — then review regularly.",
   "The safest default firewall posture is…",
   ["Allow all, block some", "Deny all inbound, allow only what's needed",
    "No firewall, monitor only", "Open all high ports"],
   1, "Default-deny with explicit allows minimizes attack surface.",
   spell="aegis_ward")

# ---- Tier 3: Security+ track ---------------------------------------------- #
_L("tvr", 3, "Risk", "Threat, Vulnerability, Risk",
   "A THREAT is a potential cause of harm, a VULNERABILITY is a weakness, and "
   "RISK is the chance a threat exploits a vuln times the impact. You manage "
   "risk, you don't eliminate it.",
   "Risk = likelihood × impact. Spend effort where that product is highest.",
   "A patch reduces…",
   ["The threat", "The vulnerability", "The asset value", "The attacker"],
   1, "Patching removes the weakness (vulnerability), lowering risk.", xp=18)
_L("authn", 3, "IAM", "Authentication & MFA",
   "Authentication proves who you are using factors: something you know "
   "(password), have (token), or are (biometric). Multi-factor combines two+ and "
   "stops most account takeovers.",
   "Enable MFA everywhere — it blocks the vast majority of credential attacks.",
   "Which is 'something you have'?",
   ["A password", "A fingerprint", "A hardware security key", "A security question"],
   2, "A hardware key is a possession factor; passwords/questions are knowledge.",
   xp=18)
_L("crypto", 3, "Crypto", "Symmetric vs Asymmetric",
   "Symmetric crypto uses one shared key (fast, e.g. AES). Asymmetric uses a "
   "public/private key pair (e.g. RSA/ECC) to exchange keys and sign. TLS uses "
   "both.",
   "Never roll your own crypto — use vetted libraries and current algorithms.",
   "Which is an asymmetric algorithm?",
   ["AES", "RSA", "SHA-256", "ChaCha20"], 1,
   "RSA uses a key pair; AES/ChaCha20 are symmetric, SHA-256 is a hash.", xp=18)
_L("hashing", 3, "Crypto", "Hashing & Salting",
   "A hash is a one-way fingerprint of data. Passwords should be stored hashed "
   "with a unique SALT and a slow algorithm (bcrypt/argon2) to resist cracking.",
   "Hashing isn't encryption — you can't 'decrypt' a hash, only guess-and-check.",
   "Why add a unique salt to each password hash?",
   ["To encrypt it", "To defeat precomputed (rainbow table) attacks",
    "To speed up login", "To shorten the hash"],
   1, "Salts make identical passwords hash differently, defeating rainbow tables.",
   spell="soul_scream", xp=18)
_L("soceng", 3, "Human", "Social Engineering",
   "The weakest link is usually people. Phishing, pretexting and baiting trick "
   "users into giving access. Technical controls can't fully fix a human who "
   "clicks.",
   "Verify unexpected requests out-of-band. Urgency + authority = classic phishing.",
   "Phishing primarily exploits…",
   ["A software bug", "Human trust and urgency", "Weak encryption", "Open ports"],
   1, "Phishing manipulates people, not code.", xp=18)

# ---- Tier 4: Blue team (CySA+ track) -------------------------------------- #
_L("logging", 4, "BlueTeam", "Logging & SIEM",
   "You can't defend what you can't see. Centralized logs feed a SIEM that "
   "correlates events to detect attacks. Good logging is the backbone of "
   "detection and response.",
   "Log centrally and tamper-evidently — attackers try to wipe local logs.",
   "A SIEM mainly helps you…",
   ["Encrypt traffic", "Detect & correlate security events",
    "Block all malware", "Patch systems"],
   1, "A SIEM aggregates and correlates logs to surface incidents.", xp=20)
_L("ir", 4, "BlueTeam", "Incident Response",
   "IR follows phases: Prepare, Identify, Contain, Eradicate, Recover, and "
   "Lessons-learned. Containment before eradication stops the bleeding first.",
   "Have a plan BEFORE an incident. Practiced playbooks beat improvising at 3am.",
   "What comes right after Identification in IR?",
   ["Recovery", "Containment", "Eradication", "Lessons learned"],
   1, "Contain first to limit damage, then eradicate and recover.", xp=20)
_L("segmentation", 4, "BlueTeam", "Network Segmentation",
   "Splitting a network into zones (and limiting traffic between them) stops an "
   "attacker who breaches one area from moving freely across everything.",
   "Segment sensitive systems away from general user/IoT networks.",
   "Segmentation most directly limits…",
   ["Phishing", "Lateral movement", "Cert expiry", "Password reuse"],
   1, "Zoned networks restrict lateral movement after a breach.", xp=20)

# ---- Tier 5: Red team ethics & web (PenTest+ track) ----------------------- #
_L("roe", 5, "RedTeam", "Rules of Engagement",
   "A pentest is bounded by a signed scope: which targets, which techniques, "
   "timing, and who to call if something breaks. Going out of scope is both "
   "unprofessional and illegal.",
   "If it's not in scope, don't touch it — document and ask instead.",
   "Testing a target NOT listed in your authorization is…",
   ["Fine if you find a bug", "Out of scope and likely illegal",
    "Encouraged", "Only an issue if detected"],
   1, "Only authorized, in-scope targets may be tested — ever.", xp=22)
_L("methodology", 5, "RedTeam", "Pentest Methodology",
   "A structured test flows: recon → scanning/enumeration → exploitation → "
   "post-exploitation → reporting. The REPORT is the actual deliverable that "
   "helps defenders fix things.",
   "The value of a pentest is the clear, actionable report — not the 'hack'.",
   "What is the real deliverable of a pentest?",
   ["A shell", "A clear remediation report", "A screenshot", "Bragging rights"],
   1, "Findings + remediation guidance are what the client pays for.", xp=20)
_L("owasp", 5, "Web", "OWASP Top 10",
   "The OWASP Top 10 lists the most critical web app risks (e.g. Broken Access "
   "Control, Injection, Cryptographic Failures). It's the baseline checklist for "
   "web security.",
   "Broken Access Control is consistently #1 — always test authorization, not just login.",
   "Which is the OWASP Top 10 category for SQL injection?",
   ["Broken Access Control", "Injection", "Security Misconfiguration", "SSRF"],
   1, "SQL/command/LDAP injection all fall under 'Injection'.", xp=20)

# ---- Tier 6: Advanced (CISSP track) --------------------------------------- #
_L("grc", 6, "Governance", "Risk Frameworks & GRC",
   "Mature programs use frameworks (NIST CSF, ISO 27001) to govern security as a "
   "business function: identify, protect, detect, respond, recover — with "
   "documented policy and accountability.",
   "Security is a business risk decision, not just a technical one.",
   "NIST CSF's five functions are Identify, Protect, Detect, Respond and…",
   ["Recover", "Encrypt", "Audit", "Deploy"], 0,
   "The five functions are Identify, Protect, Detect, Respond, Recover.", xp=22)
_L("keymgmt", 6, "Crypto", "Key Management",
   "Crypto is only as strong as its key management: generation, storage (HSMs), "
   "rotation, and revocation. A leaked key breaks everything it protected.",
   "Rotate keys, store them in an HSM/secret manager, and never hardcode them.",
   "The most common real-world crypto failure is…",
   ["Weak algorithms", "Poor key management", "Slow hardware", "Short messages"],
   1, "Most breaches of 'encrypted' data come from mishandled keys, not broken math.",
   xp=22)
_L("zerotrust", 6, "Architecture", "Zero Trust",
   "Zero Trust assumes no implicit trust by network location: verify every "
   "request, enforce least privilege, and assume breach. 'Never trust, always "
   "verify.'",
   "Identity becomes the new perimeter — authenticate and authorize every request.",
   "Zero Trust's core principle is…",
   ["Trust the internal network", "Never trust, always verify",
    "Block all traffic", "Trust after first login"],
   1, "Zero Trust verifies continuously and grants least privilege.", xp=22)

# ---- Tier 7: RF / SDR (tie to the RF spells) ------------------------------ #
_L("sdr", 7, "RF", "Software-Defined Radio",
   "An SDR (like the RTL-SDR) turns radio waves into data your computer decodes. "
   "Receiving is passive and legal for most bands; transmitting is heavily "
   "regulated and often requires a license.",
   "Listening (RX) is broadly fine; transmitting (TX) is where law and licensing apply.",
   "Using an RTL-SDR to LISTEN to public broadcasts is…",
   ["Always illegal", "Generally legal (receive-only)",
    "Only legal with a warrant", "Impossible"],
   1, "Receive-only monitoring of public signals is generally legal; transmitting is regulated.",
   spell="subghz_listen", xp=18)
_L("ism", 7, "RF", "ISM Bands",
   "Unlicensed ISM bands (e.g. 315/433/915 MHz) carry sensors, key fobs, weather "
   "stations and telemetry. rtl_433 decodes many of these public, unencrypted "
   "broadcasts.",
   "Much ISM telemetry is unencrypted by design — privacy, not secrecy, is the norm.",
   "ISM bands are used for…",
   ["Licensed TV", "Low-power sensors/telemetry", "Military only", "Cellular voice"],
   1, "ISM = Industrial, Scientific, Medical: unlicensed low-power devices.",
   spell="subghz_listen", xp=18)
_L("adsb", 7, "RF", "ADS-B Aircraft Tracking",
   "Aircraft broadcast position/identity on 1090 MHz (ADS-B). Anyone with a "
   "receiver can decode these public safety broadcasts — the basis of flight "
   "trackers.",
   "ADS-B is intentionally public; receiving it is a great, legal SDR starter project.",
   "ADS-B on 1090 MHz is…",
   ["Encrypted military data", "Public aircraft position broadcasts",
    "A Wi-Fi channel", "A cellular band"],
   1, "ADS-B is an open broadcast of aircraft position/identity.",
   spell="adsb_sky", xp=18)


# --------------------------------------------------------------------------- #
# Tier ladder (completed-count -> rank)
# --------------------------------------------------------------------------- #
TIERS = [
    (0, "Script Kiddie"),
    (1, "Curious Newcomer"),
    (4, "IT Apprentice (ITF+ track)"),
    (8, "Security Student (Security+ track)"),
    (12, "SOC Analyst (CySA+ track)"),
    (16, "Pentest Apprentice (PenTest+ track)"),
    (20, "Security Engineer"),
    (24, "Red/Blue Specialist (OSCP/GCIH track)"),
    (28, "Security Architect (CISSP track)"),
    (31, "Principal Security Expert"),
]

_BY_ID = {les["id"]: les for les in LESSONS}
TOTAL = len(LESSONS)


def tier_for(completed: int):
    title, idx = TIERS[0][1], 0
    for i, (threshold, name) in enumerate(TIERS):
        if completed >= threshold:
            title, idx = name, i
        else:
            break
    return title, idx


def get(lid: str) -> Optional[Dict[str, Any]]:
    return _BY_ID.get(lid)


def next_lesson(done: List[str]) -> Optional[Dict[str, Any]]:
    doneset = set(done or [])
    for les in LESSONS:
        if les["id"] not in doneset:
            return les
    return None


def spell_lesson(spell_id: str) -> Optional[Dict[str, Any]]:
    for les in LESSONS:
        if les.get("spell") == spell_id:
            return les
    return None


def public_lesson(les: Dict[str, Any]) -> Dict[str, Any]:
    """Lesson without the quiz answer (for display before answering)."""
    if not les:
        return {}
    return {
        "id": les["id"], "tier": les["tier"], "topic": les["topic"],
        "title": les["title"], "body": les["body"], "tip": les["tip"],
        "xp": les["xp"], "spell": les.get("spell"),
        "quiz": {"q": les["quiz"]["q"], "choices": list(les["quiz"]["choices"])},
    }


def summary(academy: Dict[str, Any]) -> Dict[str, Any]:
    done = list((academy or {}).get("completed", []))
    title, idx = tier_for(len(done))
    nxt = next_lesson(done)
    correct = (academy or {}).get("quiz_correct", 0)
    total_ans = (academy or {}).get("quiz_total", 0)
    return {
        "tier": title, "tier_idx": idx, "tier_max": len(TIERS),
        "completed": len(done), "total": TOTAL,
        "pct": round(100 * len(done) / TOTAL, 1) if TOTAL else 0,
        "knowledge_xp": (academy or {}).get("knowledge_xp", 0),
        "quiz_accuracy": round(100 * correct / total_ans) if total_ans else 0,
        "next": public_lesson(nxt) if nxt else None,
        "done_ids": done,
    }
