import base64
import binascii
import hmac
import struct
import time
from hashlib import sha1

from django.conf import settings


def admin_second_factor_enabled():
    return bool(settings.ADMIN_SECURITY_CODE or settings.ADMIN_TOTP_SECRET)


def verify_totp_code(secret, code, window=1):
    code = (code or "").strip()
    if not secret or not code.isdigit() or len(code) != 6:
        return False

    try:
        key = base64.b32decode(secret.replace(" ", "").upper(), casefold=True)
    except (binascii.Error, ValueError):
        return False

    current_counter = int(time.time() // 30)
    for offset in range(-window, window + 1):
        counter = current_counter + offset
        message = struct.pack(">Q", counter)
        digest = hmac.new(key, message, sha1).digest()
        index = digest[-1] & 0x0F
        token = (struct.unpack(">I", digest[index:index + 4])[0] & 0x7FFFFFFF) % 1000000
        if hmac.compare_digest(f"{token:06d}", code):
            return True

    return False


def verify_admin_code(code):
    configured_code = settings.ADMIN_SECURITY_CODE
    if configured_code and hmac.compare_digest(configured_code, (code or "").strip()):
        return True

    return verify_totp_code(settings.ADMIN_TOTP_SECRET, code)
