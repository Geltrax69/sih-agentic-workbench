"""Question-aware selection; cosine scores remain separate from lexical ranking."""
from __future__ import annotations

import math
import re
from collections import Counter
from functools import lru_cache

import snowballstemmer

from app.grounding.confidence import WEAK

_STOP = set("a an the what which how is are was were does do did in of on for to and or with "
            "this that these those it its be by as at from according manuscript paper document "
            "source sources provided use used have has been can would please tell give exact project "
            "specified reported measured recorded mentioned stated described given".split())
_STEMMER = snowballstemmer.stemmer("english")


@lru_cache(maxsize=16384)
def _stem(word: str) -> str:
    return _STEMMER.stemWord(word)


def terms(text: str) -> list[str]:
    result = []
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in _STOP:
            continue
        result.append(_stem(word))
    # Normalize metric vocabulary in ranking only; source text is unchanged.
    if re.search(r"\brequests?\s*/\s*s\b|\brequests? per second\b", text, re.I):
        result.extend([_stem("throughput"), _stem("rate")])
    if re.search(r"\bp(?:50|95|99)\s+ms\b", text, re.I):
        result.append(_stem("latency"))
    return result


def select_evidence(question: str, rows: list[dict], keep: int = 4) -> list[dict]:
    """Fuse vector and BM25 ranks without treating lexical rank as confidence."""
    candidates = [r.copy() for r in rows if r["score"] >= WEAK and not r.get("context_only")]
    if not candidates:
        return []
    query = set(terms(question))
    counts = [Counter(terms(r["content"])) for r in candidates]
    avg = sum(sum(c.values()) for c in counts) / len(counts) or 1
    df = Counter(w for c in counts for w in c)
    lexical = []
    for c in counts:
        size = sum(c.values())
        lexical.append(sum(math.log(1 + (len(counts) - df[w] + .5) / (df[w] + .5))
                           * c[w] * 2.2 / (c[w] + 1.2 * (.25 + .75 * size / avg))
                           for w in query if c[w]))
    vector_order = sorted(range(len(candidates)), key=lambda i: candidates[i]["score"], reverse=True)
    lexical_order = sorted(range(len(candidates)), key=lambda i: lexical[i], reverse=True)
    vr = {i: rank for rank, i in enumerate(vector_order, 1)}
    lr = {i: rank for rank, i in enumerate(lexical_order, 1)}
    for i, row in enumerate(candidates):
        row["lexical_score"] = lexical[i]
        row["selection_score"] = 1 / (20 + vr[i]) + (1 / (20 + lr[i]) if lexical[i] else 0)
    ranked = sorted(candidates, key=lambda r: r["selection_score"], reverse=True)
    selected, pages = [], set()
    for row in ranked:
        # Similar chunks from one page must not occupy all context slots.
        page = (row.get("document_id"), row.get("location"))
        if page[0] is not None and page[1] and page in pages:
            continue
        selected.append(row)
        pages.add(page)
        if len(selected) == keep:
            break
    return selected


def expand_context(selected: list[dict], rows: list[dict], budget: int = 14000) -> list[dict]:
    """Attach adjacent chunks from the same scoped document/page, preserving gaps."""
    result = []
    for hit in selected:
        neighbors = [r for r in rows if r.get("document_id") == hit.get("document_id")
                     and r.get("location") == hit.get("location")
                     and abs(r.get("chunk_index", 0) - hit.get("chunk_index", 0)) <= 4]
        neighbors = sorted(neighbors or [hit], key=lambda r: r.get("chunk_index", 0))
        content = ""
        for row in neighbors:
            addition = row["content"]
            overlap = next((size for size in range(min(len(content), len(addition), 800), 19, -1)
                            if content[-size:] == addition[:size]), 0)
            content += addition[overlap:] if overlap else ("\n\n" if content else "") + addition
        # Preserve paragraphs and labeled table rows, not thousands of visual
        # alignment spaces. This keeps whole page context inside a small model.
        content = re.sub(r"[ \t]{2,}", " ", content)
        if len(content) > budget:
            content = hit["content"]
        if len(content) > budget:
            break
        result.append({**hit, "content": content})
        budget -= len(content)
    return result
