import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import requests
except ImportError:
    requests = None


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_FILE = DATA_DIR / "raven_mvp.json"
HOST = os.environ.get("RAVEN_HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("RAVEN_PORT", "8765")))

FRAUD_BUCKETS = [
    "Authority scam",
    "Emergency scam",
    "Relationship scam",
    "Opportunity scam",
    "Business process scam",
    "Access scam",
    "Recovery scam",
]

RED_FLAGS = {
    "urgency": [
        "today",
        "now",
        "immediately",
        "urgent",
        "deadline",
        "expires",
        "final notice",
        "by 11",
        "within 24",
    ],
    "threat": [
        "jail",
        "prison",
        "arrest",
        "collections",
        "lawsuit",
        "court",
        "shut off",
        "suspend",
        "locked",
        "penalty",
    ],
    "secrecy": [
        "do not tell",
        "don't tell",
        "keep this confidential",
        "secret",
        "between us",
    ],
    "payment pressure": [
        "wire",
        "zelle",
        "cash app",
        "venmo",
        "gift card",
        "crypto",
        "bitcoin",
        "payment",
        "pay",
        "invoice",
        "bank account",
    ],
    "account access": [
        "password",
        "login",
        "security code",
        "verification code",
        "mfa",
        "2fa",
        "remote access",
        "anydesk",
        "teamviewer",
        "install",
    ],
    "unverified sender": [
        "gmail.com",
        "outlook.com",
        "yahoo.com",
        "proton.me",
        "icloud.com",
    ],
    "link or attachment": [
        "http://",
        "https://",
        ".zip",
        ".exe",
        ".scr",
        ".html",
        "attachment",
        "attached",
        "click",
    ],
}

AUTHORITY_TERMS = [
    "bank",
    "chase",
    "irs",
    "police",
    "sheriff",
    "court",
    "microsoft",
    "apple",
    "amazon",
    "utility",
    "fraud department",
]
EMERGENCY_TERMS = ["hospital", "jail", "bail", "accident", "emergency", "stranded", "help me"]
RELATIONSHIP_TERMS = ["love", "baby", "dear", "romance", "military", "lonely", "relationship"]
OPPORTUNITY_TERMS = ["investment", "crypto", "guaranteed", "lottery", "grant", "job offer", "profit"]
BUSINESS_TERMS = ["invoice", "vendor", "supplier", "payroll", "direct deposit", "bank change", "ceo"]
ACCESS_TERMS = ["password", "login", "security code", "remote access", "mfa", "install"]
RECOVERY_TERMS = ["recover your money", "fund recovery", "chargeback", "refund fee"]


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if DATA_FILE.exists():
        return
    seed = {
        "clients": [
            {
                "id": "client-demo-family",
                "name": "Linda Carter",
                "plan": "Companion",
                "segment": "Family",
                "raven_address": "linda-carter@verify.ravencontrol.test",
                "preferred_alerts": ["App", "Text", "Email"],
                "trusted_contacts": [
                    {
                        "name": "Maya Carter",
                        "relationship": "Daughter",
                        "phone": "(555) 013-4410",
                        "email": "maya@example.com",
                        "notify_for": ["High", "Critical"],
                    }
                ],
                "pause_rules": [
                    "Gift cards",
                    "Crypto",
                    "Wire transfer",
                    "Bank login",
                    "Remote access",
                    "Family emergency money request",
                ],
                "notes": "Weekly Tuesday check-in. Daughter receives high-risk alerts.",
            },
            {
                "id": "client-demo-business",
                "name": "Maria's Cafe",
                "plan": "Business Shield",
                "segment": "Business",
                "raven_address": "marias-cafe@verify.ravencontrol.test",
                "preferred_alerts": ["App", "Email"],
                "trusted_contacts": [
                    {
                        "name": "Maria Lopez",
                        "relationship": "Owner",
                        "phone": "(555) 019-8821",
                        "email": "maria@example.com",
                        "notify_for": ["Medium", "High", "Critical"],
                    }
                ],
                "pause_rules": [
                    "Vendor bank change",
                    "Payment over $1000",
                    "Payroll change",
                    "Utility shutoff",
                ],
                "notes": "Verify vendor changes by known phone number before payment.",
            },
        ],
        "cases": [],
    }
    DATA_FILE.write_text(json.dumps(seed, indent=2), encoding="utf-8")


def load_state():
    ensure_data()
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_state(state):
    DATA_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def count_matches(text, terms):
    lower = text.lower()
    return sum(1 for term in terms if term in lower)


def extract_amounts(text):
    amounts = re.findall(r"\$\s?\d[\d,]*(?:\.\d{2})?|\b\d{3,}(?:\.\d{2})?\b", text)
    return list(dict.fromkeys(amounts))[:6]


def extract_links(text):
    links = re.findall(r"https?://[^\s)>\"]+", text)
    return list(dict.fromkeys(links))[:8]


def classify_bucket(text):
    scores = {
        "Authority scam": count_matches(text, AUTHORITY_TERMS),
        "Emergency scam": count_matches(text, EMERGENCY_TERMS),
        "Relationship scam": count_matches(text, RELATIONSHIP_TERMS),
        "Opportunity scam": count_matches(text, OPPORTUNITY_TERMS),
        "Business process scam": count_matches(text, BUSINESS_TERMS),
        "Access scam": count_matches(text, ACCESS_TERMS),
        "Recovery scam": count_matches(text, RECOVERY_TERMS),
    }
    best = max(scores, key=scores.get)
    return best if scores[best] else "Needs review"


def rules_review(payload, client=None):
    text = "\n".join(
        [
            payload.get("subject", ""),
            payload.get("sender", ""),
            payload.get("message", ""),
        ]
    ).strip()
    lower = text.lower()
    flags = []
    for flag, terms in RED_FLAGS.items():
        if any(term in lower for term in terms):
            flags.append(flag)

    amounts = extract_amounts(text)
    links = extract_links(text)
    bucket = classify_bucket(text)

    score = 0
    score += len(flags) * 12
    score += 18 if amounts else 0
    score += 12 if links else 0
    score += 18 if bucket in {"Authority scam", "Emergency scam", "Access scam", "Business process scam"} else 0
    score += 12 if client and any(rule.lower() in lower for rule in client.get("pause_rules", [])) else 0
    score = min(score, 100)

    if score >= 75 or ("account access" in flags and "payment pressure" in flags):
        risk = "Critical"
    elif score >= 52:
        risk = "High"
    elif score >= 28:
        risk = "Medium"
    else:
        risk = "Low"

    safe_path = "Verify through a known official channel before acting."
    if "payment pressure" in flags:
        safe_path = "Do not pay yet. Verify the request through a known phone number, app, or prior trusted contact."
    if "account access" in flags:
        safe_path = "Do not share codes, passwords, or remote access. Use the official app/site only."
    if "threat" in flags:
        safe_path = "Do not respond to the threat. Check the official account or call the known official number."

    if risk in {"High", "Critical"}:
        recommendation = "Pause immediately. Do not click, pay, reply, share codes, or open attachments until a Guardian reviews it."
    elif risk == "Medium":
        recommendation = "Pause and verify independently before responding."
    else:
        recommendation = "No urgent scam pattern detected, but verify independently before money or access is involved."

    customer_response = build_customer_response(risk, flags, safe_path)
    return {
        "risk": risk,
        "risk_score": score,
        "fraud_bucket": bucket,
        "red_flags": flags,
        "amounts": amounts,
        "links": links,
        "safe_verification_path": safe_path,
        "guardian_recommendation": recommendation,
        "customer_response": customer_response,
        "review_source": "rules",
    }


def build_customer_response(risk, flags, safe_path):
    if risk in {"High", "Critical"}:
        opener = f"Raven Alert: preliminary risk is {risk}. Stop and do not act on this request yet."
    elif risk == "Medium":
        opener = "Raven received your item. Preliminary risk is Medium. Pause before responding."
    else:
        opener = "Raven received your item. Preliminary risk is Low, but still verify before money, account access, links, or codes are involved."
    flag_text = ", ".join(flags) if flags else "no major red flags detected"
    return f"{opener} We noticed: {flag_text}. {safe_path} Use only a known official app, website, saved contact, or number from your card or bill."


def review_prompt(payload, rules, client=None):
    return {
        "client": client or {},
        "submitted_item": payload,
        "rules_review": rules,
        "allowed_fraud_buckets": FRAUD_BUCKETS,
        "required_output": {
            "risk": "Low | Medium | High | Critical",
            "fraud_bucket": "one allowed bucket",
            "red_flags": ["short labels"],
            "safe_verification_path": "plain language",
            "guardian_recommendation": "plain language",
            "customer_response": "short text/app-safe message",
            "escalation_needed": True,
        },
    }


def axiom_system_prompt():
    return (
        "You are Axiom for Raven Control. Review suspicious customer-submitted items. "
        "Be cautious, calm, practical, and non-shaming. Do not provide legal, financial, "
        "banking, medical, or law-enforcement advice. Return JSON only with the requested keys."
    )


def openai_review(payload, rules, client=None):
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    model = os.environ.get("RAVEN_OPENAI_MODEL", "gpt-5.4-mini")
    prompt = review_prompt(payload, rules, client)
    body = {
        "model": model,
        "input": [
            {
                "role": "developer",
                "content": axiom_system_prompt(),
            },
            {"role": "user", "content": json.dumps(prompt)},
        ],
    }

    request = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RavenControl/1.0 (https://ravencontrol.com)",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {"api_error": str(exc)}

    text = extract_response_text(raw)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"api_raw_text": text}
    parsed["review_source"] = "openai"
    parsed["model"] = model
    return parsed


def claude_review(payload, rules, client=None):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    model = os.environ.get("RAVEN_CLAUDE_MODEL", "claude-haiku-4-5")
    prompt = review_prompt(payload, rules, client)
    body = {
        "model": model,
        "max_tokens": 1200,
        "system": axiom_system_prompt(),
        "messages": [
            {
                "role": "user",
                "content": json.dumps(prompt),
            }
        ],
    }

    request = Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {"api_error": str(exc)}

    text = extract_claude_text(raw)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = {"api_raw_text": text}
    parsed["review_source"] = "claude"
    parsed["model"] = model
    return parsed


def provider_review(provider, payload, rules, client=None):
    if provider == "claude":
        return claude_review(payload, rules, client)
    if provider == "openai":
        return openai_review(payload, rules, client)
    return None


def extract_response_text(response):
    if "output_text" in response:
        return response["output_text"]
    chunks = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and "text" in content:
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def extract_claude_text(response):
    chunks = []
    for block in response.get("content", []):
        if block.get("type") == "text":
            chunks.append(block.get("text", ""))
    return "\n".join(chunks).strip()


def merge_reviews(rules, ai):
    if not ai or ai.get("api_error"):
        merged = dict(rules)
        if ai and ai.get("api_error"):
            merged["api_error"] = ai["api_error"]
        return merged

    merged = dict(rules)
    for key in [
        "risk",
        "fraud_bucket",
        "red_flags",
        "safe_verification_path",
        "guardian_recommendation",
        "customer_response",
        "escalation_needed",
        "model",
    ]:
        if key in ai and ai[key]:
            merged[key] = ai[key]
    merged["rules_risk_score"] = rules["risk_score"]
    merged["review_source"] = f"{ai.get('review_source', 'api')}+rules"
    return merged


def resend_email(to, subject, text_body, html_body=None, reply_to=None):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        return {"skipped": True, "reason": "RESEND_API_KEY not set"}

    from_email = os.environ.get("RAVEN_FROM_EMAIL", "Raven Control <onboarding@resend.dev>")
    payload = {
        "from": from_email,
        "to": [to] if isinstance(to, str) else to,
        "subject": subject,
        "text": text_body,
    }
    if html_body:
        payload["html"] = html_body
    if reply_to:
        payload["reply_to"] = reply_to

    if requests:
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "User-Agent": "RavenControl/1.0 (https://ravencontrol.com)",
                },
                json=payload,
                timeout=20,
            )
            response_body = response.text
            try:
                response_body = response.json()
            except json.JSONDecodeError:
                pass
            if response.ok:
                return response_body
            return {"error": f"HTTP Error {response.status_code}", "status": response.status_code, "details": response_body}
        except requests.RequestException as exc:
            return {"error": str(exc)}

    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RavenControl/1.0 (https://ravencontrol.com)",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        try:
            error_body = json.loads(error_body)
        except json.JSONDecodeError:
            pass
        return {"error": str(exc), "status": exc.code, "details": error_body}
    except (URLError, TimeoutError, OSError) as exc:
        return {"error": str(exc)}


def send_intake_emails(case, payload):
    notify_to = os.environ.get("RAVEN_NOTIFY_EMAIL", "akeemandrew@ravencontrol.com")
    customer_email = payload.get("email", "")
    review = case.get("review", {})
    console_url = os.environ.get("RAVEN_CONSOLE_URL", "https://ravencontrol-site.onrender.com")
    reply_to = os.environ.get("RAVEN_REPLY_TO", "verify@ravencontrol.com")

    internal_subject = f"Raven intake: {review.get('risk', 'Needs review')} - {case.get('client_name', '')}"
    flags = ", ".join(review.get("red_flags", [])) or "None detected"
    amounts = ", ".join(review.get("amounts", [])) or "None detected"
    links = ", ".join(review.get("links", [])) or "None detected"
    internal_text = f"""New Raven Control intake received.

Case ID: {case.get('id')}
Risk: {review.get('risk')}
Bucket: {review.get('fraud_bucket')}
Status: {case.get('status')}
Red flags: {flags}
Amounts: {amounts}
Links: {links}

Name: {case.get('client_name')}
Email: {customer_email}
Phone: {payload.get('phone', '')}
Who needs help: {payload.get('who_needs_help', '')}
Item type: {payload.get('item_type', '')}
Claimed sender: {payload.get('claimed_sender', '')}

Message:
{payload.get('suspicious_message', '')}

Recommended response:
{review.get('customer_response', '')}

Guardian next steps:
1. Confirm the risk level and final decision.
2. If money, account access, codes, or remote access are involved, keep the client paused.
3. Tell the client to verify only through an official app, known website, saved contact, or number from a card/bill.
4. Escalate to family contact or fraud specialist if loss, access, or ongoing pressure is present.

Guardian Console:
{console_url}
"""
    internal_result = resend_email(
        notify_to,
        internal_subject,
        internal_text,
        reply_to=customer_email or reply_to,
    )

    customer_result = {"skipped": True, "reason": "customer email missing"}
    if customer_email:
        customer_subject = f"Raven received your scam check: {review.get('risk')} risk"
        customer_text = f"""Raven Control received your scam check.

Preliminary risk: {review.get('risk')}
Fraud category: {review.get('fraud_bucket')}

For now, pause. Do not click links, send money, reply, share codes, open attachments, install software, allow remote access, or call numbers from the suspicious message.

Raven's initial guidance:
{review.get('customer_response', '')}

Safe verification path:
{review.get('safe_verification_path', '')}

If money has already been sent, account access was shared, a code was given, or someone is pressuring you right now, contact your bank or account provider directly using the official app, website, card number, or saved trusted contact. You can also reply to this email with URGENT.

A Guardian may follow up if this needs a closer look.

Raven Control helps organize, verify, and escalate suspicious requests. Raven Control is not a law firm, bank, financial advisor, medical provider, or law enforcement agency.

The AI remembers. The Guardian cares.
"""
        customer_result = resend_email(
            customer_email,
            customer_subject,
            customer_text,
            reply_to=reply_to,
        )

    return {"internal": internal_result, "customer": customer_result}


class Handler(BaseHTTPRequestHandler):
    server_version = "RavenMVP/0.1"

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def do_GET(self):
        # Check if this is a customer access (not Guardian console)
        host = self.headers.get("Host", "").split(":")[0].lower()
        is_customer_site = host == "ravencontrol.com" or host == "www.ravencontrol.com"
        
        if self.path == "/" or self.path.startswith("/?"):
            if is_customer_site:
                # Serve customer site from root
                self.send_file(ROOT.parent / "index.html", "text/html")
            else:
                # Serve Guardian console from backend/public
                self.send_file(ROOT / "public" / "index.html", "text/html")
        elif self.path == "/styles.css" or self.path.startswith("/style.css"):
            if is_customer_site:
                self.send_file(ROOT.parent / "style.css", "text/css")
            else:
                self.send_file(ROOT / "public" / "styles.css", "text/css")
        elif self.path == "/app.js":
            if is_customer_site:
                self.send_file(ROOT.parent / "ask-raven.js", "application/javascript")
            else:
                self.send_file(ROOT / "public" / "app.js", "application/javascript")
        elif self.path == "/ask-raven.html":
            self.send_file(ROOT.parent / "ask-raven.html", "text/html")
        elif self.path == "/ask-raven.js":
            # Customer scam check JavaScript
            self.send_file(ROOT.parent / "ask-raven.js", "application/javascript")
        elif self.path.startswith("/assets/"):
            # Serve customer assets
            asset_path = ROOT.parent / self.path.lstrip("/")
            if asset_path.exists() and asset_path.is_file():
                # Determine content type based on extension
                ext = asset_path.suffix.lower()
                content_type = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".svg": "image/svg+xml",
                }.get(ext, "application/octet-stream")
                self.send_file(asset_path, content_type)
            else:
                self.send_error(404, "Asset not found")
        elif self.path == "/api/state":
            self.send_json(load_state())
        elif self.path == "/api/health":
            self.send_json({"ok": True, "service": "raven-control-api"})
        else:
            self.send_error(404, "Not found")

    def do_POST(self):
        if self.path == "/api/review":
            self.handle_review()
        elif self.path == "/api/public-intake":
            self.handle_public_intake()
        elif self.path == "/api/clients":
            self.handle_client()
        elif self.path.startswith("/api/cases/") and self.path.endswith("/status"):
            self.handle_status()
        elif self.path.startswith("/api/cases/") and self.path.endswith("/review"):
            self.handle_case_review()
        else:
            self.send_error(404, "Not found")

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def handle_review(self):
        payload = self.read_json()
        state = load_state()
        client = next((c for c in state["clients"] if c["id"] == payload.get("client_id")), None)
        rules = rules_review(payload, client)
        provider = payload.get("api_provider", "rules")
        ai = provider_review(provider, payload, rules, client)
        review = merge_reviews(rules, ai)
        case = {
            "id": f"case-{uuid.uuid4().hex[:10]}",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "status": "Needs Guardian" if review["risk"] in {"High", "Critical"} else "Auto Reviewed",
            "client_id": payload.get("client_id"),
            "client_name": client["name"] if client else "Unknown client",
            "channel": payload.get("channel", "Forwarded email"),
            "sender": payload.get("sender", ""),
            "subject": payload.get("subject", ""),
            "message": payload.get("message", ""),
            "review": review,
        }
        state["cases"].insert(0, case)
        save_state(state)
        self.send_json(case)

    def handle_public_intake(self):
        payload = self.read_json()
        name = (payload.get("name") or "Website visitor").strip()
        item_type = payload.get("item_type", "Website intake")
        claimed_sender = payload.get("claimed_sender", "")
        subject = f"Website intake: {item_type}"
        message_parts = [
            payload.get("suspicious_message", ""),
            "",
            f"Who needs help: {payload.get('who_needs_help', '')}",
            f"Asking for money: {payload.get('asking_money', '')}",
            f"Asking for login/code/access: {payload.get('asking_access', '')}",
            f"Urgency: {payload.get('urgency', '')}",
            f"Already acted: {payload.get('already_acted', '')}",
            f"Submitter email: {payload.get('email', '')}",
            f"Submitter phone: {payload.get('phone', '')}",
        ]
        review_payload = {
            "client_id": None,
            "channel": f"Ask Raven - {item_type}",
            "sender": claimed_sender,
            "subject": subject,
            "message": "\n".join(message_parts).strip(),
        }
        state = load_state()
        rules = rules_review(review_payload)
        ai = provider_review(payload.get("api_provider", "rules"), review_payload, rules)
        review = merge_reviews(rules, ai)
        case = {
            "id": f"case-{uuid.uuid4().hex[:10]}",
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "status": "Needs Guardian" if review["risk"] in {"High", "Critical"} else "Auto Reviewed",
            "client_id": None,
            "client_name": name,
            "contact": {
                "email": payload.get("email", ""),
                "phone": payload.get("phone", ""),
                "who_needs_help": payload.get("who_needs_help", ""),
            },
            "offer": payload.get("offer", "website_intake"),
            "channel": review_payload["channel"],
            "sender": claimed_sender,
            "subject": subject,
            "message": review_payload["message"],
            "review": review,
        }
        state["cases"].insert(0, case)
        case["email_delivery"] = send_intake_emails(case, payload)
        print(f"Email delivery for {case['id']}: {json.dumps(case['email_delivery'])}")
        save_state(state)
        self.send_json(
            {
                "case_id": case["id"],
                "status": case["status"],
                "risk": review["risk"],
                "fraud_bucket": review["fraud_bucket"],
                "customer_response": review["customer_response"],
                "email_delivery": case["email_delivery"],
            },
            status=201,
        )

    def handle_client(self):
        payload = self.read_json()
        state = load_state()
        client = {
            "id": f"client-{uuid.uuid4().hex[:8]}",
            "name": payload.get("name", "New Client").strip() or "New Client",
            "plan": payload.get("plan", "Verify"),
            "segment": payload.get("segment", "Individual"),
            "raven_address": payload.get("raven_address", "").strip(),
            "preferred_alerts": payload.get("preferred_alerts", ["App", "Email"]),
            "trusted_contacts": payload.get("trusted_contacts", []),
            "pause_rules": payload.get("pause_rules", []),
            "notes": payload.get("notes", ""),
        }
        if not client["raven_address"]:
            slug = re.sub(r"[^a-z0-9]+", "-", client["name"].lower()).strip("-") or client["id"]
            client["raven_address"] = f"{slug}@verify.ravencontrol.test"
        state["clients"].append(client)
        save_state(state)
        self.send_json(client)

    def handle_status(self):
        case_id = self.path.split("/")[3]
        payload = self.read_json()
        state = load_state()
        case = next((c for c in state["cases"] if c["id"] == case_id), None)
        if not case:
            self.send_error(404, "Case not found")
            return
        case["status"] = payload.get("status", case["status"])
        case["updated_at"] = now_iso()
        save_state(state)
        self.send_json(case)

    def handle_case_review(self):
        case_id = self.path.split("/")[3]
        payload = self.read_json()
        state = load_state()
        case = next((c for c in state["cases"] if c["id"] == case_id), None)
        if not case:
            self.send_error(404, "Case not found")
            return

        case["status"] = payload.get("status", case.get("status", "Needs Guardian"))
        case["guardian_review"] = {
            "guardian": payload.get("guardian", "Guardian"),
            "final_decision": payload.get("final_decision", ""),
            "guardian_notes": payload.get("guardian_notes", ""),
            "customer_response": payload.get("customer_response", ""),
            "response_sent": bool(payload.get("response_sent", False)),
            "escalation": payload.get("escalation", "None"),
            "updated_at": now_iso(),
        }
        case["updated_at"] = now_iso()
        save_state(state)
        self.send_json(case)

    def send_file(self, path, content_type):
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_json(self, payload, status=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {fmt % args}")


if __name__ == "__main__":
    ensure_data()
    print(f"Raven Control MVP running at http://{HOST}:{PORT}")
    print("Set ANTHROPIC_API_KEY to enable Claude review. Rules review works without an API key.")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
