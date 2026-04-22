import re


ALIASES = {
    "rag pipelines": "rag",
    "retrieval augmented generation": "rag",
    "retrieval-augmented generation": "rag",
    "vector db": "vector databases",
    "vector database": "vector databases",
    "vector database systems": "vector databases",
    "vector store": "vector databases",
    "llm": "llms",
    "large language model": "llms",
    "large language models": "llms",
    "fast api": "fastapi",
    "react.js": "react",
    "react js": "react",
    "node js": "node.js",
    "nodejs": "node.js",
    "open ai": "openai",
    "openai gpt": "openai",
    "openai gpt api": "openai",
    "openai gpt apis": "openai",
    "natural language processing": "nlp",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "cromadb": "chromadb",
    "sql databases": "sql",
    "mysql databases": "mysql",
}


KEYWORD_WEIGHTS = {
    # All skills weighted equally — the founder decides what matters by listing
    # it as a requirement; the system should not second-guess that with
    # arbitrary multipliers. Rarity is already captured by the separate
    # rare_keyword_score subscore.
}


NOISY_SKILL_TERMS = {
    "share",
    "excited",
    "collaborative",
    "positive environment",
    "attention to detail",
    "teamwork",
    "communication",
    "problem solving",
    "analytical thinking",
    "working under pressure",
    "research",
    "presentation",
    "effective communication",
    "more technical and business analyst skills",
    "development and designing role",
}


KNOWN_TERM_PATTERNS = {
    r"\brag\b|\bretrieval[- ]augmented generation\b": "rag",
    r"\bvector db\b|\bvector store\b|\bvector database\b|\bvector databases\b": "vector databases",
    r"\bpinecone\b": "pinecone",
    r"\bchromadb\b|\bcromadb\b": "chromadb",
    r"\bllm\b|\bllms\b|\blarge language model": "llms",
    r"\bfastapi\b|\bfast api\b": "fastapi",
    r"\breact\b|\breact\.js\b": "react",
    r"\bnode\.?js\b|\bnode js\b": "node.js",
    r"\bmongodb\b": "mongodb",
    r"\bopen ai\b|\bopenai\b": "openai",
    r"\bgenerative ai\b|\bgenai\b": "generative ai",
    r"\bnlp\b|\bnatural language processing\b": "nlp",
    r"\bmachine learning\b": "machine learning",
    r"\bdeep learning\b": "deep learning",
    r"\bdata engineering\b": "data engineering",
    r"\bcloud computing\b|\bcloud architecture\b|\bcloud engineering\b": "cloud computing",
    r"\baws\b|\bamazon web services\b": "aws",
    r"\bpython\b": "python",
    r"\bsql\b": "sql",
    r"\bmysql\b": "mysql",
    r"\bapi development\b|\bapis\b": "api development",
    r"\bui\/ux\b|\bux\b|\buser experience\b": "ui/ux",
    r"\bbusiness strategy\b": "business strategy",
    r"\bcomputer vision\b": "computer vision",
    r"\bstreamlit\b": "streamlit",
    r"\btableau\b": "tableau",
    r"\bpower bi\b": "power bi",
    r"\bvertex ai\b": "vertex ai",
    r"\bgemini\b": "gemini",
}


ROLE_PATTERNS = {
    r"\bfull[ -]?stack\b": "full stack engineer",
    r"\bfrontend\b|\bfront end\b": "frontend engineer",
    r"\bbackend\b|\bback end\b": "backend engineer",
    r"\bmachine learning\b|\bml engineer\b": "ml engineer",
    r"\bdata scientist\b": "data scientist",
    r"\bdata engineer\b": "data engineer",
    r"\bai engineer\b": "ai engineer",
    r"\bsoftware engineer\b|\bsde\b|\bdeveloper\b": "software engineer",
    r"\bcloud engineer\b": "cloud engineer",
    r"\bproduct manager\b": "product manager",
    r"\bbusiness analyst\b": "business analyst",
}


DOMAIN_HINTS = {
    "ai/ml": {"rag", "llms", "openai", "nlp", "machine learning", "deep learning", "computer vision", "generative ai"},
    "full-stack": {"react", "node.js", "fastapi", "api development", "mongodb", "sql", "ui/ux"},
    "data": {"data engineering", "sql", "tableau", "power bi", "vector databases", "pinecone", "chromadb"},
    "cloud": {"aws", "cloud computing", "mongodb"},
}


def normalize_term(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9+#./-]+", " ", str(value or "").lower()).strip()
    return ALIASES.get(normalized, normalized)


def dedupe_terms(values) -> list:
    seen = set()
    out = []
    for value in values or []:
        cleaned = re.sub(r"\s+", " ", str(value or "")).strip(" ,")
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(cleaned)
    return out


def split_text_values(value) -> list:
    if not value:
        return []
    if isinstance(value, list):
        out = []
        for item in value:
            out.extend(split_text_values(item))
        return out
    if isinstance(value, dict):
        out = []
        for item in value.values():
            out.extend(split_text_values(item))
        return out
    return [part.strip() for part in re.split(r"[\n,;/|]+", str(value)) if part.strip()]


def tokenize(value: str) -> set:
    return {token for token in normalize_term(value).split() if len(token) > 1}


def extract_known_terms(text: str) -> list:
    lowered = str(text or "").lower()
    found = []
    for pattern, canonical in KNOWN_TERM_PATTERNS.items():
        if re.search(pattern, lowered):
            found.append(canonical)
    return dedupe_terms(found)


def infer_roles(text: str) -> list:
    lowered = str(text or "").lower()
    roles = []
    for pattern, role in ROLE_PATTERNS.items():
        if re.search(pattern, lowered):
            roles.append(role)
    return dedupe_terms(roles)


def infer_domain_labels(terms: list, text: str = "") -> list:
    normalized_terms = {normalize_term(term) for term in terms or [] if term}
    normalized_terms.update(extract_known_terms(text))
    labels = []
    for label, hints in DOMAIN_HINTS.items():
        if normalized_terms & hints:
            labels.append(label)
    return dedupe_terms(labels)


def parse_years_of_experience(*values) -> int:
    for value in values:
        if value in [None, "", []]:
            continue
        if isinstance(value, (int, float)):
            return int(value)
        match = re.search(r"\d+", str(value))
        if match:
            return int(match.group())
    return 0


def keyword_weight(term: str) -> float:
    return 1.0


def is_noisy_skill(term: str) -> bool:
    normalized = normalize_term(term)
    if normalized in NOISY_SKILL_TERMS:
        return True
    if len(normalized) <= 2:
        return True
    if normalized in {"sql", "aws", "nlp", "rag", "llms", "ui/ux"}:
        return False
    if normalized.count(" ") >= 5:
        return True
    return False
