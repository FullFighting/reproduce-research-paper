#!/usr/bin/env python3
"""Shared deterministic helpers for reproduction evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


GENERATOR_NAME = "reproduce-research-paper"
GENERATOR_VERSION = "1.0.0"
SECRET_REF_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")
SECRET_NAME_PATTERN = re.compile(
    r"(?:api[_-]?key|access[_-]?token|auth(?:orization)?|bearer|client[_-]?secret|"
    r"password|passwd|secret|token|webhook|credential|private[_-]?key)",
    re.I,
)
HIGH_CONFIDENCE_SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,})\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def object_sha256(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def safe_relative_path(value: str, *, label: str) -> Path:
    path = Path(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"{label} must be a non-empty relative path without '..'")
    return path


def redact_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return value
    if not parsed.scheme or not parsed.netloc:
        return value
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    netloc = f"{hostname}{port}"
    if parsed.username or parsed.password:
        netloc = f"[REDACTED]@{netloc}"
    query = []
    for key, item in parse_qsl(parsed.query, keep_blank_values=True):
        query.append((key, "[REDACTED]" if SECRET_NAME_PATTERN.search(key) else item))
    return urlunsplit((parsed.scheme, netloc, parsed.path, urlencode(query), parsed.fragment))


def redact_text(text: str, exact_secrets: list[str] | tuple[str, ...] = ()) -> str:
    redacted = text
    for secret in sorted((item for item in exact_secrets if item), key=len, reverse=True):
        redacted = redacted.replace(secret, "[REDACTED]")
    redacted = re.sub(
        r"(?i)\b(api[_-]?key|access[_-]?token|client[_-]?secret|password|passwd|"
        r"secret|token|webhook|credential)\s*([:=])\s*([^\s,;]+)",
        lambda match: f"{match.group(1)}{match.group(2)}[REDACTED]",
        redacted,
    )
    redacted = re.sub(
        r"(?i)\b(Authorization\s*:\s*(?:Bearer|Basic)?)\s+[^\s,;]+",
        lambda match: f"{match.group(1)} [REDACTED]",
        redacted,
    )
    for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return re.sub(
        r"https?://[^\s\"'<>]+",
        lambda match: redact_url(match.group(0)),
        redacted,
    )


def contains_high_confidence_secret(value: str) -> bool:
    if any(pattern.search(value) for pattern in HIGH_CONFIDENCE_SECRET_PATTERNS):
        return True
    if re.search(
        r"(?i)(?:[?&](?:api[_-]?key|access[_-]?token|secret|token|password)=)[^&#\s]{4,}",
        value,
    ):
        return True
    if re.search(r"(?i)\bAuthorization\s*:\s*(?:Bearer|Basic)\s+\S+", value):
        return True
    if re.search(
        r"(?i)(?:^|\s)--?(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
        r"password|passwd|secret|token|webhook|credential)=[^\s]{4,}",
        value,
    ):
        return True
    try:
        parsed = urlsplit(value)
        if parsed.scheme and parsed.netloc and (parsed.username or parsed.password):
            return True
    except ValueError:
        return True
    return False


def base_child_environment() -> dict[str, str]:
    """Return a narrow environment allowlist without credential-shaped names."""
    allowed = {
        "PATH",
        "PATHEXT",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USERPROFILE",
        "HOME",
        "LANG",
        "LC_ALL",
        "PYTHONPATH",
        "CUDA_VISIBLE_DEVICES",
        "NVIDIA_VISIBLE_DEVICES",
    }
    result = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in allowed and not SECRET_NAME_PATTERN.search(key)
    }
    result["PYTHONDONTWRITEBYTECODE"] = "1"
    result["PYTHONUTF8"] = "1"
    return result
