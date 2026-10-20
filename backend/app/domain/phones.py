# File:     backend/app/domain/phones.py
# Author:   mrbacco04@gmail.com
# GitHub:   https://github.com/mrbacco
# Created:  2026-10-20
# Updated:  2026-10-20
# Project:  SYNDICATE
# License:  Apache-2.0 OR AGPL-3.0-or-later OR LicenseRef-Commercial

"""Phone numbers, matching the app's PhoneNumbers.kt."""


def international(raw: str, default_country_code: str = "353") -> str | None:
    """International digits without "+": "087 123 4567" -> "353871234567" (Irish by default).

    Returns None if it does not look like a phone number.
    """
    trimmed = raw.strip()
    if any(not c.isdigit() and c not in "+ -()." for c in trimmed):
        return None
    digits = "".join(c for c in trimmed if c.isdigit())
    if trimmed.startswith("+"):
        result = digits
    elif digits.startswith("00"):
        result = digits[2:]
    elif digits.startswith("0"):
        result = default_country_code + digits[1:]
    else:
        result = digits
    return result if 8 <= len(result) <= 15 else None
