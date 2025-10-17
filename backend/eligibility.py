# backend/eligibility.py
import re
from rapidfuzz import process, fuzz

# Conservative degree equivalence by level (we do NOT equate Bachelor -> Master)
DEGREE_LEVELS = {
    "phd": 3,
    "doctor": 3,
    "m.tech": 2, "mtech": 2, "ms": 2, "m.sc": 2, "master": 2, "me": 2,
    "b.tech": 1, "btech": 1, "b.e": 1, "be": 1, "b.sc": 1, "b.des": 1, "bdes": 1, "bachelor": 1
}

# Degree subject equivalences (used only if level requirement satisfied)
DEGREE_EQUIVALENCE = {
    # canonical : list of subject variants
    "mechanical": ["mechanical engineering", "mechanical"],
    "computer": ["computer science", "computer engineering", "cse", "computer science engineering"],
    "design": ["design", "b.des", "b des", "bdes"],
    "electrical": ["electrical", "electrical engineering", "eee"],
    # add more domain mappings as required
}

# Skill synonyms (canonical -> variants)
SKILL_SYNONYMS = {
    "javascript": ["js", "java script"],
    "react": ["react.js", "reactjs", "react js"],
    "tailwindcss": ["tailwind", "tailwind css", "tailwind.css"],
    "pocketbase": ["pocket base"],
    "firebase": ["google firebase"],
    "git": ["github", "gitlab", "version control"],
    "python": ["py"]
}

# Minimums/thresholds
FUZZY_THRESHOLD = 82           # Slightly stricter fuzzy threshold
MIN_TOKEN_LEN_FOR_FUZZY = 4   # tokens shorter than this require exact/phrase match
BLACKLIST_TOKENS = {"icse","cbse","class","school","all","grade","section","board","roll"}  # obvious non-skill tokens

def _normalize_text(s):
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r'[^a-z0-9\.\+\# ]', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def _compact(s):
    return re.sub(r'[\s\.]+', '', _normalize_text(s))

def _get_degree_level_from_string(s):
    """Return numeric level (0 none, 1 bachelor, 2 master, 3 phd)"""
    if not s:
        return 0
    t = _normalize_text(s)
    for key, lvl in DEGREE_LEVELS.items():
        if re.search(r'\b' + re.escape(key) + r'\b', t):
            return lvl
    # heuristics: if contains 'm' and 'tech' assume master
    if re.search(r'\b(m(\.?)tech|master|ms|m.sc|m\.?e)\b', t):
        return 2
    if re.search(r'\b(b(\.?)tech|btech|bachelor|b\.?des|bdes|b\.?sc)\b', t):
        return 1
    if re.search(r'\b(ph\.?|phd|doctor)\b', t):
        return 3
    return 0

def _subject_matches(req_subject, parsed_degrees_list):
    """
    Conservative subject matching for degrees.
    req_subject: string (e.g. 'M.tech Mechanical Engineering')
    parsed_degrees_list: list of parsed degree phrases from the resume
    Returns: (matched_bool, matched_phrase, score, method)
    """
    req_norm = _normalize_text(req_subject or "")
    # try to extract required subject token (e.g., 'mechanical engineering' -> 'mechanical')
    # look for known equivalences first
    req_subtokens = []
    for canon, variants in DEGREE_EQUIVALENCE.items():
        for v in [canon] + variants:
            if v in req_norm:
                req_subtokens.append(canon)
                break
    # if no mapping found, try to take last words as subject
    if not req_subtokens:
        # attempt to pick noun phrase after level tokens
        # example: "m.tech mechanical engineering" -> pick "mechanical"
        parts = req_norm.split()
        # pick words not in level tokens
        parts = [p for p in parts if p not in {"m","mtech","b","btech","b.tech","master","bachelor","tech","m."}]
        if parts:
            # take first substantive token
            req_subtokens.append(parts[0])

    parsed_norm = [_normalize_text(d) for d in (parsed_degrees_list or [])]
    # exact/substring match first
    for d_orig, d_norm in zip(parsed_degrees_list or [], parsed_norm):
        for req_sub in req_subtokens:
            if req_sub and (req_sub in d_norm or d_norm in req_sub):
                return True, d_orig, 100.0, "exact"
    # fuzzy match if parsed degrees exist and required subject token not too short
    if parsed_norm and req_subtokens:
        for req_sub in req_subtokens:
            if len(req_sub) < 3:
                continue
            # use partial ratio
            best = process.extractOne(req_sub, parsed_norm, scorer=fuzz.partial_ratio)
            if best and best[1] >= FUZZY_THRESHOLD:
                # find the original phrase
                for d_orig, d_norm in zip(parsed_degrees_list or [], parsed_norm):
                    if d_norm == best[0]:
                        return True, d_orig, float(best[1]), "fuzzy"
    return False, None, 0.0, "none"

def _variants_for_skill(skill):
    """List of normalized variants for a required skill (canonical + synonyms)."""
    k = _normalize_text(skill)
    variants = [k]
    if k in SKILL_SYNONYMS:
        variants += SKILL_SYNONYMS[k]
    # compact and normalized unique
    seen = []
    for v in variants:
        nv = _normalize_text(v)
        if nv not in seen:
            seen.append(nv)
    return seen

def _is_blacklisted(token):
    if not token:
        return False
    t = _normalize_text(token)
    return any(t == b or b in t for b in BLACKLIST_TOKENS)

def _fuzzy_match_skill(variants, parsed_skills):
    """
    Return matched_token, score (0-100) or (None,0).
    Variants: list of normalized variant strings for required skill.
    parsed_skills: list of normalized skill tokens extracted from resume.
    """
    parsed = parsed_skills or []
    parsed_compact = [_compact(p) for p in parsed]

    # exact/compact match first
    for v in variants:
        v_comp = _compact(v)
        if v_comp in parsed_compact:
            return v_comp, 100.0, "exact"

    # try fuzzy only if variant length sufficient (> min)
    for v in variants:
        v_clean = re.sub(r'[\s\.]+', '', v)
        if len(v_clean) < MIN_TOKEN_LEN_FOR_FUZZY:
            continue
        # attempt fuzzy against parsed_compact
        try:
            match = process.extractOne(v_clean, parsed_compact, scorer=fuzz.partial_ratio)
        except Exception:
            match = None
        if match and match[1] >= FUZZY_THRESHOLD:
            return match[0], float(match[1]), "fuzzy"

    return None, 0.0, "none"

def check_eligibility(parsed_resume, criteria, debug=False):
    """
    parsed_resume: dict from resume_parser.parse_resume
    criteria: dict with min_experience, min_publications, required_degree, required_skills, optional_skills
    Returns: eligible(bool), reasons(list), match_info(dict)
    """
    reasons = []
    eligible = True
    match_info = {
        "degree": {},
        "matched_required": {},
        "missing_required": [],
        "matched_optional": {},
        "optional_bonus_count": 0
    }

    # Experience check
    min_exp = criteria.get("min_experience", 0) or 0
    found_exp = parsed_resume.get("experience_years", 0) or 0
    if found_exp < min_exp:
        eligible = False
        reasons.append(f"Experience < {min_exp} years")
    match_info["experience"] = {"required": min_exp, "found": found_exp}

    # Publications
    min_pubs = criteria.get("min_publications", 0) or 0
    found_pubs = parsed_resume.get("publications", 0) or 0
    if found_pubs < min_pubs:
        eligible = False
        reasons.append(f"Publications < {min_pubs}")
    match_info["publications"] = {"required": min_pubs, "found": found_pubs}

    # Degree: enforce level before subject
    req_deg = criteria.get("required_degree")
    deg_required_level = _get_degree_level_from_string(req_deg)
    parsed_degrees = parsed_resume.get("degrees", []) or []
    parsed_levels = [_get_degree_level_from_string(d) for d in parsed_degrees]
    # If no req level explicit, require only subject match
    if deg_required_level == 0:
        # only subject match
        deg_matched, deg_phrase, deg_score, deg_method = _subject_matches(req_deg or "", parsed_degrees)
        match_info["degree"] = {"required": req_deg, "matched": deg_matched, "matched_with": deg_phrase, "score": deg_score, "method": deg_method}
        if not deg_matched:
            eligible = False
            reasons.append(f"Missing required degree: {req_deg}")
    else:
        # require candidate to have at least the required level
        has_level = any(lvl >= deg_required_level for lvl in parsed_levels)
        if not has_level:
            eligible = False
            reasons.append(f"Required degree level not met: {req_deg} (need level {deg_required_level})")
            # still attempt subject fuzzy match for debug
            deg_matched, deg_phrase, deg_score, deg_method = _subject_matches(req_deg or "", parsed_degrees)
            match_info["degree"] = {"required": req_deg, "matched": False, "matched_with": deg_phrase, "score": deg_score, "method": deg_method}
        else:
            # if level satisfied, require subject match (conservative)
            deg_matched, deg_phrase, deg_score, deg_method = _subject_matches(req_deg or "", parsed_degrees)
            match_info["degree"] = {"required": req_deg, "matched": deg_matched, "matched_with": deg_phrase, "score": deg_score, "method": deg_method}
            if not deg_matched:
                eligible = False
                reasons.append(f"Degree level OK but subject mismatch for required degree: {req_deg}")

    # Skill matching
    parsed_skills = parsed_resume.get("skills", []) or []
    # normalize parsed skills
    parsed_skills_norm = [_normalize_text(s) for s in parsed_skills]

    required_skills = criteria.get("required_skills", []) or []
    optional_skills = criteria.get("optional_skills", []) or []

    for rs in required_skills:
        variants = _variants_for_skill(rs)
        # disallow matching if rs itself is blacklisted or too short? handle normally but variants will protect
        matched_token, score, method = _fuzzy_match_skill(variants, parsed_skills_norm)
        # filter out blacklisted results or suspicious short matches
        if matched_token:
            if _is_blacklisted(matched_token):
                matched_token = None
                score = 0.0
                method = "blacklisted"
            else:
                # ensure token length reasonable for fuzzy matches
                if method == "fuzzy" and len(matched_token) < MIN_TOKEN_LEN_FOR_FUZZY:
                    matched_token = None
                    score = 0.0
                    method = "too_short"
        if score >= FUZZY_THRESHOLD or (method == "exact" and score >= 60):
            match_info["matched_required"][rs] = {"matched_with": matched_token, "score": float(score), "method": method}
        else:
            # last-ditch loose substring check but only if not blacklisted and reasonable
            r_comp = _compact(rs)
            found_loose = False
            for p in [ _compact(x) for x in parsed_skills_norm ]:
                if p and (r_comp in p or p in r_comp):
                    if not _is_blacklisted(p) and len(p) >= 3:
                        match_info["matched_required"][rs] = {"matched_with": p, "score": 55.0, "method":"loose_substr"}
                        found_loose = True
                        break
            if not found_loose:
                match_info["missing_required"].append(rs)
                eligible = False
                reasons.append(f"Missing required skill: {rs}")

    opt_count = 0
    for osk in optional_skills:
        variants = _variants_for_skill(osk)
        matched_token, score, method = _fuzzy_match_skill(variants, parsed_skills_norm)
        if matched_token and _is_blacklisted(matched_token):
            matched_token = None
            score = 0.0
        if score >= FUZZY_THRESHOLD or (method == "exact" and score >= 60):
            match_info["matched_optional"][osk] = {"matched_with": matched_token, "score": float(score), "method": method}
            opt_count += 1
        else:
            # loose substring
            r_comp = _compact(osk)
            for p in [ _compact(x) for x in parsed_skills_norm ]:
                if p and (r_comp in p or p in r_comp) and not _is_blacklisted(p):
                    match_info["matched_optional"][osk] = {"matched_with": p, "score": 60.0, "method": "loose_substr"}
                    opt_count += 1
                    break

    match_info["optional_bonus_count"] = opt_count

    if debug:
        match_info["debug_parsed_skills"] = parsed_skills
        match_info["debug_parsed_degrees"] = parsed_degrees

    return eligible, reasons, match_info
