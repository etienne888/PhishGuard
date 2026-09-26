"""Unit tests for the mailbox scanner / forwarding building blocks (no database needed)."""
import email
from email import policy
from email.message import EmailMessage

import pytest

from app.services import crypto_box, inbound_service, scan_service


def test_token_encryption_round_trip():
    secret = 'ya29.a0AfH6SMB-token-é' * 5
    token = crypto_box.encrypt(secret)
    assert token != secret and token.split(':')[0] in ('s1', 'f1')
    assert crypto_box.decrypt(token) == secret


def test_token_encryption_uses_a_fresh_nonce():
    assert crypto_box.encrypt('same') != crypto_box.encrypt('same')


def test_tampered_token_is_rejected():
    token = crypto_box.encrypt('refresh-token')
    scheme, _, body = token.partition(':')
    flipped = body[:-2] + ('AA' if body[-2:] != 'AA' else 'BB')
    with pytest.raises(crypto_box.DecryptionError):
        crypto_box.decrypt(f'{scheme}:{flipped}')


def test_finalize_maps_levels_to_verdicts():
    for level, verdict in (('Critical', 'phishing'), ('High', 'phishing'), ('Medium', 'suspicious'), ('Low', 'legitimate')):
        result = scan_service.finalize({'verdict': level, 'urls': []})
        assert result['verdict'] == verdict and result['level'] == level


def _forward(inner: EmailMessage | None, body: str = '') -> email.message.EmailMessage:
    outer = EmailMessage()
    outer['From'] = 'Jean <jean@example.cm>'
    outer['To'] = 'check@phishguard.cm'
    outer['Subject'] = 'Fwd: suspect'
    outer.set_content(body or 'voir pièce jointe')
    if inner is not None:
        outer.add_attachment(inner.as_bytes(), maintype='message', subtype='rfc822')
    return email.message_from_bytes(outer.as_bytes(), policy=policy.default)


def test_forward_as_attachment_keeps_the_original_email():
    inner = EmailMessage()
    inner['From'] = 'MTN <alerte@mtn-secure.tk>'
    inner['Subject'] = 'Compte suspendu'
    inner.set_content('Confirmez votre PIN sur http://mtn-secure.tk')
    raw, text = inbound_service._inner_message(_forward(inner))
    assert raw is not None and b'mtn-secure.tk' in raw and text == ''


def test_inline_forward_is_analysed_as_text():
    raw, text = inbound_service._inner_message(_forward(None, '---- Message transféré ----\nVotre compte MoMo est bloqué'))
    assert raw is None and 'MoMo' in text


def test_auto_replies_are_ignored(monkeypatch):
    monkeypatch.setenv('INBOUND_IMAP_HOST', 'imap.example.com')
    monkeypatch.setenv('INBOUND_IMAP_USER', 'check@phishguard.cm')
    monkeypatch.setenv('INBOUND_IMAP_PASSWORD', 'x')
    msg = EmailMessage()
    msg['From'] = 'robot@example.cm'
    msg['Auto-Submitted'] = 'auto-replied'
    msg.set_content('Out of office')
    assert inbound_service.process(msg.as_bytes()) == 'ignored'
    own = EmailMessage()
    own['From'] = 'check@phishguard.cm'
    own.set_content('loop')
    assert inbound_service.process(own.as_bytes()) == 'ignored'
