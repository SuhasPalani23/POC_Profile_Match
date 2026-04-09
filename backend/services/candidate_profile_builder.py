from services.matching_taxonomy import (
    dedupe_terms,
    extract_known_terms,
    infer_domain_labels,
    infer_roles,
    is_noisy_skill,
    normalize_term,
    parse_years_of_experience,
    split_text_values,
)


class CandidateProfileBuilder:
    def build(self, user: dict) -> dict:
        normalized_profile = user.get("normalized_profile", {}) or {}
        extra = user.get("extraFields", {}) or {}

        summary = (
            normalized_profile.get("unified_profile_summary")
            or user.get("about")
            or user.get("bio")
            or user.get("aboutMe")
            or ""
        )
        title = (
            normalized_profile.get("primary_role")
            or user.get("professional_title")
            or user.get("headline")
            or user.get("currentPosition")
            or ""
        )

        base_skills = (
            (normalized_profile.get("canonical_skills") or [])
            + (user.get("skills") or [])
            + (user.get("tools") or [])
            + (user.get("coreDomains") or [])
            + split_text_values(extra.get("unique_value"))
            + split_text_values(extra.get("domain_expertise"))
            + split_text_values(extra.get("co_founder_expectations"))
            + split_text_values(extra.get("cofounder_expectations"))
        )

        text_blob = "\n".join(
            str(value)
            for value in [
                title,
                summary,
                user.get("resume_text"),
                extra.get("unique_value"),
                extra.get("domain_expertise"),
                extra.get("co_founder_expectations"),
            ]
            if value
        )

        exact_terms = dedupe_terms(
            [normalize_term(term) for term in base_skills if term]
            + extract_known_terms(text_blob)
        )
        domain_terms = dedupe_terms(
            [normalize_term(term) for term in (normalized_profile.get("core_domains") or []) if term]
            + [normalize_term(term) for term in (user.get("coreDomains") or []) if term]
            + [normalize_term(term) for term in (user.get("interests") or []) if term]
            + infer_domain_labels(exact_terms, text_blob)
        )
        role_terms = dedupe_terms(
            infer_roles(title)
            + infer_roles(summary)
            + infer_roles(user.get("resume_text") or "")
        )

        years_experience = parse_years_of_experience(
            normalized_profile.get("total_experience_years"),
            user.get("experience_years"),
            user.get("totalYearsExperience"),
        )

        evidence_count = sum(
            1
            for value in [
                summary,
                user.get("resume_text"),
                normalized_profile.get("canonical_skills"),
                user.get("skills"),
                extra,
            ]
            if value
        )

        return {
            "user_id": user.get("_id"),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", "user"),
            "is_founder": user.get("role", "user") == "founder",
            "title": title,
            "summary": summary,
            "exact_terms": exact_terms,
            "domain_terms": domain_terms,
            "role_terms": role_terms,
            "years_experience": years_experience,
            "founder_fields": extra,
            "skills_display": [
                term for term in dedupe_terms(base_skills)
                if not is_noisy_skill(term)
            ],
            "linkedin": user.get("linkedin") or user.get("linkedinUrl") or "",
            "resume": user.get("resume", ""),
            "bio": user.get("bio") or user.get("about") or "",
            "vector_similarity": float(user.get("vector_similarity", 0) or 0),
            "text_blob": text_blob,
            "ai_depth_terms": [
                term for term in exact_terms
                if term in {"rag", "llms", "openai", "generative ai", "nlp", "machine learning", "deep learning", "vector databases", "pinecone", "chromadb", "fastapi"}
            ],
            "confidence_inputs": {
                "has_resume": bool(user.get("resume_text")),
                "has_normalized_profile": bool(normalized_profile),
                "evidence_count": evidence_count,
                "term_count": len(exact_terms),
                "domain_count": len(domain_terms),
            },
        }
