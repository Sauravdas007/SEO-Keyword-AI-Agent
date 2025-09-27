"""
agent.generator
Refactored SEO Keyword Research Agent core logic.

Public functions:
- generate_candidates(seed: str, n: int = 50, use_cache: bool = True) -> list[dict]

Design:
- Candidate generation (templates + modifiers + question forms)
- Metrics fetching (pluggable: mock by default; replace fetch_metrics_for_keywords with API-backed version)
- Scoring: favors high volume and low competition
- Simple in-memory cache to reduce repeated computation while demoing
"""

from __future__ import annotations
import hashlib, random, math, time
from typing import List, Dict, Callable

# ---- Configuration ----
DEFAULT_MODIFIERS = [
    "best", "top", "cheap", "affordable", "2025", "guide", "how to", "tips",
    "what is", "benefits", "advantages", "vs", "near me", "jobs", "internships",
    "remote", "online", "course", "program", "schools", "scholarship",
    "opportunities", "apply", "requirements", "salary", "scope", "career", "for students",
    "for beginners", "examples", "case study", "statistics", "trends", "market", "global"
]

QUESTION_WORDS = ["how", "what", "why", "where", "when"]

_CACHE = {}  # simple in-process cache: {(seed,n): (timestamp, results)}

CACHE_TTL = 300  # seconds


# ---- Utilities ----
def _deterministic_random(seed_text: str) -> random.Random:
    h = hashlib.md5(seed_text.encode("utf-8")).hexdigest()
    seed = int(h[:8], 16)
    return random.Random(seed)


# ---- Candidate generation ----
def generate_long_tail(seed: str, n: int = 120, modifiers: List[str] = None) -> List[str]:
    """
    Generate a diverse set of keyword candidates based on the seed.
    Return up to n unique candidate phrases.
    """
    seed = seed.strip()
    if not seed:
        return []
    modifiers = modifiers or DEFAULT_MODIFIERS
    candidates = set()
    rnd = _deterministic_random(seed + "_gen")
    # combine modifiers in various positions
    for mod in modifiers:
        if len(candidates) >= n:
            break
        if rnd.random() < 0.95:
            candidates.add(f"{mod} {seed}")
        if rnd.random() < 0.7:
            candidates.add(f"{seed} {mod}")
        if rnd.random() < 0.35:
            candidates.add(f"{mod} {seed} {rnd.choice(['2025','guide','for students','near me'])}")
    # question forms (intent-focused)
    for q in QUESTION_WORDS:
        if len(candidates) >= n:
            break
        candidates.add(f"{q} {seed}")
        candidates.add(f"{q} {seed} {rnd.choice(['benefits','requirements','how to apply'])}")
    # geo / audience variations
    geos = ["global", "india", "us", "uk", "canada", "europe", "asia"]
    for g in geos:
        if len(candidates) >= n:
            break
        candidates.add(f"{seed} {g}")
    # pad with adjective combinations if still short
    adjectives = ["best", "top", "cheap", "affordable", "legit"]
    i = 0
    while len(candidates) < n and i < 500:
        a = rnd.choice(adjectives)
        candidates.add(f"{a} {seed} {rnd.choice(['guide','program','internships'])}")
        i += 1
    return list(candidates)[:n]


# ---- Mock metrics (deterministic) ----
def mock_metrics_for_keyword(keyword: str) -> Dict[str, float]:
    """
    Deterministic pseudo-metrics so demos are reproducible.
    Returns: {"est_volume": int, "est_competition": float (0..1)}
    """
    rnd = _deterministic_random("metrics_" + keyword)
    tokens = keyword.split()
    base = max(3, 300 - 10 * len(tokens))
    bump = sum([5 for w in ["best", "top", "jobs", "internships", "guide", "2025"] if w in keyword.lower()])
    est_volume = int(base + bump * rnd.uniform(1, 5) + (rnd.random() * 200))
    comp_base = 0.55 - 0.05 * len(tokens)
    if any(w in keyword.lower() for w in ["how", "what", "why"]):
        comp_base -= 0.12
    if "global" in keyword.lower():
        comp_base += 0.08
    est_competition = min(0.99, max(0.01, comp_base + rnd.uniform(-0.12, 0.12)))
    return {"est_volume": est_volume, "est_competition": round(est_competition, 3)}


def fetch_metrics_for_keywords(keywords: List[str], fetcher: Callable = None) -> Dict[str, Dict]:
    """
    Fetch metrics for a list of keywords.
    - By default uses deterministic mock metrics above.
    - You may pass a custom `fetcher` function that accepts a list of keywords and returns a dict.
    """
    if fetcher is None:
        fetcher = lambda kws: {k: mock_metrics_for_keyword(k) for k in kws}
    return fetcher(keywords)


# ---- Scoring ----
def score_keyword(metrics: Dict[str, float]) -> float:
    """
    Composite score where higher is better for targeting:
      score = vol_norm * (1 - comp)^p
    We square (p=2) the (1-comp) term to amplify the effect of low competition.
    """
    vol = metrics["est_volume"]
    comp = metrics["est_competition"]
    vol_norm = math.log1p(vol) / math.log1p(1000)
    score = vol_norm * ((1 - comp) ** 2)
    return score


# ---- Public API ----
def generate_candidates(seed: str, n: int = 50, use_cache: bool = True, fetcher: Callable = None) -> List[Dict]:
    """
    Generate top-n candidate keywords for the given seed.
    Returns a list of dicts: {"keyword","est_volume","est_competition","score"}
    """
    key = (seed, n)
    now = time.time()
    if use_cache and key in _CACHE:
        ts, results = _CACHE[key]
        if now - ts < CACHE_TTL:
            return results

    # generate a larger pool, then enrich & rank
    pool = generate_long_tail(seed, n * 3)
    metrics = fetch_metrics_for_keywords(pool, fetcher=fetcher)
    enriched = []
    for k in pool:
        m = metrics.get(k, {"est_volume": 0, "est_competition": 0.99})
        s = score_keyword(m)
        enriched.append({
            "keyword": k,
            "est_volume": int(m["est_volume"]),
            "est_competition": float(m["est_competition"]),
            "score": round(s, 6)
        })
    # sort: primary by score desc, secondary by low competition, tertiary by volume desc
    enriched_sorted = sorted(enriched, key=lambda x: (-x["score"], x["est_competition"], -x["est_volume"]))
    top_n = enriched_sorted[:n]
    _CACHE[key] = (now, top_n)
    return top_n
