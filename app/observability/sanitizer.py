"""Log sanitization utilities for PII protection.

M2.6: Prevents personally identifiable information from leaking into logs.
"""

import re
from typing import Any


# PII patterns to detect and mask
# Note: Not using \b (word boundary) as it doesn't work with non-ASCII characters like Chinese
EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
# Chinese ID card (18 digits)
ID_CARD_PATTERN = re.compile(r"\d{17}[\dXx]")
# Credit card patterns (simple version)
CREDIT_CARD_PATTERN = re.compile(r"\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}")


def mask_email(text: str) -> str:
    """Mask email addresses in text.

    Example: user@example.com → u***@example.com
    """
    def replacer(match):
        email = match.group(0)
        parts = email.split("@")
        if len(parts) != 2:
            return "***@***.***"
        username = parts[0]
        domain = parts[1]
        masked_username = username[0] + "***" if len(username) > 0 else "***"
        return f"{masked_username}@{domain}"

    return EMAIL_PATTERN.sub(replacer, text)


def mask_phone(text: str) -> str:
    """Mask phone numbers in text.

    Example: 123-456-7890 → ***-***-7890
    """
    return PHONE_PATTERN.sub("***-***-****", text)


def mask_id_card(text: str) -> str:
    """Mask ID card numbers in text.

    Example: 110101199001011234 → ************1234
    """
    def replacer(match):
        id_card = match.group(0)
        return "*" * (len(id_card) - 4) + id_card[-4:]

    return ID_CARD_PATTERN.sub(replacer, text)


def mask_credit_card(text: str) -> str:
    """Mask credit card numbers in text.

    Example: 1234-5678-9012-3456 → ****-****-****-3456
    """
    def replacer(match):
        card = match.group(0)
        # Keep last 4 digits
        return re.sub(r"\d", "*", card[:-4]) + card[-4:]

    return CREDIT_CARD_PATTERN.sub(replacer, text)


def mask_chinese_name(text: str, name: str) -> str:
    """Mask a specific Chinese name in text.

    Example: 张三 → 张*
    """
    if not name or len(name) < 2:
        return text

    # Mask all but first character
    masked = name[0] + "*" * (len(name) - 1)
    return text.replace(name, masked)


def sanitize_text(text: str, known_names: list[str] | None = None) -> str:
    """Apply all sanitization rules to text.

    Args:
        text: Text to sanitize
        known_names: Optional list of known names to mask

    Returns:
        Sanitized text with PII masked
    """
    if not text:
        return text

    sanitized = text

    # Apply pattern-based masking
    sanitized = mask_email(sanitized)
    sanitized = mask_phone(sanitized)
    sanitized = mask_id_card(sanitized)
    sanitized = mask_credit_card(sanitized)

    # Mask known names
    if known_names:
        for name in known_names:
            sanitized = mask_chinese_name(sanitized, name)

    return sanitized


def sanitize_dict(data: dict[str, Any], sensitive_keys: set[str] | None = None) -> dict[str, Any]:
    """Sanitize dictionary by masking sensitive keys.

    Args:
        data: Dictionary to sanitize
        sensitive_keys: Set of keys to mask (default: common PII keys)

    Returns:
        Sanitized dictionary
    """
    if sensitive_keys is None:
        sensitive_keys = {
            "name",
            "email",
            "phone",
            "mobile",
            "address",
            "id_card",
            "passport",
            "credit_card",
            "password",
            "token",
            "api_key",
            "secret",
            # Resume-specific
            "candidate_name",
            "contact_info",
            "personal_info",
            # Interview-specific
            "answer_text",  # Can contain personal stories
            "raw_text",  # Can contain resumes with PII
        }

    sanitized = {}
    for key, value in data.items():
        if key.lower() in sensitive_keys or any(sk in key.lower() for sk in sensitive_keys):
            # Mask the entire value
            if isinstance(value, str):
                sanitized[key] = "***MASKED***"
            elif isinstance(value, (int, float)):
                sanitized[key] = 0
            else:
                sanitized[key] = None
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, sensitive_keys)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item, sensitive_keys) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def safe_log_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Prepare dictionary for safe logging.

    This is a convenience wrapper around sanitize_dict with default settings.
    Use this before logging any structured data.

    Example:
        logger.info("user_action", **safe_log_dict(user_data))
    """
    return sanitize_dict(data)


def truncate_for_logging(text: str, max_length: int = 200) -> str:
    """Truncate text for logging while sanitizing.

    Args:
        text: Text to truncate
        max_length: Maximum length (default: 200)

    Returns:
        Truncated and sanitized text
    """
    sanitized = sanitize_text(text)
    if len(sanitized) <= max_length:
        return sanitized

    return sanitized[:max_length] + "..."


# Export commonly used functions
__all__ = [
    "sanitize_text",
    "sanitize_dict",
    "safe_log_dict",
    "truncate_for_logging",
    "mask_email",
    "mask_phone",
    "mask_id_card",
    "mask_credit_card",
    "mask_chinese_name",
]
