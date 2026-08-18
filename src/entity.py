"""Small, dependency-free company identity helpers."""
from __future__ import annotations

import re
from urllib.parse import urlparse

LEGAL_SUFFIXES = {"inc", "inc.", "llc", "ltd", "limited", "corp", "corporation", "co", "company", "plc", "gmbh"}


def normalize_company_name(name: str) -> str:
    value = re.sub(r"[^a-z0-9 ]+", " ", name.lower())
    words = [w for w in value.split() if w not in LEGAL_SUFFIXES]
    return " ".join(words)


def canonical_domain(url: str) -> str:
    host = urlparse(url).netloc.lower().split(":")[0]
    return host.removeprefix("www.")


def company_key(name: str, url: str = "") -> str:
    domain = canonical_domain(url)
    return domain or normalize_company_name(name)
