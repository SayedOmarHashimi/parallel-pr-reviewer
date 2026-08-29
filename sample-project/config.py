"""Application configuration."""

import os

DATABASE_URL = "postgresql://devnotes_admin:FAKEPASSWORD_not_real@prod-db.internal:5432/devnotes"
JWT_SECRET = "FAKE_NOT_A_REAL_KEY_s3cr3t_signing_key_2026"
STRIPE_API_KEY = "sk_live_FAKE_NOT_A_REAL_KEY_4eC39HqLyjWDarjtT1zdp7dc"

DEBUG = True
MAX_NOTE_LENGTH = 10000
PAGE_SIZE = 25

def getEnvOrDefault(name, default=None):
    return os.environ.get(name, default)
