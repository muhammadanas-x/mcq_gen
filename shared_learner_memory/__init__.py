"""
Shared learner memory: Pinecone upsert/query for MCQ + Tutor (single source of truth).

Uses Pinecone Inference embedding model (default: llama-text-embed-v2, 1048 dimensions).
No-op when PINECONE_API_KEY or PINECONE_INDEX_LEARNER is unset.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_EMBED_MODEL = "llama-text-embed-v2"
DEFAULT_RAG_MIN_SCORE = 0.1

_pc = None
_index = None


def normalize_key(text: Optional[str]) -> str:
    """Canonical key for topic / sub_topic matching."""
    if not text:
        return ""
    s = str(text).strip().lower()
    s = re.sub(r"[\u2013\u2014\u2212]", "-", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def topic_subtopic_from_strings(topic: str, sub_topic: str) -> Tuple[str, str, str, str]:
    """Returns (topic_display, sub_topic_display, topic_key, sub_topic_key)."""
    td = (topic or "").strip()
    sd = (sub_topic or "").strip()
    return td, sd, normalize_key(td), normalize_key(sd)


def memory_lane_embed_text(topic_key: str, sub_topic_key: str, user_id: str = "") -> str:
    """Text embedded for learner-memory queries: user + topic lane (personalized)."""
    tk = (topic_key or "").strip()
    sk = (sub_topic_key or "").strip()
    uk = normalize_key(user_id or "")
    if uk:
        return f"user:{uk} | [{tk}] > [{sk}]"
    return f"[{tk}] > [{sk}]"


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


def weak_fragments_from_metadata(meta: Dict[str, Any]) -> List[str]:
    raw = meta.get("weak_concepts")
    out: List[str] = []
    if raw is None:
        return out
    s = str(raw).strip()
    if not s or s.lower() in ("none", "null", "[]"):
        return out
    try:
        parsed = json.loads(s)
        if isinstance(parsed, list):
            for x in parsed:
                t = " ".join(str(x).split()).strip()
                if t:
                    out.append(t)
            return out[:30]
        if isinstance(parsed, dict):
            for v in parsed.values():
                t = " ".join(str(v).split()).strip()
                if t:
                    out.append(t)
            return out[:30]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    if s:
        out.append(s[:2000])
    return out


def _json_list_or_empty(raw: Any, max_items: int = 20) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        vals = raw
    else:
        s = str(raw).strip()
        if not s:
            return []
        try:
            vals = json.loads(s)
        except (json.JSONDecodeError, TypeError, ValueError):
            return []
    if not isinstance(vals, list):
        return []
    out: List[str] = []
    for item in vals[:max_items]:
        text = " ".join(str(item).split()).strip()
        if text:
            out.append(text)
    return out


def _summary_snippet_from_metadata(meta: Dict[str, Any]) -> str:
    summary = " ".join(str(meta.get("weak_summary") or "").split()).strip()
    if summary:
        return summary[:420]
    return ""


def compose_learner_prefix_for_generation(bundle: Dict[str, Any]) -> str:
    parts: List[str] = []
    wf = (bundle.get("weak_focus_markdown") or "").strip()
    if wf:
        parts.append(wf)
    blk = build_memory_block(
        bundle.get("learner_context") or "",
        bundle.get("difficulty_hint") or "medium",
    ).strip()
    if blk:
        parts.append(blk)
    return "\n\n".join(parts).strip()


def _tier_min_score(base: float, env_key: str, fallback: float) -> float:
    raw = (os.getenv(env_key) or "").strip()
    if raw:
        try:
            return max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            pass
    return max(0.0, min(1.0, fallback if fallback is not None else base))


def _query_tier_matches(
    idx: Any,
    qvec: List[float],
    top_k: int,
    flt: Dict[str, Any],
) -> List[Dict[str, Any]]:
    try:
        res = idx.query(vector=qvec, top_k=top_k, filter=flt, include_metadata=True)
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    for m in getattr(res, "matches", None) or []:
        md = dict(m.metadata or {})
        out.append({"score": float(m.score or 0.0), "metadata": md})
    return out


def _match_dedupe_key(match: Dict[str, Any]) -> str:
    md = match.get("metadata") or {}
    session_id = str(md.get("session_id") or "")
    source = str(md.get("source") or "")
    excerpt = str(md.get("excerpt") or "")[:260]
    prompt = str(md.get("prompt") or "")[:120]
    created_at = str(md.get("created_at") or "")
    weak = str(md.get("weak_concepts") or "")[:160]
    return "|".join([session_id, source, excerpt, prompt, created_at, weak])


def query_memory_bundle(
    user_id: Optional[str],
    topic_key: str,
    sub_topic_key: str,
    query_text: str,
    top_k: int = 8,
    min_score: float = DEFAULT_RAG_MIN_SCORE,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "learner_context": "",
        "difficulty_hint": "medium",
        "memory_hits": 0,
        "summary_hits": 0,
        "top_scores": [],
        "weak_focus_markdown": "",
        "lane_used": "none",
        "retrieval_tier": "none",
        "retrieval_trace": [],
    }
    uid = (user_id or "").strip()
    if not uid or not topic_key or not is_configured():
        return out
    _, idx = _client()
    if idx is None:
        return out

    lane = memory_lane_embed_text(topic_key, sub_topic_key, uid)
    qvec = embed_query(f"{lane} | {(query_text or '').strip()}"[:8000])
    if not qvec:
        return out

    strict_min = _tier_min_score(min_score, "RAG_MIN_SCORE_STRICT", min_score)
    topic_min = _tier_min_score(min_score, "RAG_MIN_SCORE_TOPIC", min_score - 0.02)
    user_min = _tier_min_score(min_score, "RAG_MIN_SCORE_USER", min_score - 0.05)
    try:
        min_hits = int((os.getenv("RAG_MIN_HITS_FOR_CONFIDENCE") or "2").strip() or "2")
    except (TypeError, ValueError):
        min_hits = 2
    min_hits = max(1, min(8, min_hits))

    tier_specs = []
    if sub_topic_key:
        tier_specs.append(
            (
                "strict_lane",
                {
                    "user_id": {"$eq": uid},
                    "topic_key": {"$eq": topic_key},
                    "sub_topic_key": {"$eq": sub_topic_key},
                },
                max(1, top_k),
                strict_min,
                1.0,
            )
        )
    tier_specs.append(
        (
            "topic_lane",
            {
                "user_id": {"$eq": uid},
                "topic_key": {"$eq": topic_key},
            },
            max(1, min(24, top_k + 2)),
            topic_min,
            0.92,
        )
    )
    tier_specs.append(
        (
            "user_global",
            {
                "user_id": {"$eq": uid},
            },
            max(1, min(24, top_k + 4)),
            user_min,
            0.84,
        )
    )

    ranked: List[Dict[str, Any]] = []
    seen: set[str] = set()
    retrieval_trace: List[Dict[str, Any]] = []

    for tier_name, flt, tier_top_k, tier_min_score, weight in tier_specs:
        tier_matches = _query_tier_matches(idx, qvec, tier_top_k, flt)
        retrieval_trace.append(
            {
                "tier": tier_name,
                "raw_hits": len(tier_matches),
                "min_score": round(float(tier_min_score), 4),
            }
        )
        for m in tier_matches:
            raw_score = float(m.get("score") or 0.0)
            if raw_score <= float(tier_min_score):
                continue
            key = _match_dedupe_key(m)
            if key in seen:
                continue
            seen.add(key)
            ranked.append(
                {
                    "score": raw_score,
                    "weighted_score": raw_score * float(weight),
                    "tier": tier_name,
                    "metadata": m.get("metadata") or {},
                }
            )

        confident_hits = len([m for m in ranked if m["tier"] == tier_name])
        if confident_hits >= min_hits:
            break

    ranked.sort(key=lambda x: x.get("weighted_score") or 0.0, reverse=True)
    selected = ranked[: max(1, top_k)]
    matches = selected

    out["top_scores"] = [round(x["score"], 4) for x in matches[:5]]
    out["memory_hits"] = len(matches)
    out["summary_hits"] = len(
        [m for m in matches if str((m.get("metadata") or {}).get("weak_summary") or "").strip()]
    )
    out["retrieval_trace"] = retrieval_trace

    snippets: List[str] = []
    for i, m in enumerate(matches, start=1):
        md = m["metadata"]
        summary_snip = _summary_snippet_from_metadata(md)
        ex = str(md.get("excerpt", ""))[:300]
        body = summary_snip or ex
        if not body.strip():
            continue
        label = "summary" if summary_snip else "excerpt"
        snippets.append(f"{i}. [{m.get('tier', 'lane')}] {label}: {body}")

    out["learner_context"] = "\n".join(snippets).strip()
    out["difficulty_hint"] = difficulty_hint_from_matches(matches)
    out["retrieval_tier"] = matches[0].get("tier", "none") if matches else "none"
    out["lane_used"] = lane

    focus_lines: List[str] = []
    seen: set[str] = set()
    max_bullets = 16
    for rank, m in enumerate(matches, start=1):
        md = m.get("metadata") or {}
        sid = str(md.get("session_id", "") or "")[:36]
        tier = str(m.get("tier") or "")
        summary_text = _summary_snippet_from_metadata(md)
        if summary_text:
            base_label = f"hit {rank} ({tier})"
            label = f"{base_label} session `{sid}`" if sid else base_label
            focus_lines.append(f"- **{label} summary:** {summary_text}")
            for focus in _json_list_or_empty(md.get("focus_areas"), max_items=5):
                focus_lines.append(f"  - focus: {focus[:240]}")
            for guide in _json_list_or_empty(md.get("next_mcq_guidance"), max_items=4):
                focus_lines.append(f"  - guidance: {guide[:240]}")
            if len(focus_lines) >= max_bullets:
                break
        for frag in weak_fragments_from_metadata(md):
            nk = frag[:400]
            if nk in seen:
                continue
            seen.add(nk)
            base_label = f"hit {rank} ({tier})"
            label = f"{base_label} session `{sid}`" if sid else base_label
            focus_lines.append(f"- **{label}:** {frag[:900]}")
            if len(focus_lines) >= max_bullets:
                break
        if len(focus_lines) >= max_bullets:
            break
    if focus_lines:
        out["weak_focus_markdown"] = (
            "## RAG: weak concepts from prior flashcard practice (top retrieved)\n\n"
            "**Instruction for generation:** At least half of new MCQs should remediate these misconceptions "
            "(novel stems and numbers; stay within topic).\n\n"
            + "\n".join(focus_lines)
        )
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
    weak_summary: Optional[str] = None,
    focus_areas: Optional[List[str]] = None,
    common_mistakes: Optional[List[str]] = None,
    next_mcq_guidance: Optional[List[str]] = None,
    last_score: Optional[float] = None,
    wrong_count: Optional[int] = None,
    total_attempted: Optional[int] = None,
) -> Optional[str]:
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
    weak_summary_s = " ".join(str(weak_summary or "").split()).strip()
    focus_areas_s = json.dumps((focus_areas or [])[:10], ensure_ascii=False)
    common_mistakes_s = json.dumps((common_mistakes or [])[:10], ensure_ascii=False)
    next_mcq_guidance_s = json.dumps((next_mcq_guidance or [])[:10], ensure_ascii=False)

    lane = memory_lane_embed_text(tk, sk, uid)
    primary_summary = weak_summary_s[:2500]
    if source.startswith("mcq_flashcard_practice") and primary_summary:
        embedding_payload = (
            f"summary: {primary_summary} | focus_areas: {focus_areas_s[:1200]} "
            f"| mistakes: {common_mistakes_s[:1200]} | next_guidance: {next_mcq_guidance_s[:1200]}"
        )
    else:
        embedding_payload = f"weak: {weak_str} | excerpt: {(excerpt or '')[:1500]}"
    text = (
        f"{lane} | prompt: {prompt[:2000]} | source: {source} | {embedding_payload}"
    )

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
        "weak_summary": weak_summary_s[:3500],
        "focus_areas": focus_areas_s[:3500],
        "common_mistakes": common_mistakes_s[:3500],
        "next_mcq_guidance": next_mcq_guidance_s[:3500],
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
    }
    if last_score is not None:
        try:
            meta["last_score"] = float(last_score)
        except (TypeError, ValueError):
            pass
    if wrong_count is not None:
        try:
            meta["wrong_count"] = int(wrong_count)
        except (TypeError, ValueError):
            pass
    if total_attempted is not None:
        try:
            meta["total_attempted"] = int(total_attempted)
        except (TypeError, ValueError):
            pass
    meta["practice_at"] = __import__("datetime").datetime.utcnow().isoformat() + "Z"

    try:
        idx.upsert(vectors=[{"id": vid, "values": vec, "metadata": meta}])
        return vid
    except Exception:
        return None
