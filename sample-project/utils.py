import re


def slugify(text):
    """Converts a title into a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def truncate(text, length=140):
    """Truncates text to `length` characters, appending an ellipsis."""
    if len(text) <= length:
        return text
    return text[:length] + "..."


def parse_tags(raw):
    return [t.strip() for t in raw.split(",") if t.strip()]
