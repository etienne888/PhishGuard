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


# --- Origin tracing: the receiving provider must not hide the sender -------------------------
def _eml(*received):
    lines = ''.join(f'Received: {r}\r\n' for r in received)
    return (lines + 'From: a@b.test\r\nSubject: x\r\nDate: Mon, 1 Sep 2026 10:00:00 +0000\r\n\r\nbody').encode()


def test_origin_external_server_delivered_to_gmail_is_located():
    from app.services.email_origin import trace
    raw = _eml('by 2002:a05:6a10::1 with SMTP id x; Mon, 1 Sep 2026 10:00:02 +0000',
               'from out197-184.us.a.dm.aliyun.com (out197-184.us.a.dm.aliyun.com. [47.90.197.184]) '
               'by mx.google.com with ESMTPS id y; Mon, 1 Sep 2026 10:00:01 +0000')
    r = trace(raw, network=False)
    assert r['precision'] != 'hidden'
    assert r['sender_ip'] == '47.90.197.184'
    assert r['mailbox_provider'] == 'Gmail'


def test_origin_sent_from_gmail_account_is_hidden():
    from app.services.email_origin import trace
    raw = _eml('by 2002:a05:6a10::1 with SMTP id x; Mon, 1 Sep 2026 10:00:02 +0000',
               'from mail-sor-f69.google.com (mail-sor-f69.google.com. [209.85.220.69]) '
               'by mx.google.com with SMTPS id y; Mon, 1 Sep 2026 10:00:01 +0000')
    r = trace(raw, network=False)
    assert r['precision'] == 'hidden' and r['sender_ip'] is None
    assert r['provider_server']['ip'] == '209.85.220.69'
