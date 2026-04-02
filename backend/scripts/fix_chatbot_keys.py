#!/usr/bin/env python3
"""
Fix existing users: identify which extraFields came from chatbot (not scrape)
and set chatbotFieldKeys accordingly.

Scrape-discovered fields have known keys from OpenAI post analysis.
Everything else is from the chatbot.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_collection
from datetime import datetime

# These are the keys that come from the LinkedIn post scrape analysis
SCRAPE_INSIGHT_KEYS = {
    "achievementSignals", "communityInvolvement", "content_style",
    "expertise_level", "industryFocus", "thoughtLeadershipTopics",
    "projectsMentioned", "growth_mindset", "job_search_strategy",
    "mentoring_experience", "open_source_contributor",
    "project_management_experience",
}

users = get_collection("users")
count = 0

for user in users.find({"extraFields": {"$exists": True}}):
    extra = user.get("extraFields", {})
    if not extra:
        continue

    # Everything NOT in SCRAPE_INSIGHT_KEYS is from the chatbot
    chatbot_keys = [k for k in extra.keys() if k not in SCRAPE_INSIGHT_KEYS]

    if chatbot_keys:
        users.update_one(
            {"_id": user["_id"]},
            {"$set": {"chatbotFieldKeys": chatbot_keys, "updated_at": datetime.utcnow()}}
        )
        print(f"  {user.get('email', user['_id'])}: {len(chatbot_keys)} chatbot keys tagged")
        count += 1

print(f"\nUpdated {count} users with chatbotFieldKeys")
