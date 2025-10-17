# backend/resume_parser.py
import os, re, json
from datetime import datetime
from typing import List, Optional, Dict, Any

# optional imports
try:
    from pdfminer.high_level import extract_text as extract_pdf_text
except Exception:
    extract_pdf_text = None

try:
    from docx import Document
except Exception:
    Document = None

# spaCy for PhraseMatcher
try:
    import spacy
    from spacy.matcher import PhraseMatcher
    nlp = spacy.load("en_core_web_sm")
except Exception:
    nlp = None
    PhraseMatcher = None

# fuzzy fallback
try:
    from rapidfuzz import process, fuzz
    HAS_RAPIDFUZZ = True
except Exception:
    HAS_RAPIDFUZZ = False

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


# ---------- Configurable synonyms map (extendable) ----------
GLOBAL_SKILL_SYNONYMS = {
    "javascript": ["js", "java script"],
    "react": ["react.js", "reactjs", "react js"],
    "tailwindcss": ["tailwind", "tailwind css", "tailwind.css"],
    "pocketbase": ["pocket base", "pocket-base"],
    "firebase": ["google firebase", "firebase realtime", "firebase auth"],
    "git": ["github", "gitlab", "version control"],
    "python": ["py"],
    # design examples
    "figma": ["figma design"],
    "photoshop": ["adobe photoshop", "ps"],
}


# ---------- Helpers ----------
def extract_text_from_file(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    text = ""
    try:
        if ext == ".pdf" and extract_pdf_text:
            text = extract_pdf_text(path) or ""
        elif ext in (".docx", ".doc") and Document:
            doc = Document(path)
            text = "\n".join([p.text for p in doc.paragraphs])
        else:
            with open(path, "rb") as f:
                raw = f.read()
                try:
                    text = raw.decode("utf-8")
                except:
                    text = raw.decode("latin-1", errors="ignore")
    except Exception:
        try:
            with open(path, "rb") as f:
                raw = f.read()
                text = raw.decode("utf-8", errors="ignore")
        except:
            text = ""
    return text or ""


def _normalize(s: str) -> str:
    if not s: return ""
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\.\+\# ]', ' ', s)  # keep dots for react.js etc
    s = re.sub(r'\s+', ' ', s)
    return s


def _compact(s: str) -> str:
    return re.sub(r'[\s\.]+', '', _normalize(s))


def _expand_skill_variants(skill: str, extra_synonyms: Optional[Dict[str, List[str]]] = None):
    s = _normalize(skill)
    variants = [s]
    # global synonyms
    for canon, vals in GLOBAL_SKILL_SYNONYMS.items():
        if canon == s or s in [ _normalize(v) for v in vals ]:
            variants = [canon] + vals
            break
    # extra synonyms override/extend
    if extra_synonyms:
        for canon, vals in extra_synonyms.items():
            canon_n = _normalize(canon)
            if canon_n == s or s in [ _normalize(v) for v in vals ]:
                variants = [canon_n] + [_normalize(v) for v in vals]
                break
    variants = list(dict.fromkeys([_normalize(v) for v in variants if v]))
    return variants


# ---------- Main parser ----------
def parse_resume(path: str,
                 job_skills: Optional[List[str]] = None,
                 extra_synonyms: Optional[Dict[str, List[str]]] = None,
                 debug: bool = False) -> Dict[str, Any]:
    """
    Parse resume and return structured dict.
    - job_skills: list of skills from the job posting to focus extraction.
    - extra_synonyms: optional dict to extend GLOBAL_SKILL_SYNONYMS for this job.
    - debug: include debug helpers and candidates found.
    """
    text = extract_text_from_file(path)
    t = text or ""
    t_norm = _normalize(t)

    # contact
    email_m = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', t)
    phone_m = re.search(r'(\+?\d[\d\-\s]{7,}\d)', t)

    # degrees: heuristics
    degrees = []
    deg_patterns = [r"\b(b\.?tech\b)", r"\b(b\.?des\b)", r"\b(bachelor of [a-z ]+)\b", r"\b(m\.?tech\b)", r"\b(ph\.?d\b)"]
    for p in deg_patterns:
        for m in re.findall(p, t, flags=re.I):
            degrees.append(_normalize(m))

    # experience years heuristic
    years = 0
    for m in re.findall(r'(\d{1,2})\s+years', t.lower()):
        try:
            v = int(m)
            if v > years:
                years = v
        except:
            pass

    # publications heuristic
    pubs = len(re.findall(r'\b(publication|published|journal|conference|doi)\b', t, flags=re.I))

    # Build candidate variants using job_skills + global synonyms
    candidate_variants = set()
    if job_skills:
        for s in job_skills:
            for v in _expand_skill_variants(s, extra_synonyms=extra_synonyms):
                candidate_variants.add(v)
    # include global synonyms keys as possible detects
    for canon, vals in (extra_synonyms or GLOBAL_SKILL_SYNONYMS).items():
        candidate_variants.add(_normalize(canon))
        for vv in vals:
            candidate_variants.add(_normalize(vv))

    # heuristic tokens from entire text
    heuristic_tokens = set(re.findall(r'[A-Za-z0-9\.\+\#]{2,}', t))
    heuristic_norm = {_normalize(tok) for tok in heuristic_tokens if len(tok) > 1}

    found = set()
    debug_found = {"phrase_matches": [], "heuristic_matches": [], "fuzzy_matches": []}

    # Try spaCy PhraseMatcher first for robust phrase detection
    if nlp and PhraseMatcher:
        try:
            matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
            patterns = [nlp.make_doc(var) for var in sorted(candidate_variants) if var and len(var.split()) <= 6]
            if patterns:
                matcher.add("SKILLS", patterns)
                doc = nlp(t)
                matches = matcher(doc)
                for mid, start, end in matches:
                    span = doc[start:end].text
                    found.add(_normalize(span))
                    debug_found["phrase_matches"].append(span)
        except Exception:
            pass

    # substring/compact scanning
    text_compact = re.sub(r'[\s\.]+', '', t_norm)
    for var in candidate_variants:
        if var and (var in t_norm or var.replace(" ", "") in text_compact):
            found.add(var)

    # heuristics: match any heuristic token containing or contained-in candidate variants
    for h in heuristic_norm:
        for var in candidate_variants:
            if var in h or h in var:
                found.add(var)
                debug_found["heuristic_matches"].append(h)

    # fuzzy fallback using rapidfuzz (match job_skills to heuristic tokens)
    if HAS_RAPIDFUZZ and job_skills:
        parsed_list = list(heuristic_norm)
        compact_list = [re.sub(r'[\s\.]+', '', x) for x in parsed_list]
        for sk in job_skills:
            sk_compact = re.sub(r'[\s\.]+', '', _normalize(sk))
            try:
                best = process.extractOne(sk_compact, compact_list, scorer=fuzz.partial_ratio) if compact_list else None
                if best and best[1] >= 80:
                    idx = compact_list.index(best[0])
                    matched = parsed_list[idx]
                    found.add(_normalize(matched))
                    debug_found["fuzzy_matches"].append((sk, matched, best[1]))
            except Exception:
                pass

    # soft keywords
    soft_kw = ["communication","interpersonal","presentation","collaborat","team","client"]
    for kw in soft_kw:
        if kw in t_norm:
            found.add("communication")

    skills = sorted({ _normalize(s) for s in found })

    parsed = {
        "email": email_m.group(0) if email_m else None,
        "phone": phone_m.group(0) if phone_m else None,
        "degrees": degrees,
        "experience_years": years,
        "publications": pubs,
        "skills": skills,
        "raw_text_excerpt": t[:4000]
    }
    if debug:
        parsed["_debug"] = {
            "candidate_variants": sorted(list(candidate_variants))[:300],
            "heuristic_tokens_sample": sorted(list(heuristic_norm))[:200],
            "found_variants": sorted(list(found))[:200],
            "phrase_matches": debug_found.get("phrase_matches", []),
            "heuristic_matches": debug_found.get("heuristic_matches", [])[:200],
            "fuzzy_matches": debug_found.get("fuzzy_matches", [])[:50]
        }
    return parsed
