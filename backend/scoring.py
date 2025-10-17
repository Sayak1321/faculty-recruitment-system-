# backend/scoring.py
def compute_score(parsed_resume, criteria, match_info):
    """
    Returns a numeric score (0-100).
    Weights:
      - Required skills coverage: 50%
      - Degree match strength: 15%
      - Experience (relative to min): 15%
      - Optional skills bonus: 10%
      - Publications bonus: 10%
    """
    score = 0.0
    # Required skills
    required = criteria.get("required_skills", []) or []
    if required:
        matched = match_info.get("matched_required", {})
        req_pct = min(1.0, len(matched) / len(required))
    else:
        req_pct = 1.0
    score += req_pct * 50.0

    # Degree match strength (if matched score given)
    deg = match_info.get("degree", {})
    deg_score = deg.get("score", 0) or 0
    deg_pct = min(1.0, deg_score / 100.0)
    score += deg_pct * 15.0

    # Experience: more than min gives linear bonus up to 2x min
    min_exp = criteria.get("min_experience", 0)
    found_exp = parsed_resume.get("experience_years", 0)
    if min_exp <= 0:
        exp_pct = 1.0
    else:
        exp_pct = min(1.0, found_exp / (min_exp * 2))  # cap
    score += exp_pct * 15.0

    # Optional skills bonus
    opt_count = match_info.get("optional_bonus_count", 0)
    # give each optional match 10% of the optional bucket
    # optional bucket = 10
    # approximate: min(opt_count, len(optional_skills)) / (len(optional_skills) or 1)
    total_opt = len(criteria.get("optional_skills", []) or [])
    if total_opt:
        opt_pct = min(1.0, opt_count / total_opt)
    else:
        opt_pct = min(1.0, opt_count / (opt_count + 1))
    score += opt_pct * 10.0

    # Publications bonus (simple)
    min_pubs = criteria.get("min_publications", 0)
    pubs_found = parsed_resume.get("publications", 0)
    if min_pubs <= 0:
        pub_pct = min(1.0, pubs_found / 1.0)  # any publications gives some bonus
    else:
        pub_pct = min(1.0, pubs_found / (min_pubs * 1.0))
    score += min(10.0, pub_pct * 10.0)

    # final clamp
    final = max(0.0, min(100.0, round(score, 2)))
    return final
