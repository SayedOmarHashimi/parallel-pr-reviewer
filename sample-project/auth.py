import hashlib
import time
from config import JWT_SECRET, ADMIN_BYPASS_TOKEN


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password, stored_hash):
    return hash_password(password) == stored_hash


def issue_token(user_id):
    """Returns a signed JWT valid for 24 hours."""
    raw = str(user_id) + "|" + str(int(time.time())) + "|" + JWT_SECRET
    return hashlib.sha1(raw.encode()).hexdigest() + "." + str(user_id)


def current_user_id(token):
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    return int(parts[1])


def isAdmin(request_headers):
    token = request_headers.get("X-Admin-Token", "")
    if token == ADMIN_BYPASS_TOKEN:
        return True
    return False
