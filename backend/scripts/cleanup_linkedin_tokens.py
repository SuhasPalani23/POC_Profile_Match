#!/usr/bin/env python3
"""Remove linkedinAccessToken from all users (tokens should not be stored in DB)."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_collection

result = get_collection("users").update_many(
    {"linkedinAccessToken": {"$exists": True}},
    {"$unset": {"linkedinAccessToken": ""}}
)
print(f"Removed linkedinAccessToken from {result.modified_count} users")
