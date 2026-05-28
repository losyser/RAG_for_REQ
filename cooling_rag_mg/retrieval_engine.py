from __future__ import annotations

from typing import Any

import torch
from cooling_rag_mg.hybrid_fusion import rrf_fuse

from cooling_rag_mg.index_store import HybridIndexSearcher, load_index, load_sentence_transformer
from cooling_rag_mg.jsonl import read_jsonl
from cooling_rag_mg.retrieval_profile import build_profile
from cooling_rag_mg.schema import normalize_v2_metadata
from cooling_rag_mg.text_utils import safe_text


def record_id(record: dict[str, Any]) -> str:
    return safe_text(record.get("id") or record.get("chunk_id"))


class MultiGranularRetriever:
    def __init__(
        self,
        *,
        source_index_dir: str,
        evidence_index_dir: str,
        evidence_units_path: str,
        evidence_groups_path: str,
        device: str = "cpu",
    ):
        source_built = load_index(source_index_dir)
        evidence_built = load_index(evidence_index_dir)
        model_kwargs = {"torch_dtype": torch.float16} if device.startswith("cuda") else {}
        shared_model = load_sentence_transformer(
            source_built.model_name,
            device=device,
            label="[Retriever]",
            model_kwargs=model_kwargs,
        )
        actual_device = str(shared_model.device)
        self.source_searcher = HybridIndexSearcher(source_built, device=actual_device, model=shared_model)
        self.evidence_searcher = HybridIndexSearcher(evidence_built, device=actual_device, model=shared_model)
        self.units = read_jsonl(evidence_units_path)
        self.groups = read_jsonl(evidence_groups_path)
        for unit in self.units:
            unit["metadata"] = normalize_v2_metadata(unit.get("metadata", {}) or {})
        for group in self.groups:
            group["metadata"] = normalize_v2_metadata(group.get("metadata", {}) or {})
        self.units_by_id = {u["id"]: u for u in self.units}
        self.units_by_chunk: dict[str, list[dict[str, Any]]] = {}
        for u in self.units:
            self.units_by_chunk.setdefault(u["parent_chunk_id"], []).append(u)
        self.groups_by_id = {g["group_id"]: g for g in self.groups}

    def search_sub_requirement(
        self,
        sub_requirement: dict[str, Any],
        *,
        top_k: int = 4,
        coarse_k: int = 12,
        fine_k: int = 40,
    ) -> dict[str, Any]:
        profile = build_profile(sub_requirement)

        # ── 粗检索：用聚焦 query（主题 + 部件 + 方面），找相关 chunk ──
        coarse_query = self._build_coarse_query(sub_requirement, profile)
        # ── 细检索：用完整 query（含全部关键词），提升 recall ──
        fine_query = self._build_fine_query(sub_requirement, profile)

        # 粗检索（source_chunks 级别）
        coarse_vector = self.source_searcher.vector_search(coarse_query, coarse_k * 2)
        coarse_bm25 = self.source_searcher.bm25_search(coarse_query, coarse_k * 2)
        coarse = rrf_fuse([coarse_vector, coarse_bm25], id_key="chunk_id")[: coarse_k * 2]
        coarse = self._score_by_profile(coarse, profile, is_chunk=True)
        coarse = sorted(coarse, key=lambda x: x.get("final_score", 0.0), reverse=True)[:coarse_k]
        allowed_chunks = {c["chunk_id"] for c in coarse}

        # 细检索（evidence_units 级别）
        fine_vector = self.evidence_searcher.vector_search(fine_query, fine_k * 2)
        fine_bm25 = self.evidence_searcher.bm25_search(fine_query, fine_k * 2)
        fine = rrf_fuse([fine_vector, fine_bm25], id_key="id")

        for item in fine:
            item["coarse_chunk_hit"] = item.get("parent_chunk_id") in allowed_chunks
            # coarse_bonus 仅给 hit 的证据加分，且上限 0.30
            item["coarse_bonus"] = 0.30 if item["coarse_chunk_hit"] else 0.0

        fine = self._score_by_profile(fine, profile, is_chunk=False)
        fine = self._soft_filter_by_profile(fine, profile)
        fine = sorted(fine, key=lambda x: x.get("final_score", 0.0), reverse=True)[:fine_k]

        # 扩展：通过 evidence group 引入同组近邻证据
        # 改进：扩展证据使用独立分数，不继承父证据的 rrf_score
        expanded = self._expand_groups(fine[: max(top_k, 12)], base_items=fine)
        expanded = self._score_by_profile(expanded, profile, is_chunk=False)
        expanded = self._soft_filter_by_profile(expanded, profile)
        expanded = self._dedupe(expanded)
        expanded = sorted(expanded, key=lambda x: x.get("final_score", 0.0), reverse=True)

        return {
            "query": fine_query,
            "coarse_query": coarse_query,
            "profile": profile,
            "coarse_results": coarse,
            "candidate_results": expanded[:fine_k],
            "selected_results": expanded[:top_k],
        }

    def _build_coarse_query(self, sub: dict[str, Any], profile: dict[str, Any]) -> str:
        """粗检索 query：聚焦主题 + 部件 + 方面，不堆砌所有关键词。"""
        parts = [
            safe_text(sub.get("topic")),
            safe_text(sub.get("text")),
            # 部件名：只取前 5 个，避免 query 过长
            " ".join(profile.get("target_components", [])[:5]),
            " ".join(profile.get("target_aspects", [])[:5]),
        ]
        return "\n".join([p for p in parts if safe_text(p)])

    def _build_fine_query(self, sub: dict[str, Any], profile: dict[str, Any]) -> str:
        """细检索 query：加入 can_support、条件、关键词，提升 recall。"""
        parts = [
            safe_text(sub.get("topic")),
            safe_text(sub.get("text")),
            profile.get("intent", ""),
            " ".join(profile.get("target_components", [])),
            " ".join(profile.get("target_aspects", [])),
            " ".join(profile.get("target_phases", [])),
            " ".join(profile.get("target_conditions", [])),
            " ".join(profile.get("required_can_support", [])),
            # positive_keywords 截取前 20 个，避免噪声过多
            " ".join(profile.get("positive_keywords", [])[:20]),
            " ".join(profile.get("must_have_any", [])),
        ]
        return "\n".join([p for p in parts if safe_text(p)])

    def _score_by_profile(
        self,
        items: list[dict[str, Any]],
        profile: dict[str, Any],
        *,
        is_chunk: bool,
    ) -> list[dict[str, Any]]:
        target_components = set(profile.get("target_components", []) or [])
        target_aspects = set(profile.get("target_aspects", []) or [])
        target_phases = set(profile.get("target_phases", []) or [])
        target_conditions = set(profile.get("target_conditions", []) or [])
        required_can_support = set(profile.get("required_can_support", []) or [])
        keywords = [k.lower() for k in profile.get("positive_keywords", []) + profile.get("must_have_any", []) if k]

        scored: list[dict[str, Any]] = []
        for item in items:
            metadata = normalize_v2_metadata(item.get("metadata", {}) or {})
            item_components = set(metadata.get("component_objects", []) or [])
            item_aspects = set(metadata.get("requirement_intents", []) or [])
            item_phases = set(metadata.get("engineering_phase", []) or [])
            item_conditions = set(metadata.get("applicable_condition", []) or [])
            item_can_support = set(metadata.get("can_support", []) or [])

            evidence_strength = safe_text(metadata.get("evidence_strength")).lower()
            applicability_level = safe_text(metadata.get("applicability_level"))
            is_generalizable = safe_text(metadata.get("is_generalizable")).lower()
            source_type = safe_text(metadata.get("source_type")).lower()

            rrf = float(item.get("rrf_score", 0.0))
            coarse_bonus = float(item.get("coarse_bonus", 0.0))
            score = rrf + coarse_bonus

            matched_components = sorted(target_components & item_components)
            matched_aspects = sorted(target_aspects & item_aspects)
            matched_phases = sorted(target_phases & item_phases)
            matched_conditions = sorted(target_conditions & item_conditions)
            matched_can_support = sorted(required_can_support & item_can_support)

            # ── 部件匹配 ──
            if target_components:
                comp_ratio = len(matched_components) / len(target_components) if target_components else 0
                if matched_components:
                    score += 0.40 + 0.20 * comp_ratio  # 0.40~0.60
                else:
                    # 系统级证据不惩罚
                    if "main_engine_cooling_water_system" not in item_components:
                        score -= 0.30

            # ── 方面匹配 ──
            if target_aspects:
                aspect_ratio = len(matched_aspects) / len(target_aspects) if target_aspects else 0
                if matched_aspects:
                    score += 0.35 + 0.25 * aspect_ratio  # 0.35~0.60
                else:
                    score -= 0.45

            # ── can_support 匹配 ──
            if required_can_support:
                if matched_can_support:
                    score += 0.40
                else:
                    score -= 0.20

            # ── 工程阶段 ──
            if target_phases and matched_phases:
                score += 0.20

            # ── 工况 ──
            if target_conditions and matched_conditions:
                score += 0.15

            # ── 证据强度 ──
            if evidence_strength == "direct":
                score += 0.50
            elif evidence_strength == "indirect":
                score += 0.20
            elif evidence_strength == "background":
                score -= 0.50
            elif evidence_strength == "not_applicable":
                score -= 1.50

            # ── 来源类型 ──
            if source_type in {"ship_rule", "class_rule", "standard"}:
                score += 0.40
            elif source_type in {"project_guide", "engine_manual", "installation_guide"}:
                score += 0.25
            elif source_type in {"paper", "patent"}:
                score -= 0.80

            # ── 泛化性 ──
            if is_generalizable == "no":
                score -= 0.40
            elif is_generalizable == "limited":
                score -= 0.05

            # ── 适用性等级 ──
            if applicability_level == "background_reference":
                score -= 0.40
            elif applicability_level in {"class_rule", "general_engineering"}:
                score += 0.25
            elif applicability_level in {"manufacturer_specific", "project_specific"}:
                score += 0.05

            # ── 噪声标记 ──
            if metadata.get("is_noise") is True:
                score -= 2.0

            # ── 关键词命中（BM25 增强，上限 0.50）──
            text_blob = "\n".join([
                safe_text(item.get("search_text")),
                safe_text(item.get("text")),
                safe_text(item.get("chunk_text")),
                safe_text(metadata.get("topic")),
                safe_text(metadata.get("section_title")),
                safe_text(metadata.get("limitation")),
                safe_text(metadata.get("unsupported_requirements")),
                safe_text(metadata.get("normalized_summary")),
                " ".join(metadata.get("keywords_zh", []) or []),
                " ".join(metadata.get("keywords_en", []) or []),
            ]).lower()
            hit_count = sum(1 for k in keywords if k and k.lower() in text_blob)
            score += min(0.50, hit_count * 0.06)

            item["metadata"] = metadata
            item["profile_score"] = round(score - rrf - coarse_bonus, 4)
            item["final_score"] = round(score, 4)
            item["profile_match"] = {
                "target_components": sorted(target_components),
                "item_components": sorted(item_components),
                "matched_components": matched_components,
                "target_aspects": sorted(target_aspects),
                "item_aspects": sorted(item_aspects),
                "matched_aspects": matched_aspects,
                "target_phases": sorted(target_phases),
                "item_phases": sorted(item_phases),
                "matched_phases": matched_phases,
                "target_conditions": sorted(target_conditions),
                "item_conditions": sorted(item_conditions),
                "matched_conditions": matched_conditions,
                "required_can_support": sorted(required_can_support),
                "item_can_support": sorted(item_can_support),
                "matched_can_support": matched_can_support,
                "evidence_strength": evidence_strength,
                "source_type": source_type,
                "applicability_level": applicability_level,
                "is_generalizable": is_generalizable,
            }
            scored.append(item)
        return scored

    def _soft_filter_by_profile(
        self,
        items: list[dict[str, Any]],
        profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """软过滤：标注 retrieval_role；对低分 paper/patent 和双不匹配负分项 hard-reject。"""
        out: list[dict[str, Any]] = []
        target_components = set(profile.get("target_components", []) or [])
        target_aspects = set(profile.get("target_aspects", []) or [])

        for item in items:
            metadata = normalize_v2_metadata(item.get("metadata", {}) or {})
            strength = safe_text(metadata.get("evidence_strength")).lower()
            app_level = safe_text(metadata.get("applicability_level"))
            generalizable = safe_text(metadata.get("is_generalizable")).lower()
            source_type = safe_text(metadata.get("source_type")).lower()

            # hard-reject：明确不适用
            if strength == "not_applicable":
                continue
            if metadata.get("is_noise") is True:
                continue

            final_score = float(item.get("final_score", 0.0))

            # paper/patent 且分数低于 0.2 → 丢弃
            if source_type in {"paper", "patent"} and final_score < 0.2:
                continue

            item_components = set(metadata.get("component_objects", []) or [])
            item_aspects = set(metadata.get("requirement_intents", []) or [])

            comp_hit = not target_components or bool(target_components & item_components) or "main_engine_cooling_water_system" in item_components
            aspect_hit = not target_aspects or bool(target_aspects & item_aspects)

            # 部件和方面双不匹配且分数为负 → 丢弃
            if not comp_hit and not aspect_hit and final_score < 0.0:
                continue

            if strength == "background" or (generalizable == "no" and app_level == "background_reference"):
                item["retrieval_role"] = "context"
            elif not comp_hit and not aspect_hit:
                # 部件和方面都不匹配，降为弱候选，但不丢弃
                item["retrieval_role"] = "weak_context"
            elif not comp_hit or not aspect_hit:
                item["retrieval_role"] = item.get("retrieval_role") or "supporting"
            else:
                item["retrieval_role"] = item.get("retrieval_role") or "candidate"

            item["metadata"] = metadata
            out.append(item)
        return out

    def _expand_groups(
        self,
        items: list[dict[str, Any]],
        base_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        通过 evidence group 扩展同组证据。

        改进：扩展证据使用固定低分（0.15）而非继承父证据的 rrf_score，
        避免扩展证据分数虚高。
        """
        out = list(base_items)  # 细检索全量结果为基础
        seen = {x.get("id") for x in out if x.get("id")}

        for item in items:
            metadata = normalize_v2_metadata(item.get("metadata", {}) or {})
            gid = metadata.get("refined_group_id") or metadata.get("same_requirement_group")
            if not gid or gid not in self.groups_by_id:
                continue
            group = self.groups_by_id[gid]
            # 每个 group 最多扩展 4 条，避免一个 group 主导候选
            added = 0
            for eid in group.get("evidence_ids", []):
                if added >= 4:
                    break
                if eid in seen:
                    continue
                unit = dict(self.units_by_id.get(eid, {}))
                if not unit:
                    continue
                unit["expanded_from_group"] = gid
                # 扩展证据使用独立基础分，而非继承父证据
                unit["rrf_score"] = 0.15
                unit["coarse_bonus"] = 0.0
                out.append(unit)
                seen.add(eid)
                added += 1
        return out

    def _dedupe(
        self,
        items: list[dict[str, Any]],
        max_per_group: int = 4,  # 从 2 提高到 4，避免过度压制同部件证据
    ) -> list[dict[str, Any]]:
        seen_ids: set[str] = set()
        group_counts: dict[str, int] = {}
        out = []

        for item in items:
            rid = item.get("id")
            if not rid or rid in seen_ids:
                continue
            metadata = normalize_v2_metadata(item.get("metadata", {}) or {})
            gid = (
                metadata.get("refined_group_id")
                or metadata.get("same_requirement_group")
                or rid
            )
            if group_counts.get(gid, 0) >= max_per_group:
                continue
            item["metadata"] = metadata
            out.append(item)
            seen_ids.add(rid)
            group_counts[gid] = group_counts.get(gid, 0) + 1
        return out
