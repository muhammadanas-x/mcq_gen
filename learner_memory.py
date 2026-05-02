"""
Unified learner memory: Pinecone upsert/query for personalization across MCQ + Tutor.

Uses Pinecone Inference embedding model (default: llama-text-embed-v2, 1048 dimensions).
No-op when PINECONE_API_KEY or PINECONE_INDEX_LEARNER is unset.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

# Pinecone embedding model (1048-dim index required in Pinecone console)
DEFAULT_EMBED_MODEL = "llama-text-embed-v2"

_pc = None
_index = None


def normalize_key(text: Optional[str]) -> str:
    """Canonical key for topic / sub_topic matching."""
    if not text:
        return ""
    s = str(text).strip().lower()
    s = re.sub(r"[\u2013\u2014\u2212]", "-", s)  # en dash, em dash, minus → hyphen
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def topic_subtopic_from_strings(topic: str, sub_topic: str) -> Tuple[str, str, str, str]:
    """Returns (topic_display, sub_topic_display, topic_key, sub_topic_key)."""
    td = (topic or "").strip()
    sd = (sub_topic or "").strip()
    return td, sd, normalize_key(td), normalize_key(sd)


def split_tutor_topic(tutor_topic: Optional[str]) -> Tuple[str, str]:
    """Split tutor `topic` like 'calculus – differentiation' into display topic + sub_topic."""
    t = (tutor_topic or "").strip()
    if not t:
        return "", ""
    for sep in [" – ", " - ", "–", "-"]:
        if sep in t:
            parts = t.split(sep, 1)
            return parts[0].strip(), (parts[1].strip() if len(parts) > 1 else parts[0].strip())
    return t, t


def _client():
    global _pc, _index
    if _pc is not None or _index is not None:
        return _pc, _index
    api_key = (os.getenv("PINECONE_API_KEY") or "").strip()
    index_name = (os.getenv("PINECONE_INDEX_LEARNER") or "").strip()
    if not api_key or not index_name:
        return None, None
    try:
        from pinecone import Pinecone

        _pc = Pinecone(api_key=api_key)
        _index = _pc.Index(index_name)
    except Exception:
        _pc, _index = None, None
    return _pc, _index


def is_configured() -> bool:
    pc, idx = _client()
    return pc is not None and idx is not None


def embed_model() -> str:
    return (os.getenv("PINECONE_EMBED_MODEL") or DEFAULT_EMBED_MODEL).strip()


def _embed(text: str, input_type: str) -> List[float]:
    pc, _ = _client()
    if pc is None:
        return []
    model = embed_model()
    result = pc.inference.embed(
        model=model,
        inputs=[text[:8000]],
        parameters={"input_type": input_type, "truncate": "END"},
    )
    return list(result.data[0].values)


def embed_passage(text: str) -> List[float]:
    return _embed(text or "", "passage")


def embed_query(text: str) -> List[float]:
    return _embed(text or "", "query")


def difficulty_hint_from_matches(matches: List[Dict[str, Any]]) -> str:
    """
    Map retrieval hits + metadata to a coarse difficulty hint for MCQ / quiz prompts.
    matches: list of {score, metadata}
    """
    if not matches:
        return "medium"
    top = matches[0]
    score = float(top.get("score") or 0.0)
    meta = top.get("metadata") or {}
    weak = meta.get("weak_concepts") or ""
    last = meta.get("last_score")
    try:
        last_f = float(last) if last is not None and str(last) != "" else None
    except (TypeError, ValueError):
        last_f = None

    weak_nonempty = bool(str(weak).strip()) and str(weak).strip().lower() not in ("none", "[]", "null")

    if weak_nonempty or (last_f is not None and last_f < 55.0):
        return "easy"
    if score > 0.82 and last_f is not None and last_f >= 80.0 and not weak_nonempty:
        return "hard"
    if score > 0.88 and last_f is None and not weak_nonempty:
        return "hard"
    return "medium"


def build_memory_block(learner_context: str, difficulty_hint: str) -> str:
    """Markdown block prepended to chapter input for LangGraph."""
    ctx = (learner_context or "").strip()
    hint = (difficulty_hint or "medium").strip().lower()
    lines = [
        "## Learner memory (internal — do not address the student as 'memory')",
        f"**Difficulty bias for NEW questions:** {hint}",
    ]
    if ctx:
        lines.append("**Prior related activity (summarize in your head; avoid repeating verbatim stems):**")
        lines.append(ctx[:6000])
    lines.append("")
    return "\n".join(lines)


def query_memory_bundle(
    user_id: Optional[str],
    topic_key: str,
    sub_topic_key: str,
    query_text: str,
    top_k: int = 8,
) -> Dict[str, Any]:
    """
    Retrieve prior vectors for same user + canonical topic lane; embed query_text for similarity.
    Returns learner_context, difficulty_hint, memory_hits, top_scores.
    """
    out: Dict[str, Any] = {
        "learner_context": "",
        "difficulty_hint": "medium",
        "memory_hits": 0,
        "top_scores": [],
    }
    uid = (user_id or "").strip()
    if not uid or not topic_key or not is_configured():
        return out
    _, idx = _client()
    if idx is None:
        return out

    qvec = embed_query(query_text or f"{topic_key} {sub_topic_key}")
    if not qvec:
        return out

    flt: Dict[str, Any] = {
        "user_id": {"$eq": uid},
        "topic_key": {"$eq": topic_key},
        "sub_topic_key": {"$eq": sub_topic_key},
    }
    try:
        res = idx.query(vector=qvec, top_k=top_k, filter=flt, include_metadata=True)
    except Exception:
        return out

    matches: List[Dict[str, Any]] = []
    for m in getattr(res, "matches", None) or []:
        md = dict(m.metadata or {})
        matches.append({"score": float(m.score or 0.0), "metadata": md})

    out["memory_hits"] = len(matches)
    out["top_scores"] = [round(x["score"], 4) for x in matches[:5]]

    snippets: List[str] = []
    for i, m in enumerate(matches[:6], start=1):
        md = m["metadata"]
        src = md.get("source", "")
        pr = str(md.get("prompt", ""))[:400]
        ex = str(md.get("excerpt", ""))[:300]
        snippets.append(f"{i}. [{src}] {pr}\n   excerpt: {ex}")

    out["learner_context"] = "\n".join(snippets).strip()
    out["difficulty_hint"] = difficulty_hint_from_matches(matches)
    return out


def upsert_memory_record(
    *,
    user_id: Optional[str],
    topic: str,
    sub_topic: str,
    prompt: str,
    source: str,
    session_id: str,
    excerpt: str = "",
    weak_concepts: Optional[List[str]] = None,
    last_score: Optional[float] = None,
) -> Optional[str]:
    """Upsert one vector; returns vector id or None if skipped/failed."""
    uid = (user_id or "").strip()
    if not uid or not is_configured():
        return None
    _, idx = _client()
    if idx is None:
        return None

    td, sd, tk, sk = topic_subtopic_from_strings(topic, sub_topic)
    weak_str = ""
    if weak_concepts:
        weak_str = json.dumps(weak_concepts[:20], ensure_ascii=False)

    text = f"[{td}] > [{sd}] | prompt: {prompt[:2000]} | source: {source} | weak: {weak_str} | excerpt: {(excerpt or '')[:1500]}"

    vec = embed_passage(text)
    if not vec:
        return None

    vid = f"{source}_{session_id}_{uuid.uuid4().hex[:12]}"
    meta: Dict[str, Any] = {
        "user_id": uid,
        "topic": td[:500],
        "sub_topic": sd[:500],
        "topic_key": tk[:256],
        "sub_topic_key": sk[:256],
        "prompt": prompt[:3500],
        "source": source[:64],
        "session_id": session_id[:64],
        "excerpt": (excerpt or "")[:3500],
        "weak_concepts": weak_str[:3500],
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    if last_score is not None:
        try:
            meta["last_score"] = float(last_score)
        except (TypeError, ValueError):
            pass

    try:
        idx.upsert(vectors=[{"id": vid, "values": vec, "metadata": meta}])
        return vid
    except Exception:
        return None
