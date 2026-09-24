"""
Turn raw input (pasted text or an .eml file) into one ParsedMessage.

For forwarded emails, the original message is usually attached as
message/rfc822; when present we analyse that inner message, because its
headers are the attacker's, not the forwarder's.
"""

import hashlib
import re
from dataclasses import dataclass, field
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import parseaddr
from html import unescape

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"')\]]+", re.IGNORECASE)


class ParseError(ValueError):
    """Raised when an .eml file cannot be read (test case T-05)."""


@dataclass
class ParsedMessage:
    text: str
    subject: str | None = None
    sender: str | None = None
    sender_domain: str | None = None
    reply_to_domain: str | None = None
    auth_results: dict = field(default_factory=dict)  # {"spf": "pass", ...}
    urls: list[str] = field(default_factory=list)
    attachments: list[dict] = field(default_factory=list)  # name + sha256
    source_type: str = "text"  # "text" | "eml"


def extract_urls(text: str) -> list[str]:
    seen = []
    for url in URL_RE.findall(text or ""):
        url = url.rstrip(".,;:!?")
        if url not in seen:
            seen.append(url)
    return seen[:20]


def _domain_of(address: str | None) -> str | None:
    _, email_addr = parseaddr(address or "")
    if "@" not in email_addr:
        return None
    return email_addr.rsplit("@", 1)[1].lower().strip(">")


def _parse_auth_results(msg: EmailMessage) -> dict:
    header = " ".join(str(h) for h in msg.get_all("Authentication-Results", []))
    results = {}
    for mech in ("spf", "dkim", "dmarc"):
        match = re.search(rf"\b{mech}=(\w+)", header, re.IGNORECASE)
        if match:
            results[mech] = match.group(1).lower()
    return results


def _body_text(msg: EmailMessage) -> str:
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    content = part.get_content()
    if part.get_content_subtype() == "html":
        content = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", content, flags=re.S | re.I)
        # Keep link targets visible to URL extraction before stripping tags
        content = re.sub(r'<a\s[^>]*href="([^"]+)"[^>]*>', r" \1 ", content, flags=re.I)
        content = unescape(re.sub(r"<[^>]+>", " ", content))
    return re.sub(r"\s+", " ", content).strip()


def parse_text(text: str) -> ParsedMessage:
    return ParsedMessage(text=text.strip(), urls=extract_urls(text))


def parse_eml(raw: bytes) -> ParsedMessage:
    try:
        msg = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:  # pragma: no cover - parser is very lenient
        raise ParseError(f"Fichier .eml illisible : {exc}") from exc

    if not msg.keys():
        raise ParseError("Fichier .eml invalide : aucun en-tête trouvé.")

    # Forwarded email: analyse the attached original instead
    for part in msg.iter_attachments():
        if part.get_content_type() == "message/rfc822":
            inner = part.get_content()
            if isinstance(inner, EmailMessage) and inner.keys():
                msg = inner
                break

    body = _body_text(msg)
    subject = str(msg.get("Subject", "") or "") or None
    sender = str(msg.get("From", "") or "") or None

    attachments = []
    for part in msg.iter_attachments():
        payload = part.get_payload(decode=True) or b""
        attachments.append({
            "filename": part.get_filename() or "sans-nom",
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size": len(payload),
        })

    full_text = f"{subject}\n{body}" if subject else body
    if not full_text.strip():
        raise ParseError("Le fichier .eml ne contient aucun texte analysable.")

    return ParsedMessage(
        text=full_text,
        subject=subject,
        sender=sender,
        sender_domain=_domain_of(sender),
        reply_to_domain=_domain_of(str(msg.get("Reply-To", "") or "")),
        auth_results=_parse_auth_results(msg),
        urls=extract_urls(body),
        attachments=attachments,
        source_type="eml",
    )
