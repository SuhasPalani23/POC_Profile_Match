#!/usr/bin/env python3
"""
Toggle LinkedIn authentication for a user (for testing purposes).

Usage:
    python scripts/toggle_linkedin_auth.py <email> --enable
    python scripts/toggle_linkedin_auth.py <email> --disable
    python scripts/toggle_linkedin_auth.py --disable-all

--disable removes all LinkedIn auth fields from the database entirely.
--enable sets linkedinAuthed=True (for testing without going through OAuth).

Examples:
    python scripts/toggle_linkedin_auth.py test@test.com --disable
    python scripts/toggle_linkedin_auth.py test@test.com --enable
    python scripts/toggle_linkedin_auth.py --disable-all
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_collection
from datetime import datetime

LINKEDIN_FIELDS = [
    "linkedinAuthed",
    "linkedinAccessToken",
    "linkedinAuthedAt",
    "linkedinOAuthEmail",
    "linkedinOAuthName",
]


def enable_user(email):
    users = get_collection("users")
    result = users.update_one(
        {"email": email},
        {"$set": {
            "linkedinAuthed": True,
            "linkedinAuthedAt": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }}
    )
    if result.matched_count == 0:
        print(f"No user found with email: {email}")
        return
    print(f"LinkedIn auth ENABLED for {email}")


def disable_user(email):
    users = get_collection("users")
    result = users.update_one(
        {"email": email},
        {
            "$unset": {field: "" for field in LINKEDIN_FIELDS},
            "$set": {"updated_at": datetime.utcnow()},
        }
    )
    if result.matched_count == 0:
        print(f"No user found with email: {email}")
        return
    print(f"LinkedIn auth REMOVED (fields deleted) for {email}")


def disable_all():
    users = get_collection("users")
    result = users.update_many(
        {},
        {
            "$unset": {field: "" for field in LINKEDIN_FIELDS},
            "$set": {"updated_at": datetime.utcnow()},
        }
    )
    print(f"LinkedIn auth REMOVED (fields deleted) for {result.modified_count} users")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if "--disable-all" in sys.argv:
        disable_all()
    elif len(sys.argv) >= 3:
        email = sys.argv[1]
        if "--enable" in sys.argv:
            enable_user(email)
        elif "--disable" in sys.argv:
            disable_user(email)
        else:
            print("Use --enable or --disable")
            sys.exit(1)
    else:
        print(__doc__)
        sys.exit(1)
