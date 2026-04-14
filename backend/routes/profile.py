from flask import Blueprint, request, jsonify, send_file
from models.user import User
from routes.auth import token_required
from services.ats_service import ATSService
from services.vector_service import VectorService
from services.websocket_service import ws_service
from werkzeug.utils import secure_filename
from pymongo import MongoClient
from bson.objectid import ObjectId
from config import Config
import gridfs
import tempfile
import os
import io
from models.project import Project
from utils.api_response import api_error, api_success, validation_error
import json
import time
import requests
from collections import Counter
from datetime import datetime
from utils.validation import validate_required_fields
from services.background_tasks import enqueue
from openai import OpenAI
from config import Config
from services.openai_service import analyze_posts_deeply, founder_chatbot_respond, normalize_profile_data

openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)

profile_bp = Blueprint("profile", __name__)
ats_service = ATSService()
vector_service = None
vector_service_init_attempted = False


def get_vector_service():
    global vector_service, vector_service_init_attempted
    if vector_service is not None:
        return vector_service
    if vector_service_init_attempted:
        return None
    vector_service_init_attempted = True
    try:
        vector_service = VectorService()
    except Exception as exc:
        print(f"[profile] Vector service unavailable: {exc}")
        vector_service = None
    return vector_service

# GridFS — same MongoDB the rest of the app uses
#
# IMPORTANT: do NOT create network connections at import time.
# Some developers run with remote MongoDB; a slow network/DNS would hang the app import.
_fs = None

def _get_fs():
    global _fs
    if _fs is not None:
        return _fs
    client = MongoClient(
        Config.MONGODB_URI,
        serverSelectionTimeoutMS=2000,
        connectTimeoutMS=2000,
        socketTimeoutMS=2000,
    )
    db = client[Config.DB_NAME]
    _fs = gridfs.GridFS(db)
    return _fs

ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


PROFILE_COMPLETION_FIELDS = [
    "firstName", "lastName", "headline", "about", "currentPosition", "currentCompany",
    "city", "state", "country", "totalYearsExperience", "skills", "tools", "languages",
    "coreDomains", "interests", "industryInclination", "skillStrength", "careerGoals",
    "preferredRole", "preferredIndustry", "strengths", "workStyle", "hobbies",
    "email", "phone", "github",
]

LIKELY_OPTIONAL_FIELDS = set()

PROFILE_ALLOWED_FIELDS = [
    "name", "bio", "skills", "linkedin",
    "professional_title", "experience_years", "location",
    "firstName", "lastName", "linkedinUsername", "headline",
    "currentPosition", "currentCompany", "city", "state", "country",
    "email", "phone", "linkedinUrl", "github", "followers", "connections",
    "about", "totalYearsExperience", "experience", "education",
    "certifications", "languages", "honors", "volunteerWork",
    "publications", "extraFields", "tools", "coreDomains", "interests",
    "industryInclination", "skillStrength", "careerGoals", "preferredRole",
    "preferredIndustry", "strengths", "weaknesses", "workStyle", "openToWork", "hobbies",
    "extraFields", "dynamicFieldLabels", "chatbotFieldKeys", "aboutMe",
]

PROFILE_RESET_DEFAULTS = {
    "name": "",
    "bio": "",
    "skills": [],
    "linkedin": "",
    "professional_title": "",
    "experience_years": 0,
    "location": "",
    "firstName": "",
    "lastName": "",
    "linkedinUsername": "",
    "headline": "",
    "currentPosition": "",
    "currentCompany": "",
    "city": "",
    "state": "",
    "country": "",
    "email": "",
    "phone": "",
    "linkedinUrl": "",
    "github": "",
    "followers": "",
    "connections": "",
    "about": "",
    "totalYearsExperience": "",
    "experience": [],
    "education": [],
    "certifications": [],
    "languages": [],
    "honors": "",
    "volunteerWork": "",
    "publications": "",
    "extraFields": {},
    "tools": [],
    "coreDomains": [],
    "interests": [],
    "industryInclination": "",
    "skillStrength": "",
    "careerGoals": "",
    "preferredRole": "",
    "preferredIndustry": "",
    "strengths": "",
    "weaknesses": "",
    "workStyle": "",
    "openToWork": False,
    "hobbies": "",
}


# ------------------------------------------------------------------
# Background: push updated vector to Pinecone
# ------------------------------------------------------------------

def _safe_emit_vector_update(user_id, status):
    try:
        if ws_service and hasattr(ws_service, 'emit_vector_update'):
            ws_service.emit_vector_update(user_id, status)
    except Exception as e:
        print(f"[_safe_emit_vector_update] Warning: {e}")

def _upsert_user_vector_bg(user_id: str):
    service = get_vector_service()
    if service is None:
        _safe_emit_vector_update(user_id, "failed")
        return
    try:
        user = User.find_by_id(user_id)
        if user:
            # 1. GENERATE CANONICAL NORMALIZED PROFILE FIRST
            try:
                # Group data to match fine-tune expectation
                normalized = normalize_profile_data(
                    linkedin_data={
                        "about": user.get("about"),
                        "aboutMe": user.get("aboutMe"),
                        "experience": user.get("experience"),
                        "headline": user.get("headline"),
                        "skills": user.get("skills"),
                        "tools": user.get("tools"),
                        "coreDomains": user.get("coreDomains"),
                        "interests": user.get("interests"),
                        "professional_title": user.get("professional_title"),
                        "currentPosition": user.get("currentPosition"),
                        "currentCompany": user.get("currentCompany"),
                        "experience_years": user.get("experience_years"),
                        "totalYearsExperience": user.get("totalYearsExperience"),
                    },
                    resume_data={
                        "bio": user.get("bio"),
                        "skills": user.get("skills"),
                        "tools": user.get("tools"),
                        "resume_text": user.get("resume_text"),
                        "experience_years": user.get("experience_years"),
                    },
                    questionnaire_data=user.get("extraFields", {})
                )
                if normalized:
                    user["normalized_profile"] = normalized
                    User.update_profile(user_id, {"normalized_profile": normalized})
            except Exception as e:
                print(f"[_upsert_user_vector_bg] Normalization failed: {e}")

            # 2. UPSERT CLEAN DATA TO PINECONE
            ok = service.upsert_user(user)
            status = "completed" if ok else "failed"
        else:
            status = "failed"
        _safe_emit_vector_update(user_id, status)
    except Exception as e:
        print(f"[profile] Vector upsert error: {e}")
        _safe_emit_vector_update(user_id, "failed")


def _start_vector_upsert(user_id: str):
    enqueue(_upsert_user_vector_bg, user_id)


# ------------------------------------------------------------------
# GET /profile/me
# ------------------------------------------------------------------

@profile_bp.route("/me", methods=["GET"])
@token_required
def get_profile(current_user):
    current_user.pop("password", None)
    return api_success({"user": current_user}, message="Profile fetched")


# ------------------------------------------------------------------
# PUT /profile/update
# ------------------------------------------------------------------

@profile_bp.route("/update", methods=["PUT"])
@token_required
def update_profile(current_user):
    data = request.get_json(silent=True) or {}
    data = _normalize_profile_payload(data)
    
    # Remove nulls/empties from data so we don't overwrite existing good data
    update_fields = {k: data[k] for k in PROFILE_ALLOWED_FIELDS if k in data and data[k] not in [None, "", [], {}]}

    if "experience_years" in update_fields:
        update_fields["experience_years"] = int(update_fields["experience_years"])
    
    from datetime import datetime
    update_fields['scrapedAt'] = datetime.utcnow()

    # Also allow chatbotFieldKeys even if it's an empty list (it's metadata, not content)
    if "chatbotFieldKeys" in data and isinstance(data["chatbotFieldKeys"], list):
        update_fields["chatbotFieldKeys"] = data["chatbotFieldKeys"]

    if not update_fields:
        return validation_error("No valid fields to update")

    print(f"[update_profile] Saving fields: {list(update_fields.keys())}")
    if "chatbotFieldKeys" in update_fields:
        print(f"[update_profile] chatbotFieldKeys: {update_fields['chatbotFieldKeys']}")

    success = User.update_profile(current_user["_id"], update_fields)
    if not success:
        return api_error("PROFILE_UPDATE_FAILED", "Failed to update profile", 500)

    # Calculate Profile Completion Score — must match frontend formula
    # Must-have (40%): firstName, lastName, headline, email, linkedinUrl
    must_have = ['firstName', 'lastName', 'headline', 'email', 'linkedinUrl']
    must_filled = sum(1 for f in must_have if update_fields.get(f) or current_user.get(f))
    # Profile (30%): about, currentPosition, skills, tools, coreDomains, totalYearsExperience, workStyle
    profile_fields = ['about', 'currentPosition', 'skills', 'tools', 'coreDomains', 'totalYearsExperience', 'workStyle']
    profile_filled = sum(1 for f in profile_fields if update_fields.get(f) or current_user.get(f))
    # Chatbot (30%): count of chatbotFieldKeys
    chatbot_keys = update_fields.get('chatbotFieldKeys') or current_user.get('chatbotFieldKeys') or []
    chatbot_count = len(chatbot_keys)

    must_score = (must_filled / len(must_have)) * 40
    profile_score = (profile_filled / len(profile_fields)) * 30
    chatbot_score = min(chatbot_count, 5) / 5 * 30
    score = min(100, round(must_score + profile_score + chatbot_score))
    User.update_profile(current_user["_id"], {"profileCompletionScore": score})

    updated_user = User.find_by_id(current_user["_id"])
    updated_user.pop("password", None)

    _start_vector_upsert(current_user["_id"])
    Project.clear_all_cached_matches()

    ws_service.emit_profile_update(current_user["_id"], {
        "message": "Profile updated successfully",
        "updated_fields": list(update_fields.keys()),
    })

    return api_success({
        "message": "Profile updated successfully",
        "user": updated_user,
        "vector_update_initiated": True,
        "match_cache_invalidated": True,
    }, message="Profile updated successfully")


# ------------------------------------------------------------------
# Apify helpers
# ------------------------------------------------------------------

import re as _re

def _apify_run_and_wait(actor_id, payload, apify_token, max_polls=60, interval=5):
    """Start an Apify run, poll until completion, return dataset items."""
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={apify_token}"
    res = requests.post(run_url, json=payload, timeout=30)
    if res.status_code not in [200, 201]:
        raise RuntimeError(f"Failed to start {actor_id}: {res.text}")
    run_id = res.json()['data']['id']

    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={apify_token}"
    for _ in range(max_polls):
        time.sleep(interval)
        sr = requests.get(status_url, timeout=15).json()
        s = sr['data']['status']
        if s == "SUCCEEDED":
            break
        if s in ["FAILED", "ABORTED", "TIMED-OUT"]:
            raise RuntimeError(f"Apify run {run_id} ended: {s}")

    dataset_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items?token={apify_token}&format=json&clean=true"
    return requests.get(dataset_url, timeout=30).json()


def _parse_apify_direct(raw, full_url):
    """Parse Apify LinkedIn profile data directly, no LLM needed."""
    basic_info = raw.get("basic_info") if isinstance(raw.get("basic_info"), dict) else {}

    def _iter_dicts(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from _iter_dicts(child)
        elif isinstance(value, list):
            for item in value:
                yield from _iter_dicts(item)

    def _find_value(value, keys):
        wanted = {key.lower() for key in keys}
        for item in _iter_dicts(value):
            for key, child in item.items():
                if key.lower() in wanted and child not in [None, "", [], {}]:
                    return child
        return None

    def _find_list(value, keys):
        found = _find_value(value, keys)
        if isinstance(found, list):
            return found
        if isinstance(found, dict):
            for nested in found.values():
                if isinstance(nested, list):
                    return nested
        return []

    def _extract_first_dict_value(item, keys):
        if not isinstance(item, dict):
            return ""
        for key in keys:
            value = item.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _list_of_str(val):
        if not val: return []
        if isinstance(val, list):
            out = []
            for item in val:
                if isinstance(item, str): out.append(item)
                elif isinstance(item, dict):
                    out.append(
                        _extract_first_dict_value(
                            item,
                            [
                                'skillName', 'name', 'title', 'text', 'value', 'label',
                                'language', 'languageName', 'technology', 'tool', 'domain',
                            ],
                        )
                    )
            return [s for s in out if s]
        return []

    def _str(val): return str(val).strip() if val else ''
    def _parse_location_parts(location_text, city_text="", state_text="", country_text=""):
        city_out = _str(city_text)
        state_out = _str(state_text)
        country_out = _str(country_text)
        if isinstance(location_text, dict):
            city_out = city_out or _str(location_text.get("city") or location_text.get("cityName") or location_text.get("locality"))
            state_out = state_out or _str(location_text.get("state") or location_text.get("region") or location_text.get("stateName"))
            country_out = country_out or _str(location_text.get("country") or location_text.get("countryName") or location_text.get("countryCode"))
            location_out = ", ".join(part for part in [city_out, state_out, country_out] if part)
        else:
            location_out = _str(location_text)
        if location_out:
            parts = [part.strip() for part in location_out.split(",") if part.strip()]
            if len(parts) >= 1 and not city_out:
                city_out = parts[0]
            if len(parts) >= 2 and not state_out:
                state_out = parts[1]
            if len(parts) >= 3 and not country_out:
                country_out = parts[2]
        return location_out, city_out, state_out, country_out

    full_name = _str(
        basic_info.get('fullName')
        or basic_info.get('displayName')
        or basic_info.get('profileName')
        or basic_info.get('full_name')
        or basic_info.get('name')
        or basic_info.get('fullName')
        or
        raw.get('fullName')
        or raw.get('displayName')
        or raw.get('profileName')
        or raw.get('full_name')
        or raw.get('name')
        or _find_value(raw, ['fullName', 'displayName', 'profileName', 'full_name', 'name'])
        or ''
    )
    first_name = _str(basic_info.get('firstName') or basic_info.get('first_name') or raw.get('firstName') or raw.get('first_name') or _find_value(raw, ['firstName', 'first_name', 'givenName']))
    last_name = _str(basic_info.get('lastName') or basic_info.get('last_name') or raw.get('lastName') or raw.get('last_name') or _find_value(raw, ['lastName', 'last_name', 'familyName']))
    if full_name and not (first_name or last_name):
        parts = [part for part in full_name.split() if part]
        if parts:
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    # Location
    location_raw = basic_info.get('location') or basic_info.get('locationName') or raw.get('location') or raw.get('locationName') or raw.get('addressWithCountry') or _find_value(raw, ['location', 'locationName', 'addressWithCountry']) or ''
    geo = raw.get('geoLocation') or _find_value(raw, ['geoLocation']) or {}
    city = _str(basic_info.get('city') or raw.get('city') or (geo.get('city') if isinstance(geo, dict) else '') or _find_value(raw, ['city', 'cityName', 'locality']) or '')
    state = _str(basic_info.get('state') or raw.get('state') or (geo.get('state') if isinstance(geo, dict) else '') or raw.get('region') or _find_value(raw, ['state', 'region', 'stateName']) or '')
    country = _str(basic_info.get('country') or raw.get('country') or (geo.get('country') if isinstance(geo, dict) else '') or raw.get('countryCode') or _find_value(raw, ['country', 'countryCode', 'countryName']) or '')
    location_raw, city, state, country = _parse_location_parts(location_raw, city, state, country)
    if not location_raw:
        location_raw = ", ".join(part for part in [city, state, country] if part)

    # Current position
    experiences = (
        raw.get('experiences')
        or raw.get('positions')
        or raw.get('experience')
        or _find_list(raw, ['experiences', 'positions', 'experience', 'positionHistory', 'workExperience', 'employmentHistory'])
        or []
    )
    if experiences and isinstance(experiences[0], str):
        experiences = []
    current_pos = ''
    current_company = ''
    if experiences:
        current_items = [item for item in experiences if isinstance(item, dict) and item.get("current")]
        first = current_items[0] if current_items else (experiences[0] if isinstance(experiences[0], dict) else {})
        current_pos = _str(first.get('title') or first.get('position') or first.get('roleName') or '')
        current_company = _str(first.get('companyName') or first.get('company') or first.get('employer') or '')
    if not current_pos:
        current_pos = _str(basic_info.get('headline') or raw.get('currentPositionName') or _find_value(raw, ['currentPositionName', 'headline', 'occupation', 'title']))
    if not current_company:
        current_company = _str(basic_info.get('company') or raw.get('currentCompanyName') or _find_value(raw, ['currentCompanyName', 'companyName', 'company']))

    # About
    about = _str(basic_info.get('about') or basic_info.get('summary') or raw.get('summary') or raw.get('about') or raw.get('aboutSection') or raw.get('bio') or raw.get('description') or _find_value(raw, ['summary', 'about', 'aboutSection', 'bio', 'description']))

    # Skills - try multiple field names
    skills_raw = (
        raw.get('skills') or raw.get('skillsLabel') or raw.get('topSkills') or
        raw.get('skills2') or _find_value(raw, ['skills', 'skillsLabel', 'topSkills', 'skills2', 'skillsList', 'skillSet']) or []
    )
    skills = _list_of_str(skills_raw)
    if not skills:
        skills = _list_of_str(raw.get('skillsList') or raw.get('skillSet') or _find_value(raw, ['skillsList', 'skillSet']) or [])
    if not skills:
        experience_skill_blobs = []
        for item in experiences:
            if not isinstance(item, dict):
                continue
            experience_skill_blobs.extend(
                _list_of_str(item.get('skills') or item.get('technologies') or item.get('tools') or [])
            )
            skill_text = _str(item.get('skillsText') or item.get('description') or '')
            if 'skills:' in skill_text.lower():
                tail = skill_text.split(':', 1)[1]
                experience_skill_blobs.extend([part.strip(" -") for part in tail.split('·') if part.strip()])
        skills = [s for s in dict.fromkeys(experience_skill_blobs) if s]

    # Years of experience
    yoe = basic_info.get('yearsOfExperience') or raw.get('yearsOfExperience') or raw.get('totalYearsOfExperience') or _estimate_years_from_experience(experiences) or ''
    inferred = _guess_tools_and_strengths(raw)
    languages = _list_of_str(raw.get('languages') or raw.get('language') or raw.get('spokenLanguages') or _find_value(raw, ['languages', 'language', 'spokenLanguages']) or [])
    education = raw.get('educations') or raw.get('education') or raw.get('schools') or _find_list(raw, ['educations', 'education', 'schools']) or []
    certifications = raw.get('certifications') or raw.get('licenses') or _find_list(raw, ['certifications', 'licenses']) or []
    headline = _str(basic_info.get('headline') or raw.get('headline') or raw.get('title') or raw.get('occupation') or raw.get('position') or raw.get('professionalHeadline') or _find_value(raw, ['headline', 'title', 'occupation', 'position', 'professionalHeadline', 'subtitle']))

    extracted = {
        'firstName':           first_name,
        'lastName':            last_name,
        'headline':            headline,
        'about':               about,
        'currentPosition':     current_pos,
        'currentCompany':      current_company,
        'location':            location_raw,
        'city':                city,
        'state':               state,
        'country':             country,
        'email':               _str(raw.get('email') or _find_value(raw, ['email', 'emailAddress']) or ''),
        'phone':               _str(raw.get('phone') or raw.get('phoneNumber') or _find_value(raw, ['phone', 'phoneNumber']) or ''),
        'linkedinUrl':         full_url,
        'github':              _str(raw.get('github') or raw.get('githubUrl') or _find_value(raw, ['github', 'githubUrl']) or ''),
        'followers':           _str(raw.get('followersCount') or raw.get('followers') or _find_value(raw, ['followersCount', 'followers']) or ''),
        'connections':         _str(raw.get('connectionsCount') or raw.get('connections') or _find_value(raw, ['connectionsCount', 'connections']) or ''),
        'totalYearsExperience': _str(yoe),
        'skills':              skills,
        'tools':               inferred.get('tools', []),
        'languages':           languages,
        'experience':          experiences,
        'education':           education,
        'certifications':      certifications,
        'honors':              _str(raw.get('honors') or _find_value(raw, ['honors']) or ''),
        'volunteerWork':       _str(raw.get('volunteerWork') or _find_value(raw, ['volunteerWork', 'volunteering']) or ''),
        'publications':        _str(raw.get('publications') or _find_value(raw, ['publications']) or ''),
        'coreDomains':         [],
        'interests':           [],
        'industryInclination': _str(raw.get('industry') or raw.get('industryName') or _find_value(raw, ['industry', 'industryName']) or ''),
        'skillStrength':       '',
        'careerGoals':         '',
        'preferredRole':       current_pos or _str(raw.get('occupation') or _find_value(raw, ['occupation', 'headline']) or ''),
        'preferredIndustry':   '',
        'strengths':           inferred.get('strengths', ''),
        'weaknesses':          '',
        'workStyle':           '',
        'openToWork':          bool(raw.get('openToWork') or raw.get('isOpenToWork') or _find_value(raw, ['openToWork', 'isOpenToWork']) or False),
        'hobbies':             '',
    }
    return extracted


def _derive_post_signals(posts_items):
    hashtags = []
    keywords = Counter()
    stop_words = {
        "about", "after", "also", "been", "from", "have", "into", "just", "more",
        "over", "that", "their", "them", "they", "this", "today", "with", "your",
        "https", "linkedin", "post", "www", "com"
    }

    for post in (posts_items or []):
        text = (post.get('text') or post.get('content') or post.get('postContent') or '').strip()
        if not text:
            continue
        hashtags.extend(tag.lower().lstrip("#") for tag in _re.findall(r"#([A-Za-z][A-Za-z0-9_-]+)", text))
        for word in _re.findall(r"\b[A-Za-z][A-Za-z+\-]{3,}\b", text.lower()):
            if word not in stop_words:
                keywords[word] += 1

    return {
        "interests": [tag.replace("-", " ").replace("_", " ") for tag, _ in Counter(hashtags).most_common(5)],
        "coreDomains": [word.replace("-", " ") for word, _ in keywords.most_common(5)],
    }


def _merge_profile_fallback(primary, fallback):
    merged = dict(primary or {})
    for key, value in (fallback or {}).items():
        current = merged.get(key)
        if current in [None, "", [], {}]:
            merged[key] = value
        elif isinstance(current, list) and isinstance(value, list) and len(value) > len(current):
            merged[key] = value
    return merged


def _prefer_concrete_scrape_data(direct_profile, ai_profile, post_signals, full_url):
    merged = _normalize_profile_payload(direct_profile or {})
    ai_profile = _normalize_profile_payload(ai_profile or {})
    merged = _merge_profile_fallback(merged, ai_profile)
    merged = _merge_profile_fallback(merged, post_signals or {})

    # Prefer richer AI arrays only when the direct parser already found the field family
    # but returned a clearly weaker result.
    for field in ["skills", "tools", "languages", "experience", "education", "certifications"]:
        direct_value = merged.get(field)
        ai_value = ai_profile.get(field)
        if isinstance(direct_value, list) and isinstance(ai_value, list) and len(ai_value) > len(direct_value):
            merged[field] = ai_value

    for field in [
        "about", "headline", "industryInclination", "skillStrength", "careerGoals",
        "preferredRole", "preferredIndustry", "weaknesses", "workStyle",
        "hobbies", "github", "phone", "email",
    ]:
        if not merged.get(field) and ai_profile.get(field):
            merged[field] = ai_profile[field]

    merged["linkedinUrl"] = full_url
    merged["linkedin"] = full_url
    return _normalize_profile_payload(merged)


def _extract_text_blobs(value, limit=20):
    blobs = []
    if isinstance(value, str):
        text = value.strip()
        if text:
            blobs.append(text)
    elif isinstance(value, dict):
        for item in value.values():
            blobs.extend(_extract_text_blobs(item, limit))
            if len(blobs) >= limit:
                break
    elif isinstance(value, list):
        for item in value:
            blobs.extend(_extract_text_blobs(item, limit))
            if len(blobs) >= limit:
                break
    return blobs[:limit]


def _parse_month_token(token):
    token = (token or "").strip().lower()
    months = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
        "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
    }
    return months.get(token, 1)


def _parse_date_fragment(fragment, end=False):
    fragment = (fragment or "").strip()
    if not fragment:
        return None
    lowered = fragment.lower()
    if lowered in {"present", "current", "now", "today"}:
        now = datetime.utcnow()
        return datetime(now.year, now.month, 1)
    parts = fragment.replace(",", " ").split()
    year = None
    month = 1
    for part in parts:
        if part.isdigit() and len(part) == 4:
            year = int(part)
        else:
            maybe_month = _parse_month_token(part)
            if maybe_month:
                month = maybe_month
    if year is None:
        match = _re.search(r"(19|20)\d{2}", fragment)
        if match:
            year = int(match.group())
    if year is None:
        return None
    if end and month == 1 and len(parts) == 1:
        month = 12
    return datetime(year, month, 1)


def _estimate_years_from_experience(experiences):
    month_spans = []
    for item in experiences or []:
        if not isinstance(item, dict):
            continue
        date_text = (
            item.get("dateRange")
            or item.get("duration")
            or item.get("period")
            or item.get("timePeriod")
            or item.get("subtitle")
            or ""
        )
        if isinstance(date_text, dict):
            start = _parse_date_fragment(date_text.get("startDate"))
            end = _parse_date_fragment(date_text.get("endDate"), end=True) or datetime.utcnow()
            if start:
                month_spans.append((start.year * 12 + start.month, end.year * 12 + end.month))
            continue
        match = _re.search(
            r"([A-Za-z]{3,9}\s+\d{4}|\d{4})\s*[-–]\s*([A-Za-z]{3,9}\s+\d{4}|\d{4}|Present|Current|Now)",
            str(date_text),
            _re.IGNORECASE,
        )
        if not match:
            continue
        start = _parse_date_fragment(match.group(1))
        end = _parse_date_fragment(match.group(2), end=True) or datetime.utcnow()
        if start:
            month_spans.append((start.year * 12 + start.month, end.year * 12 + end.month))

    if not month_spans:
        return ""

    month_spans.sort()
    merged = [month_spans[0]]
    for start, end in month_spans[1:]:
        prev_start, prev_end = merged[-1]
        if start <= prev_end:
            merged[-1] = (prev_start, max(prev_end, end))
        else:
            merged.append((start, end))

    total_months = sum(max(0, end - start + 1) for start, end in merged)
    years = max(1, round(total_months / 12))
    return str(years)


def _guess_tools_and_strengths(payload):
    text = " ".join(_extract_text_blobs(payload, limit=80)).lower()
    tool_catalog = [
        "python", "java", "javascript", "typescript", "react", "node", "node.js", "angular",
        "vue", "docker", "kubernetes", "aws", "azure", "gcp", "sql", "mongodb", "postgresql",
        "mysql", "tensorflow", "pytorch", "figma", "jira", "notion", "git", "github",
        "linux", "excel", "tableau", "power bi", "spark", "hadoop"
    ]
    strengths_catalog = [
        "leadership", "mentoring", "product strategy", "communication", "public speaking",
        "research", "analytics", "problem solving", "stakeholder management", "team building",
        "project management", "entrepreneurship", "sales", "marketing"
    ]

    found_tools = []
    for tool in tool_catalog:
        if tool in text:
            normalized = tool.replace("node.js", "Node.js").replace("power bi", "Power BI").title()
            if normalized not in found_tools:
                found_tools.append(normalized)

    found_strengths = []
    for strength in strengths_catalog:
        if strength in text:
            normalized = strength.title()
            if normalized not in found_strengths:
                found_strengths.append(normalized)

    return {
        "tools": found_tools[:12],
        "strengths": ", ".join(found_strengths[:6]),
    }


def _infer_profile_enrichment(profile):
    enriched = dict(profile or {})
    headline = str(enriched.get("headline") or "").lower()
    about = str(enriched.get("about") or "").lower()
    current_position = str(enriched.get("currentPosition") or "").strip()
    combined = " ".join(
        part for part in [
            str(enriched.get("headline") or ""),
            str(enriched.get("about") or ""),
            current_position,
            str(enriched.get("currentCompany") or ""),
            ", ".join(enriched.get("skills") or []),
            ", ".join(enriched.get("tools") or []),
            ", ".join(enriched.get("coreDomains") or []),
        ] if part
    ).lower()

    if not enriched.get("preferredRole"):
        enriched["preferredRole"] = current_position or str(enriched.get("headline") or "").split("|")[0].strip()

    if not enriched.get("skillStrength"):
        years = 0
        try:
            years = int(str(enriched.get("totalYearsExperience") or enriched.get("experience_years") or "0").strip() or "0")
        except Exception:
            years = 0
        skill_count = len(enriched.get("skills") or [])
        if years >= 6 or skill_count >= 10:
            enriched["skillStrength"] = "Expert"
        elif years >= 3 or skill_count >= 6:
            enriched["skillStrength"] = "Advanced"
        elif years >= 1 or skill_count >= 2:
            enriched["skillStrength"] = "Intermediate"

    if not enriched.get("careerGoals"):
        if "looking for full-time" in headline:
            enriched["careerGoals"] = "Seeking a full-time software engineering role to build impactful products and solve real-world problems."
        elif current_position:
            enriched["careerGoals"] = f"To grow as a {current_position} and build impactful digital products."

    if not enriched.get("workStyle"):
        if "collabor" in combined or "team" in combined:
            enriched["workStyle"] = "Team"
        elif "remote" in combined:
            enriched["workStyle"] = "Remote"
        elif current_position:
            enriched["workStyle"] = "Team"

    if not enriched.get("strengths"):
        strengths = []
        strength_rules = [
            ("lead", "Leadership"),
            ("mentor", "Mentoring"),
            ("optimiz", "Problem Solving"),
            ("impact", "Impact-Driven Development"),
            ("cloud", "Cloud Engineering"),
            ("full-stack", "Full-Stack Development"),
            ("react", "Frontend Development"),
            ("python", "Backend Development"),
            ("data", "Data Engineering"),
        ]
        for token, label in strength_rules:
            if token in combined and label not in strengths:
                strengths.append(label)
        if strengths:
            enriched["strengths"] = ", ".join(strengths[:4])

    if not enriched.get("industryInclination"):
        if any(token in combined for token in ["saas", "software", "full-stack", "web", "react"]):
            enriched["industryInclination"] = "SaaS"
        elif any(token in combined for token in ["data", "analytics", "dbt", "snowflake"]):
            enriched["industryInclination"] = "Data & Analytics"
        elif any(token in combined for token in ["ai", "machine learning"]):
            enriched["industryInclination"] = "AI/ML"

    if not enriched.get("preferredIndustry"):
        enriched["preferredIndustry"] = enriched.get("industryInclination") or ""

    if not enriched.get("openToWork") and "looking for full-time" in headline:
        enriched["openToWork"] = True

    return enriched


def _normalize_profile_payload(payload):
    normalized = dict(payload or {})
    first = str(normalized.get("firstName") or "").strip()
    last = str(normalized.get("lastName") or "").strip()
    explicit_name = str(normalized.get("name") or "").strip()
    if first or last:
        normalized["name"] = " ".join(part for part in [first, last] if part).strip()
    elif explicit_name:
        normalized["name"] = explicit_name
    if not (first or last) and explicit_name:
        parts = explicit_name.split()
        if parts:
            normalized["firstName"] = parts[0]
            normalized["lastName"] = " ".join(parts[1:]).strip()
    if normalized.get("headline") and not normalized.get("professional_title"):
        normalized["professional_title"] = normalized["headline"]
    if normalized.get("about") and not normalized.get("bio"):
        normalized["bio"] = normalized["about"]
    if normalized.get("linkedinUrl") and not normalized.get("linkedin"):
        normalized["linkedin"] = normalized["linkedinUrl"]
    if not normalized.get("location"):
        normalized["location"] = ", ".join(
            part for part in [normalized.get("city"), normalized.get("state"), normalized.get("country")] if part
        )
    if normalized.get("totalYearsExperience") not in [None, ""] and not normalized.get("experience_years"):
        match = _re.search(r"\d+", str(normalized.get("totalYearsExperience")))
        if match:
            normalized["experience_years"] = int(match.group())
    if normalized.get("experience") and not normalized.get("totalYearsExperience"):
        normalized["totalYearsExperience"] = _estimate_years_from_experience(normalized.get("experience"))
    if normalized.get("experience_years") not in [None, "", 0] and not normalized.get("totalYearsExperience"):
        normalized["totalYearsExperience"] = str(normalized.get("experience_years"))
    return normalized


def _account_identity_overrides(current_user):
    identity = {
        "name": str(current_user.get("name") or "").strip(),
        "email": str(current_user.get("email") or "").strip(),
        "firstName": str(current_user.get("firstName") or "").strip(),
        "lastName": str(current_user.get("lastName") or "").strip(),
    }
    if not (identity["firstName"] or identity["lastName"]) and identity["name"]:
        parts = identity["name"].split()
        if parts:
            identity["firstName"] = parts[0]
            identity["lastName"] = " ".join(parts[1:]).strip()
    return _normalize_profile_payload(identity)


def _latest_user_message(chat_history):
    for msg in reversed(chat_history or []):
        if msg.get("role") == "user":
            return str(msg.get("text") or "").strip()
    return ""


def _infer_field_from_latest_reply(latest_text: str, remaining_fields: list[str]):
    text = (latest_text or "").strip()
    lowered = text.lower()
    if not text:
        return {}

    inferred = {}
    url_match = _re.search(r"https?://\S+|www\.\S+|[A-Za-z0-9_.-]+\.[A-Za-z]{2,}\S*", text)
    email_match = _re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", text, _re.IGNORECASE)
    phone_match = _re.search(r"(\+?\d[\d\s().-]{7,}\d)", text)

    if "github" in remaining_fields and ("github" in lowered or "git" in lowered or url_match):
        candidate = (url_match.group(0) if url_match else text).strip().rstrip(".,")
        if "github.com" not in candidate.lower() and "/" not in candidate and "github" not in lowered:
            candidate = f"https://github.com/{candidate.lstrip('@')}"
        if not candidate.startswith(("http://", "https://")):
            candidate = f"https://{candidate}"
        inferred["github"] = candidate

    if "email" in remaining_fields and email_match:
        inferred["email"] = email_match.group(0).strip()

    if "phone" in remaining_fields and phone_match:
        inferred["phone"] = phone_match.group(1).strip()

    list_like_fields = {"skills", "tools", "coreDomains", "interests", "languages"}
    target_field = remaining_fields[0] if remaining_fields else None
    if target_field in list_like_fields and "," in text and target_field not in inferred:
        inferred[target_field] = [part.strip() for part in text.split(",") if part.strip()]

    if target_field == "hobbies" and "hobbies" not in inferred and text and len(text) <= 200:
        inferred["hobbies"] = text

    if target_field == "workStyle" and text:
        styles = {
            "remote": "Remote",
            "hybrid": "Hybrid",
            "team": "Team",
            "individual": "Individual",
        }
        for key, value in styles.items():
            if key in lowered:
                inferred["workStyle"] = value
                break

    if target_field == "skillStrength" and text:
        strengths = {"beginner": "Beginner", "intermediate": "Intermediate", "advanced": "Advanced", "expert": "Expert"}
        for key, value in strengths.items():
            if key in lowered:
                inferred["skillStrength"] = value
                break

    return inferred
def _extract_image_id(url):
    if not url:
        return None
    import re
    cleaned = str(url).strip()
    patterns = [
        r"/image(?:/v2)?/([A-Za-z0-9_-]{5,})/",
        r"/dms/image/([A-Za-z0-9_-]{5,})",
        r"/profile-displayphoto-[^/]+/([A-Za-z0-9_-]{5,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            return match.group(1).lower()
    return cleaned.split("?", 1)[0].rstrip("/").lower()


def _normalize_linkedin_username(value):
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return ""
    match = _re.search(r"linkedin\.com/in/([^/?#\s]+)", raw, _re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    if "/" not in raw and "." not in raw:
        return raw.lower()
    tail = raw.split("/")[-1].strip()
    return tail.lower()


def _normalize_person_name(value):
    return _re.sub(r"[^a-z0-9]+", "", str(value or "").lower())


# ------------------------------------------------------------------
# POST /profile/scrape-linkedin
# ------------------------------------------------------------------

@profile_bp.route("/scrape-linkedin", methods=["POST"])
@token_required
def scrape_linkedin(current_user):
    data = request.json or {}
    linkedin_url = (data.get('linkedinUrl') or '').strip().rstrip('/')

    if not linkedin_url:
        return api_error("BAD_REQUEST", "LinkedIn URL is required", 400)

    apify_token = os.getenv("APIFY_TOKEN")
    if not apify_token:
        return api_error("CONFIG_ERROR", "APIFY_TOKEN not configured", 500)

    username = _normalize_linkedin_username(linkedin_url) if linkedin_url else ""
    full_url = f"https://www.linkedin.com/in/{username}" if username else ""

    PROFILE_ACTOR = os.getenv(
        "APIFY_ACTOR_ID",
        "apimaestro~linkedin-profile-batch-scraper-no-cookies-required",
    )
    # IMPORTANT: use a no-cookies posts actor by default.
    # Many "post search" actors require LinkedIn cookies/userAgent (will fail in prod).
    POSTS_ACTOR = os.getenv("APIFY_POSTS_ACTOR_ID", "supreme_coder~linkedin-post")

    # ---- Profile scrape (required) ----
    try:
        profile_items = _apify_run_and_wait(
            PROFILE_ACTOR,
            {"usernames": [username]},
            apify_token, max_polls=60, interval=5
        )
    except Exception as e:
        return api_error("SCRAPER_ERROR", f"Profile scraper failed: {str(e)}", 500)

    if not profile_items:
        return api_error("NO_DATA", "No profile data returned from LinkedIn scraper", 404)

    # ---- Posts scrape (best-effort) ----
    posts_items = []
    if POSTS_ACTOR:
        try:
            # `supreme_coder~linkedin-post` expects `urls` and optionally `limitPerSource`.
            # A profile URL is a supported source URL per actor docs.
            posts_items = _apify_run_and_wait(
                POSTS_ACTOR,
                {"urls": [full_url], "limitPerSource": 20, "deepScrape": False, "rawData": False},
                apify_token,
                max_polls=36,
                interval=5,
            )
        except Exception as e:
            print(f"[scrape_linkedin] Posts scraper non-fatal error: {e}")

    # Collect post text snippets
    posts_text_list = []
    for post in (posts_items or []):
        text = post.get('text') or post.get('content') or post.get('postContent') or ''
        if text:
            posts_text_list.append(text[:500])

    raw_profile = profile_items[0]
    direct_profile = _parse_apify_direct(raw_profile, full_url)
    post_signals = _derive_post_signals(posts_items)
    print(f"[scrape_linkedin] RAW APIFY KEYS: {list(raw_profile.keys())}")
    print(f"[scrape_linkedin] firstName={raw_profile.get('firstName')}  fullName={raw_profile.get('fullName')}  name={raw_profile.get('name')}")
    print(f"[scrape_linkedin] skills raw = {str(raw_profile.get('skills', raw_profile.get('skillsLabel', raw_profile.get('topSkills', 'NOT FOUND'))))[:200]}")

    # Build posts section for prompt
    posts_section = ""
    if posts_text_list:
        posts_section = "\nPOSTS (for coreDomains/interests):\n"
        posts_section += "\n".join(f"- {t[:200]}" for t in posts_text_list[:5])

    # Send the raw Apify profile directly to the LLM.
    # Truncate large text fields to stay within token limits.
    def _safe_dump(raw):
        """Trim the prompt payload to stay within OpenAI limits."""
        def _trim(value, depth=0):
            if isinstance(value, str):
                limit = 1200 if depth <= 1 else 500
                return value[:limit]
            if isinstance(value, list):
                items = value[:4 if depth == 0 else 3]
                return [_trim(item, depth + 1) for item in items]
            if isinstance(value, dict):
                trimmed = {}
                for key, child in list(value.items())[:20]:
                    trimmed[key] = _trim(child, depth + 1)
                return trimmed
            return value

        return _trim(dict(raw))

    profile_for_llm = _safe_dump({
        "basic_info": raw_profile.get("basic_info"),
        "experience": raw_profile.get("experience"),
        "education": raw_profile.get("education"),
        "projects": raw_profile.get("projects"),
        "certifications": raw_profile.get("certifications"),
        "featured": raw_profile.get("featured"),
        "profileUrl": raw_profile.get("profileUrl"),
    })
    posts_for_llm = []
    for post in (posts_items or [])[:4]:
        posts_for_llm.append({
            "text": (post.get("text") or post.get("content") or post.get("postContent") or "")[:350],
            "hashtags": (post.get("hashtags") or [])[:5],
            "publishedAt": post.get("postedAt") or post.get("timestamp") or post.get("date") or "",
        })
    baseline_parse = _normalize_profile_payload(_merge_profile_fallback(direct_profile, post_signals))

    prompt = f"""You are an expert LinkedIn profile interpreter.

Your task:
1. Read the COMPLETE scraped LinkedIn profile JSON.
2. Read the scraped posts JSON.
3. Use the baseline parser output only as a fallback starting point.
4. Return the most complete JSON possible for the edit-profile form.

IMPORTANT RULES:
- Read ALL fields carefully, even if field names are unusual.
- Use both profile JSON and post JSON.
- Fill as many fields as possible from evidence in the scrape.
- Infer reasonable values for:
  skillStrength, workStyle, preferredRole, preferredIndustry, industryInclination, strengths, careerGoals.
- Do NOT hallucinate contact details. If GitHub/email/phone are not present or strongly implied, leave them empty.
- `totalYearsExperience` should almost always be filled using experience history if available.
- `skills` = professional + technical skills.
- `tools` = technologies, software, frameworks, platforms.
- `coreDomains` = 3 to 6 main domains from work + posts.
- `interests` = 3 to 6 interests/themes from posts and profile.
- `experience` = preserve structured experience array from scrape if available.
- `education` = preserve structured education array from scrape if available.
- `about` = prefer summary/about/description/bio, otherwise synthesize a concise 2-4 sentence summary from the scraped profile.
- `strengths` should be a concise comma-separated string.
- `careerGoals` should be a short sentence, inferred from trajectory/posts if possible.
- Use "" for unknown strings, [] for unknown arrays, false for unknown booleans.
- Return ONLY valid JSON. No markdown. No explanation.

OUTPUT SCHEMA (return ONLY this JSON, no other text):
{{"firstName":"","lastName":"","headline":"","about":"","currentPosition":"","currentCompany":"","location":"","city":"","state":"","country":"","email":"","phone":"","linkedinUrl":"{full_url}","github":"","followers":"","connections":"","totalYearsExperience":"","skills":[],"tools":[],"experience":[],"education":[],"certifications":[],"languages":[],"honors":"","volunteerWork":"","publications":"","coreDomains":[],"interests":[],"industryInclination":"","skillStrength":"","careerGoals":"","preferredRole":"","preferredIndustry":"","strengths":"","weaknesses":"","workStyle":"","openToWork":false,"hobbies":""}}

BASELINE PARSED DATA:
{json.dumps(baseline_parse, ensure_ascii=False)}

RAW LINKEDIN PROFILE DATA:
{json.dumps(profile_for_llm, ensure_ascii=False)}

SCRAPED POSTS DATA:
{json.dumps(posts_for_llm, ensure_ascii=False)}
{posts_section}"""

    # ---- Call LLM with retry backoff (best-effort) ----
    #
    # IMPORTANT:
    # OpenAI can return 429 (rate limit) or other transient errors.
    # We treat LLM enrichment as best-effort and fall back to direct
    # parsing of Apify output so the scrape flow still works.
    def _is_ai_rate_limit(err_text: str) -> bool:
        t = (err_text or "").upper()
        return ("429" in t) or ("413" in t) or ("RESOURCE_EXHAUSTED" in t) or ("QUOTA" in t) or ("REQUEST TOO LARGE" in t)

    def _is_ai_busy(err_text: str) -> bool:
        t = (err_text or "").upper()
        return ("503" in t) or ("UNAVAILABLE" in t) or ("SERVICE UNAVAILABLE" in t)

    response = None
    ai_error_code = None
    ai_error_message = None
    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=5000,
                response_format={"type": "json_object"}
            )
            print(f"[scrape_linkedin] LLM OK (attempt {attempt+1}). Response len={len(response.choices[0].message.content)}")
            break  # success
        except Exception as e:
            err = str(e)
            if attempt < MAX_RETRIES - 1 and (_is_ai_rate_limit(err) or _is_ai_busy(err)):
                wait_secs = 15 * (attempt + 1)
                print(f"[scrape_linkedin] LLM attempt {attempt+1} failed ({err[:120]}). Waiting {wait_secs}s...")
                time.sleep(wait_secs)
                continue
            if _is_ai_rate_limit(err):
                ai_error_code = "AI_RATE_LIMIT"
                ai_error_message = "LLM prompt exceeded current limit; returning basic profile without AI enrichment."
            elif _is_ai_busy(err):
                ai_error_code = "AI_BUSY"
                ai_error_message = "LLM temporarily unavailable; returning basic profile without AI enrichment."
            else:
                ai_error_code = "AI_ERROR"
                ai_error_message = f"LLM error; returning basic profile without AI enrichment. ({err[:200]})"
                print(f"[scrape_linkedin] FATAL LLM ERROR: {err}")
            response = None
            break

    extracted = None
    missing_fields = []

    if response is not None:
        try:
            clean_text = response.choices[0].message.content.strip()
            if clean_text.startswith("```"):
                parts = clean_text.split("```")
                clean_text = parts[1] if len(parts) > 1 else parts[0]
                if clean_text.lower().startswith("json"):
                    clean_text = clean_text[4:]
            extracted = json.loads(clean_text.strip())
        except Exception as e:
            print(f"[scrape_linkedin] PARSE ERROR: {e}")
            ai_error_code = "PARSE_ERROR"
            ai_error_message = f"AI returned invalid JSON; returning basic profile without AI enrichment. ({str(e)})"
            extracted = None

    print(f"[scrape_linkedin] ai_error_code={ai_error_code}  ai_error_message={ai_error_message}")
    print(f"[scrape_linkedin] extracted keys: {list(extracted.keys()) if extracted else 'None (using direct parse)'}")
    print(f"[scrape_linkedin] firstName={extracted.get('firstName') if extracted else 'N/A'}  skills={extracted.get('skills', [])[:3] if extracted else 'N/A'}")

    if extracted is None:
        extracted = direct_profile

    extracted = _prefer_concrete_scrape_data(direct_profile, extracted, post_signals, full_url)
    extracted = _infer_profile_enrichment(extracted)
    identity_overrides = _account_identity_overrides(current_user)
    for field in ["name", "email", "firstName", "lastName"]:
        if identity_overrides.get(field):
            extracted[field] = identity_overrides[field]
    extracted = _normalize_profile_payload(extracted)

    for field in PROFILE_COMPLETION_FIELDS:
        val = extracted.get(field)
        if val is None or val == "" or val == [] or val == {}:
            missing_fields.append(field)
        elif isinstance(val, list) and len(val) < 2:
            if field in {"skills", "tools", "coreDomains", "interests"}:
                missing_fields.append(field)

    # ---- Deep post analysis via OpenAI (best-effort) ----
    deep_post_insights = {}
    if posts_items and Config.OPENAI_API_KEY:
        try:
            deep_post_insights = analyze_posts_deeply(
                posts_items,
                profile_context={
                    "name": extracted.get("firstName", "") + " " + extracted.get("lastName", ""),
                    "headline": extracted.get("headline", ""),
                    "skills": extracted.get("skills", []),
                }
            )
            print(f"[scrape_linkedin] Deep post insights keys: {list(deep_post_insights.keys())}")

            # Merge discovered skills/tools/domains into extracted
            for field, key in [("skills", "discoveredSkills"), ("tools", "tools"), ("coreDomains", "coreDomains"), ("interests", "areasOfInterest")]:
                new_vals = deep_post_insights.get(key, [])
                if new_vals and isinstance(new_vals, list):
                    existing = extracted.get(field, [])
                    if isinstance(existing, str):
                        existing = [s.strip() for s in existing.split(",") if s.strip()]
                    merged = list(dict.fromkeys(existing + new_vals))
                    extracted[field] = merged

            # Auto-create certifications from posts if not already present
            post_certs = deep_post_insights.get("certifications", [])
            if post_certs:
                existing_certs = extracted.get("certifications", [])
                existing_cert_names = {str(c.get("name", c) if isinstance(c, dict) else c).lower() for c in existing_certs}
                for cert in post_certs:
                    if cert.lower() not in existing_cert_names:
                        existing_certs.append({"name": cert, "source": "linkedin_posts"})
                extracted["certifications"] = existing_certs

        except Exception as e:
            print(f"[scrape_linkedin] Deep post analysis non-fatal error: {e}")

    # Build extraFields from deep insights
    extra_fields = extracted.get("extraFields", {}) or {}
    if deep_post_insights:
        dynamic = deep_post_insights.get("dynamicFields", {})
        if isinstance(dynamic, dict):
            extra_fields.update(dynamic)
        for insight_key in ["thoughtLeadershipTopics", "communityInvolvement", "projectsMentioned", "achievementSignals", "industryFocus"]:
            val = deep_post_insights.get(insight_key, [])
            if val:
                extra_fields[insight_key] = val if isinstance(val, list) else str(val)
        if deep_post_insights.get("contentStyle"):
            extra_fields["content_style"] = deep_post_insights["contentStyle"]
        if deep_post_insights.get("expertiseLevel"):
            extra_fields["expertise_level"] = deep_post_insights["expertiseLevel"]
    extracted["extraFields"] = extra_fields

    # Build dynamic field labels for the frontend
    dynamic_field_labels = {}
    if deep_post_insights.get("dynamicFields"):
        for k in deep_post_insights["dynamicFields"]:
            dynamic_field_labels[k] = k.replace("_", " ").title()
    for insight_key in ["thoughtLeadershipTopics", "communityInvolvement", "projectsMentioned", "achievementSignals", "industryFocus"]:
        if extra_fields.get(insight_key):
            dynamic_field_labels[insight_key] = insight_key.replace("_", " ").replace("Topics", " Topics").title().strip()
    if extra_fields.get("content_style"):
        dynamic_field_labels["content_style"] = "Content Style"
    if extra_fields.get("expertise_level"):
        dynamic_field_labels["expertise_level"] = "Expertise Level"

    replacement_fields = {k: extracted.get(k) for k in PROFILE_ALLOWED_FIELDS if k in extracted}
    if replacement_fields.get("experience_years") in [None, ""] and replacement_fields.get("totalYearsExperience"):
        match = _re.search(r"\d+", str(replacement_fields.get("totalYearsExperience")))
        if match:
            replacement_fields["experience_years"] = int(match.group())
    for field in ["name", "email", "firstName", "lastName"]:
        if identity_overrides.get(field):
            replacement_fields[field] = identity_overrides[field]
    replacement_fields = _normalize_profile_payload(replacement_fields)
    replacement_fields["scrapedAt"] = datetime.utcnow()
    replacement_fields["extraFields"] = extra_fields
    replacement_fields["dynamicFieldLabels"] = dynamic_field_labels

    # ── DO NOT save to DB or index here ──
    # Scraped data is returned to the frontend only.
    # Nothing persists until the user explicitly clicks "Save Profile".
    # This ensures privacy — scraped data is client-side only until saved.

    return api_success(
        {
            "profileData": extracted,
            "missingFields": missing_fields,
            "postsScraped": len(posts_items),
            "aiEnrichmentUsed": response is not None and ai_error_code is None,
            "aiStatus": "ok" if (response is not None and ai_error_code is None) else "degraded",
            "aiErrorCode": ai_error_code,
            "aiErrorMessage": ai_error_message,
            "deepPostInsights": deep_post_insights,
            "extraFields": extra_fields,
            "dynamicFieldLabels": dynamic_field_labels,
        },
        "Profile scraped successfully — review and click Save to persist"
        if ai_error_code is None
        else "Profile scraped (AI enrichment unavailable) — review and click Save to persist",
    )





# ------------------------------------------------------------------
# POST /profile/chat-fill
# ------------------------------------------------------------------

@profile_bp.route("/chat-fill", methods=["POST"])
@token_required
def chat_fill(current_user):
    data = request.json
    chat_history   = data.get('messages', [])
    missing_fields = data.get('missingFields', [])
    profile_ctx    = _normalize_profile_payload(data.get('profileContext', {}) or {})

    FIELD_LABELS = {
        'firstName': 'First Name', 'lastName': 'Last Name',
        'headline': 'Professional Headline', 'about': 'Bio / About Me',
        'currentPosition': 'Current Role', 'currentCompany': 'Current Company',
        'totalYearsExperience': 'Years of Experience',
        'skills': 'Skills', 'tools': 'Tools & Technologies',
        'coreDomains': 'Core Domains', 'interests': 'Interests',
        'industryInclination': 'Industry Inclination',
        'careerGoals': 'Career Goals', 'preferredRole': 'Preferred Role',
        'preferredIndustry': 'Preferred Industry',
        'strengths': 'Strengths', 'hobbies': 'Hobbies',
        'workStyle': 'Work Style (Team / Remote / Hybrid)',
        'github': 'GitHub URL', 'email': 'Email', 'phone': 'Phone Number',
        'skillStrength': 'Skill Strength', 'languages': 'Languages',
    }
    requested_missing_fields = [field for field in missing_fields if field in PROFILE_COMPLETION_FIELDS]
    missing_fields = requested_missing_fields or PROFILE_COMPLETION_FIELDS[:]
    missing_labels = [FIELD_LABELS.get(f, f) for f in missing_fields]
    latest_user_text = _latest_user_message(chat_history)

    ctx_str = ""
    if profile_ctx:
        filled = {k: v for k, v in profile_ctx.items() if v not in [None, "", [], {}]}
        if filled:
            ctx_str = f"Profile so far: {json.dumps(filled, ensure_ascii=False)[:8000]}"

    schema = {
        "message": "short friendly reply to show in chat",
        "updated_data": {
            "fieldName": "value captured from the user's latest answer"
        },
        "remaining_fields": ["still-missing-field-name"],
        "next_question": "single next question if more details are needed, else empty string",
        "completed": False,
    }

    system_instruction = f"""You are a friendly profile completion assistant helping a professional complete an edit-profile form.

{ctx_str}

Fields still needed: {', '.join(missing_labels) if missing_labels else 'None'}

You must read the entire chat history and extract structured field updates from the USER'S MOST RECENT ANSWER.
This assistant stays available even after the profile is complete, because the user may ask to add, remove, or change details later.

Rules:
- Return ONLY JSON matching the schema shown below.
- `updated_data` must contain any profile fields you can confidently fill from the latest user message.
- Update fields immediately when the user gives them. Example: if the user says `github.com/sachin-2004jlr`, set `github` to that value in `updated_data`.
- If the user says to add something to an existing list field, return only the new items in `updated_data` for that field.
- If the user asks to update or correct an existing field, return the corrected value in `updated_data`.
- For list fields (`skills`, `tools`, `coreDomains`, `interests`, `languages`), convert comma-separated answers into arrays.
- If the latest answer does not provide a value for a field, do not invent one.
- Ask ONE clear next question at a time in `next_question`.
- `message` should briefly acknowledge what you captured and then ask the next question naturally.
- Set `completed` to true only when no important fields remain except optional ones like GitHub or phone, but still keep helping with future updates.
- `remaining_fields` should exclude fields already present in the profile context or captured from the latest answer.

Supported fields:
firstName, lastName, headline, about, currentPosition, currentCompany, totalYearsExperience, skills, tools,
coreDomains, interests, industryInclination, careerGoals, preferredRole, preferredIndustry,
strengths, hobbies, workStyle, github, email, phone, skillStrength, languages

JSON schema:
{json.dumps(schema, ensure_ascii=False)}"""

    formatted_history = []
    for msg in chat_history:
        role = "user" if msg['role'] == "user" else "assistant"
        formatted_history.append({"role": role, "content": msg['text']})

    messages = [
        {"role": "system", "content": system_instruction},
        *formatted_history,
    ]

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.2,
            max_tokens=900,
            response_format={"type": "json_object"}
        )
        raw_content = response.choices[0].message.content.strip()
        parsed = json.loads(raw_content)
        updated_data = _normalize_profile_payload(parsed.get("updated_data", {}) or {})
        remaining = parsed.get("remaining_fields") or []
        next_question = (parsed.get("next_question") or "").strip()
        completed = bool(parsed.get("completed"))

        if latest_user_text:
            fallback_updates = _infer_field_from_latest_reply(latest_user_text, missing_fields)
            updated_data = _normalize_profile_payload(_merge_profile_fallback(updated_data, fallback_updates))

        for key in ["skills", "tools", "coreDomains", "interests", "languages"]:
            if key in updated_data and isinstance(updated_data[key], str):
                updated_data[key] = [part.strip() for part in updated_data[key].split(",") if part.strip()]

        merged_ctx = _normalize_profile_payload(_merge_profile_fallback(updated_data, profile_ctx))
        normalized_remaining = []
        remaining_order = requested_missing_fields + [field for field in PROFILE_COMPLETION_FIELDS if field not in requested_missing_fields]
        for field in remaining_order:
            val = merged_ctx.get(field)
            if val in [None, "", [], {}]:
                normalized_remaining.append(field)
            elif isinstance(val, list) and field in {"skills", "tools", "coreDomains", "interests"} and len(val) < 2:
                normalized_remaining.append(field)

        if remaining:
            remaining = [field for field in remaining if field in normalized_remaining]
        else:
            remaining = normalized_remaining

        completed = len(remaining) == 0

        if not next_question and remaining:
            first_missing = remaining[0]
            label = FIELD_LABELS.get(first_missing, first_missing)
            next_question = f"Could you share your {label.lower()}?"

        message = (parsed.get("message") or "").strip()
        if not message and updated_data:
            captured_labels = [FIELD_LABELS.get(key, key) for key in updated_data.keys()]
            message = f"Noted: {', '.join(captured_labels)} updated."

        if not message:
            if completed:
                message = "Great! Your profile looks complete. You can still keep chatting if you want to add or edit anything before saving."
            elif next_question:
                message = next_question
            else:
                message = "Thanks. I updated that detail in your profile form."
        elif next_question and next_question.lower() not in message.lower():
            message = f"{message} {next_question}".strip()

        return api_success({
            "reply": message,
            "updatedData": updated_data,
            "remainingFields": remaining,
            "nextQuestion": next_question,
            "completed": completed,
        })
    except Exception as e:
        err = str(e)
        if "429" in err:
            return api_error("AI_RATE_LIMIT", "AI is busy — wait 30 seconds and try again.", 429)
        if "503" in err or "UNAVAILABLE" in err:
            return api_error("AI_BUSY", "AI model is busy. Please try again in a moment.", 503)
        return api_error("AI_ERROR", f"Chat AI failed: {err}", 500)


# ------------------------------------------------------------------
# POST /profile/founder-chat  (OpenAI-powered founder profiling chatbot)
# ------------------------------------------------------------------

@profile_bp.route("/founder-chat", methods=["POST"])
@token_required
def founder_chat(current_user):
    """LLM-driven chatbot that collects founder/cofounder profiling data dynamically."""
    data = request.json or {}
    chat_history = data.get('messages', [])
    profile_ctx = data.get('profileContext', {}) or {}
    discovered_fields = data.get('discoveredFields', {}) or {}

    # Load existing extraFields from user
    existing_extra = current_user.get('extraFields', {}) or {}
    existing_labels = current_user.get('dynamicFieldLabels', {}) or {}

    if not Config.OPENAI_API_KEY:
        return api_error("CONFIG_ERROR", "OpenAI API key not configured", 500)

    result = founder_chatbot_respond(
        chat_history=chat_history,
        profile_context=profile_ctx,
        discovered_fields=discovered_fields,
        extra_fields=existing_extra,
    )

    # Merge extracted fields — return to client only, DO NOT save to DB here.
    # Everything persists only when the user clicks "Save Profile".
    new_fields = result.get("extractedFields", {})
    new_labels = result.get("fieldLabels", {})
    if new_fields:
        merged_extra = {**existing_extra, **new_fields}
        merged_labels = {**existing_labels, **new_labels}
    else:
        merged_extra = existing_extra
        merged_labels = existing_labels

    print(f"[founder_chat] OpenAI raw result keys: {list(result.keys())}")
    print(f"[founder_chat] extractedFields={new_fields}")
    print(f"[founder_chat] fieldLabels={new_labels}")
    print(f"[founder_chat] allExtraFields keys={list(merged_extra.keys())}")

    return api_success({
        "reply": result.get("message", ""),
        "extractedFields": new_fields,
        "fieldLabels": new_labels,
        "allExtraFields": merged_extra,
        "allFieldLabels": merged_labels,
        "nextQuestion": result.get("nextQuestion", ""),
        "conversationComplete": result.get("conversationComplete", False),
    })


# ------------------------------------------------------------------
# POST /profile/rewrite-text  (AI text enhancer — like LinkedIn's AI rewrite)
# ------------------------------------------------------------------

@profile_bp.route("/rewrite-text", methods=["POST"])
@token_required
def rewrite_text(current_user):
    """Rewrite user text in different styles: shorten, elevator pitch, formal, etc."""
    data = request.json or {}
    text = (data.get("text") or "").strip()
    style = (data.get("style") or "professional").strip().lower()

    if not text:
        return api_error("BAD_REQUEST", "Text is required", 400)
    if len(text) > 5000:
        return api_error("BAD_REQUEST", "Text too long (max 5000 chars)", 400)

    style_prompts = {
        "professional": "Rewrite this as a polished, professional summary suitable for a co-founder matching platform. Keep the same meaning but make it sound confident and credible. 2-4 sentences.",
        "shorten": "Condense this into 1-2 punchy sentences. Keep the most impactful points only. Be concise and direct.",
        "elevator_pitch": "Turn this into a compelling 30-second elevator pitch. Start with a hook, highlight the unique value, end with a call to action. 3-4 sentences max.",
        "formal": "Rewrite this in a formal, corporate tone suitable for investors or board members. Use precise language and quantifiable achievements where possible.",
        "casual": "Rewrite this in a friendly, approachable tone as if talking to a potential co-founder over coffee. Keep it genuine and conversational.",
        "lengthy": "Expand this into a detailed, comprehensive description. Add context, elaborate on key points, and paint a fuller picture. 5-8 sentences.",
        "storytelling": "Rewrite this as a compelling narrative. Start with a challenge or origin story, build through achievements, and end with vision. Make it memorable.",
        "technical": "Rewrite this emphasizing technical depth and engineering excellence. Highlight specific technologies, architectures, and quantifiable technical outcomes.",
    }

    instruction = style_prompts.get(style, style_prompts["professional"])

    # Include user context for better rewrites
    user_context = ""
    name = current_user.get("name", "")
    title = current_user.get("professional_title") or current_user.get("headline", "")
    if name or title:
        user_context = f"\nContext: This person is {name}{', ' + title if title else ''}."

    prompt = f"""{instruction}
{user_context}

Original text:
\"\"\"{text}\"\"\"

Return ONLY the rewritten text. No quotes, no explanation, no markdown."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )
        rewritten = response.choices[0].message.content.strip().strip('"').strip("'")
        return api_success({
            "original": text,
            "rewritten": rewritten,
            "style": style,
        })
    except Exception as e:
        return api_error("AI_ERROR", f"Rewrite failed: {str(e)}", 500)


# ------------------------------------------------------------------
# POST /profile/text-to-speech  (OpenAI TTS for founder intro)
# ------------------------------------------------------------------

@profile_bp.route("/text-to-speech", methods=["POST"])
@token_required
def text_to_speech(current_user):
    """Convert text to speech using OpenAI TTS."""
    data = request.json or {}
    text = (data.get("text") or "").strip()
    voice = data.get("voice", "alloy")  # alloy, echo, fable, onyx, nova, shimmer

    if not text:
        return api_error("BAD_REQUEST", "Text is required", 400)
    if len(text) > 4096:
        return api_error("BAD_REQUEST", "Text too long for TTS (max 4096 chars)", 400)

    try:
        from flask import send_file
        response = openai_client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
        )
        audio_bytes = response.content
        return send_file(
            io.BytesIO(audio_bytes),
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="intro.mp3",
        )
    except Exception as e:
        return api_error("TTS_ERROR", f"Text-to-speech failed: {str(e)}", 500)


# ------------------------------------------------------------------
# POST /profile/speech-to-text  (OpenAI Whisper for voice input)
# ------------------------------------------------------------------

@profile_bp.route("/speech-to-text", methods=["POST"])
@token_required
def speech_to_text(current_user):
    """Transcribe voice input using OpenAI Whisper."""
    if "audio" not in request.files:
        return api_error("BAD_REQUEST", "Audio file is required", 400)

    audio_file = request.files["audio"]
    try:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=(audio_file.filename or "audio.webm", audio_file.read(), audio_file.content_type or "audio/webm"),
        )
        return api_success({
            "text": transcript.text,
        })
    except Exception as e:
        return api_error("STT_ERROR", f"Speech-to-text failed: {str(e)}", 500)


# ------------------------------------------------------------------
# POST /profile/upload-resume
# ------------------------------------------------------------------

@profile_bp.route("/upload-resume", methods=["POST"])
@token_required
def upload_resume(current_user):
    """
    Upload flow:
    1. Read file bytes from request
    2. Delete old GridFS file if exists
    3. Store new file in GridFS (MongoDB) → file_id
    4. Write bytes to temp file for parsing
    5. LLM analysis: skills, experience, summary
    6. Store resume_text + file_id on user document in MongoDB
    7. Upsert Pinecone vector in background (includes resume_text)
    8. Delete temp file

    The file binary lives in MongoDB GridFS — shared across
    every developer and every server using the same database.
    """
    if "resume" not in request.files:
        return validation_error("No resume file provided")

    file = request.files["resume"]

    if file.filename == "":
        return validation_error("No file selected")

    if not allowed_file(file.filename):
        return validation_error("Only PDF and DOCX files are allowed")

    # Check size (10MB limit)
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)
    if file_size > 10 * 1024 * 1024:
        return validation_error("File size must be less than 10MB")

    filename = secure_filename(f"{current_user['_id']}_{file.filename}")
    content_type = file.content_type or "application/octet-stream"
    file_bytes = file.read()

    fs = _get_fs()

    # Delete previous GridFS file so we don't accumulate old resumes
    old_file_id = current_user.get("resume_file_id")
    if old_file_id:
        try:
            fs.delete(ObjectId(old_file_id))
            print(f"[profile] Deleted old GridFS file {old_file_id}")
        except Exception as e:
            print(f"[profile] Could not delete old GridFS file: {e}")

    # Store in GridFS
    file_id = fs.put(
        file_bytes,
        filename=filename,
        content_type=content_type,
        user_id=str(current_user["_id"]),
    )
    print(f"[profile] Stored resume in GridFS with id: {file_id}")

    # Write to temp file for parsing (temp file is local, deleted right after)
    suffix = ".pdf" if filename.lower().endswith(".pdf") else ".docx"
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        # Full LLM analysis
        analysis = ats_service.comprehensive_profile_analysis(current_user, tmp_path)

    except Exception as e:
        return api_error("RESUME_ANALYSIS_FAILED", f"Failed to analyse resume: {str(e)}", 500)

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Update user document in MongoDB
    update_data = {
        "resume_file_id": str(file_id),
        "resume": filename,          # display name only
        "resume_parsed": True,
        "resume_text": analysis.get("resume_text", ""),  # full text for ATS + Pinecone
    }

    if analysis.get("merged_skills"):
        update_data["skills"] = analysis["merged_skills"]

    extracted_exp = (
        analysis.get("ai_insights", {}).get("experience_years", 0)
        or analysis.get("resume_analysis", {}).get("estimated_experience", 0)
    )
    if extracted_exp and extracted_exp > current_user.get("experience_years", 0):
        update_data["experience_years"] = extracted_exp

    User.update_profile(current_user["_id"], update_data)

    # Pinecone upsert in background (vector now includes full resume text)
    _start_vector_upsert(current_user["_id"])
    Project.clear_all_cached_matches()

    updated_user = User.find_by_id(current_user["_id"])
    updated_user.pop("password", None)

    return api_success({
        "message": "Resume uploaded and analysed successfully",
        "analysis": analysis,
        "user": updated_user,
        "vector_update_initiated": True,
        "match_cache_invalidated": True,
    }, message="Resume uploaded and analysed successfully")


# ------------------------------------------------------------------
# GET /profile/resume/<user_id>
# ------------------------------------------------------------------

@profile_bp.route("/resume/<user_id>", methods=["GET"])
@token_required
def get_resume(current_user, user_id):
    """
    Serve a user's resume file directly from GridFS.
    Works on any developer's machine — file is in MongoDB, not local disk.
    Founders can use this to download candidate resumes.
    """
    target_user = User.find_by_id(user_id)
    if not target_user:
        return api_error("USER_NOT_FOUND", "User not found", 404)

    file_id = target_user.get("resume_file_id")
    if not file_id:
        return api_error("RESUME_NOT_FOUND", "No resume uploaded for this user", 404)

    try:
        fs = _get_fs()
        grid_out = fs.get(ObjectId(file_id))
        return send_file(
            io.BytesIO(grid_out.read()),
            mimetype=grid_out.content_type or "application/pdf",
            download_name=grid_out.filename,
            as_attachment=True,
        )
    except gridfs.errors.NoFile:
        return api_error("RESUME_NOT_FOUND", "Resume file not found in storage", 404)
    except Exception as e:
        return api_error("RESUME_FETCH_FAILED", f"Failed to retrieve resume: {str(e)}", 500)


# ------------------------------------------------------------------
# DELETE /profile/delete-resume
# ------------------------------------------------------------------

@profile_bp.route("/delete-resume", methods=["DELETE"])
@token_required
def delete_resume(current_user):
    """
    Delete resume from GridFS and clear all resume fields on the user doc.
    Re-indexes in Pinecone so the vector no longer reflects resume content.
    """
    if not current_user.get("resume_file_id") and not current_user.get("resume"):
        return api_error("RESUME_NOT_FOUND", "No resume to delete", 404)

    file_id = current_user.get("resume_file_id")
    if file_id:
        try:
            fs = _get_fs()
            fs.delete(ObjectId(file_id))
            print(f"[profile] Deleted GridFS file {file_id}")
        except Exception as e:
            print(f"[profile] GridFS delete error: {e}")

    User.update_profile(current_user["_id"], {
        "resume": "",
        "resume_file_id": None,
        "resume_parsed": False,
        "resume_text": "",
    })

    _start_vector_upsert(current_user["_id"])
    Project.clear_all_cached_matches()

    return api_success({
        "message": "Resume deleted successfully",
        "vector_update_initiated": True,
        "match_cache_invalidated": True,
    }, message="Resume deleted successfully")


# ------------------------------------------------------------------
# GET /profile/ats-score/<project_id>
# ------------------------------------------------------------------

@profile_bp.route("/ats-score/<project_id>", methods=["GET"])
@token_required
def calculate_ats_score(current_user, project_id):
    """
    LLM-driven ATS score against a project.

    Reads only from MongoDB fields — no file I/O, no GridFS read needed here.
    resume_text was stored in MongoDB at upload time so it is always available
    regardless of which developer's machine is handling this request.
    """
    from models.project import Project

    project = Project.find_by_id(project_id)
    if not project:
        return api_error("PROJECT_NOT_FOUND", "Project not found", 404)

    candidate_text = ats_service.build_candidate_text(current_user)

    score_data = ats_service.calculate_ats_score(candidate_text, project["description"])
    tips = ats_service.generate_profile_optimization_tips(candidate_text, project["description"])

    result = {
        "project_id": project_id,
        "project_title": project["title"],
        "ats_score": score_data,
        "optimization_tips": tips,
    }

    ws_service.emit_ats_score_update(current_user["_id"], result)
    return api_success(result, message="ATS score calculated")


# ------------------------------------------------------------------
# POST /profile/analyze-resume
# ------------------------------------------------------------------

@profile_bp.route("/analyze-resume", methods=["POST"])
@token_required
def analyze_current_resume(current_user):
    """
    Re-run LLM analysis on the stored resume.
    Reads from GridFS first (shared), falls back to stored resume_text.
    """
    file_id = current_user.get("resume_file_id")
    resume_text_stored = current_user.get("resume_text", "")

    if not file_id and not resume_text_stored:
        return api_error("RESUME_NOT_FOUND", "No resume uploaded", 404)

    tmp_path = None
    try:
        if file_id:
            try:
                fs = _get_fs()
                grid_out = fs.get(ObjectId(file_id))
                file_bytes = grid_out.read()
                filename = grid_out.filename or "resume.pdf"
                suffix = ".pdf" if filename.lower().endswith(".pdf") else ".docx"

                with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                    tmp.write(file_bytes)
                    tmp_path = tmp.name

                analysis = ats_service.comprehensive_profile_analysis(current_user, tmp_path)

            except gridfs.errors.NoFile:
                # GridFS file gone but text is in MongoDB — use it
                if not resume_text_stored:
                    return api_error("RESUME_NOT_FOUND", "Resume file not found in storage", 404)
                ai_insights = ats_service.analyze_resume_with_ai(resume_text_stored)
                analysis = {"ai_insights": ai_insights, "resume_text": resume_text_stored}
        else:
            ai_insights = ats_service.analyze_resume_with_ai(resume_text_stored)
            analysis = {"ai_insights": ai_insights, "resume_text": resume_text_stored}

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return api_success({
        "message": "Resume analysed successfully",
        "analysis": analysis,
    }, message="Resume analysed successfully")


# ------------------------------------------------------------------
# POST /profile/skills-suggestions
# ------------------------------------------------------------------

@profile_bp.route("/skills-suggestions", methods=["POST"])
@token_required
def get_skills_suggestions(current_user):
    """LLM-powered skill gap suggestions based on current profile."""
    data = request.get_json(silent=True) or {}
    target_role = data.get("target_role", current_user.get("professional_title", ""))

    prompt = f"""
Based on this professional profile, suggest 10-15 relevant skills to add.

Current profile:
- Name: {current_user.get('name', '')}
- Bio: {current_user.get('bio', '')}
- Current Skills: {', '.join(current_user.get('skills', []))}
- Experience: {current_user.get('experience_years', 0)} years
- Target Role: {target_role}

Consider industry trends, complementary skills, and gaps common for this career path.

Respond ONLY with valid JSON — no markdown fences:
{{
    "suggested_skills": ["skill1", "skill2", ...],
    "reasoning": "brief explanation"
}}
"""
    try:
        result = ats_service.llm_service.generate_json(prompt)
        return api_success(result if result else {"suggested_skills": []}, message="Skill suggestions fetched")
    except Exception as e:
        return api_error("SKILLS_SUGGESTIONS_FAILED", str(e), 500)
