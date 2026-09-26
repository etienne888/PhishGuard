"""
Encryption at rest for mailbox OAuth tokens.

Key: MAILBOX_ENCRYPTION_KEY in .env (any long random string; falls back to a key
derived from SECRET_KEY). Rotating the key makes stored tokens unreadable, so
users simply reconnect their mailbox.

Uses Fernet when the `cryptography` package is installed ("f1:" prefix).
Otherwise a standard-library construction ("s1:" prefix): HMAC-SHA256 in counter
mode as the keystream + encrypt-then-MAC with a separate HMAC-SHA256 key and a
random 16-byte nonce. Both are authenticated: a tampered value fails to decrypt.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets

try:  # pragma: no cover - depends on the environment
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    Fernet = None
    InvalidToken = Exception


class DecryptionError(ValueError):
    pass


def _master_key() -> bytes:
    raw = os.getenv('MAILBOX_ENCRYPTION_KEY') or os.getenv('SECRET_KEY') or 'dev-key-change-in-production'
    return hashlib.sha256(('phishguard-mailbox:' + raw).encode()).digest()


def _subkey(label: bytes) -> bytes:
    return hmac.new(_master_key(), label, hashlib.sha256).digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    out = bytearray()
    counter = 0
    while len(out) < length:
        out += hmac.new(key, nonce + counter.to_bytes(8, 'big'), hashlib.sha256).digest()
        counter += 1
    return bytes(out[:length])


def encrypt(plaintext: str | None) -> str | None:
    if plaintext is None:
        return None
    data = plaintext.encode()
    if Fernet is not None:
        fernet = Fernet(base64.urlsafe_b64encode(_subkey(b'fernet')))
        return 'f1:' + fernet.encrypt(data).decode()
    nonce = secrets.token_bytes(16)
    cipher = bytes(a ^ b for a, b in zip(data, _keystream(_subkey(b'enc'), nonce, len(data))))
    tag = hmac.new(_subkey(b'mac'), nonce + cipher, hashlib.sha256).digest()
    return 's1:' + base64.urlsafe_b64encode(nonce + tag + cipher).decode()


def decrypt(token: str | None) -> str | None:
    if not token:
        return None
    scheme, _, body = token.partition(':')
    if scheme == 'f1':
        if Fernet is None:
            raise DecryptionError('cryptography package required for this token')
        try:
            return Fernet(base64.urlsafe_b64encode(_subkey(b'fernet'))).decrypt(body.encode()).decode()
        except InvalidToken as exc:
            raise DecryptionError('invalid token') from exc
    if scheme == 's1':
        try:
            raw = base64.urlsafe_b64decode(body.encode())
        except (ValueError, TypeError) as exc:
            raise DecryptionError('invalid token') from exc
        nonce, tag, cipher = raw[:16], raw[16:48], raw[48:]
        expected = hmac.new(_subkey(b'mac'), nonce + cipher, hashlib.sha256).digest()
        if len(raw) < 48 or not hmac.compare_digest(tag, expected):
            raise DecryptionError('invalid token')
        return bytes(a ^ b for a, b in zip(cipher, _keystream(_subkey(b'enc'), nonce, len(cipher)))).decode()
    raise DecryptionError('unknown scheme')
