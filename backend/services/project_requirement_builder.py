import re

from models.user import User
from services.matching_taxonomy import (
    dedupe_terms,
    extract_known_terms,
    infer_domain_labels,
    infer_roles,
    normalize_term,
    parse_years_of_experience,
)


class ProjectRequirementBuilder:
    def build(self, project: dict) -> dict:
        title = project.get("title", "")
        description = project.get("description", "")
        required_skills = project.get("required_skills", []) or []
        project_text = "\n".join([title, description, ", ".join(required_skills)])

        explicit_terms = [normalize_term(term) for term in required_skills if term]
        discovered_terms = extract_known_terms(project_text)
        exact_terms = dedupe_terms(explicit_terms + discovered_terms)
        role_terms = dedupe_terms(infer_roles(project_text))
        domain_terms = dedupe_terms(
            infer_domain_labels(exact_terms, project_text)
            + [normalize_term(term) for term in required_skills if term]
        )

        minimum_years = self._parse_minimum_years(description)
        founder_preferences = self._load_founder_preferences(project.get("founder_id"))
        rare_terms = [
            term for term in exact_terms
            if term in {"rag", "vector databases", "pinecone", "chromadb", "llms", "openai", "fastapi", "react", "node.js", "mongodb"}
        ]
        critical_terms = dedupe_terms(rare_terms + [term for term in exact_terms if term in {"python", "machine learning", "deep learning", "nlp", "aws"}])

        return {
            "title": title,
            "description": description,
            "exact_terms": exact_terms,
            "rare_terms": rare_terms,
            "critical_terms": critical_terms,
            "role_terms": role_terms,
            "domain_terms": domain_terms,
            "minimum_years": minimum_years,
            "founder_preferences": founder_preferences,
            "text_blob": project_text,
        }

    def _parse_minimum_years(self, description: str) -> int:
        lowered = str(description or "").lower()
        match = re.search(r"(\d+)\s*\+?\s*(?:years|yrs)", lowered)
        if match:
            return int(match.group(1))
        return parse_years_of_experience(description)

    def _load_founder_preferences(self, founder_id: str) -> dict:
        founder = User.find_by_id(founder_id) if founder_id else None
        if not founder:
            return {}
        extra = founder.get("extraFields", {}) or {}
        return {
            "industry_preferences": extra.get("industry_preferences") or extra.get("industry_preference"),
            "technical_orientation": extra.get("technical_vs_business_orientation") or extra.get("technical_orientation"),
            "leadership_style": extra.get("leadership_style"),
            "risk_tolerance": extra.get("risk_tolerance"),
            "co_founder_expectations": extra.get("co_founder_expectations") or extra.get("cofounder_expectations"),
        }
