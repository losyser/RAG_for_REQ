from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from cooling_rag_mg.config import get_config
from cooling_rag_mg.text_utils import safe_text

SPLIT_PROMPT = """
你是船舶主机冷却水系统需求工程师。
任务：从工程角度分解原始需求，识别其涵盖的各工程方面，供后续证据检索和工程需求生成使用。
只输出合法 JSON，不输出 Markdown，不输出注释。

## 核心原则：溯源优先，宁少勿多
每个工程方面必须能在原文中找到支撑词句（source_phrase）或属于工程直接隐含。
最多输出 4 个方面。拿不准时合并，不拆。

## implication_type 判断标准
- "explicit"：原文字面包含该方面的关键词或短语
- "direct_implication"：任何熟悉船舶冷却水系统的工程师看到原文，无歧义地认同该方面
  是原文的直接工程含义，不依赖个人偏好（例："稳定可靠的冷却能力" → 冗余泵配置）

## 禁止行为
- source_phrase 在原文中不存在或只是模糊匹配
- 用 direct_implication 覆盖原文未提及的独立工程领域（如原文说参数限值却添加"倾斜工况"）
- 将同一方面拆为多条（如相同工况下不同参数 → 合并为一条）
- 逐字复制原文作为 text（text 应是面向检索的工程化表达）

## 修订模式（有 previous_aspects 和 reviewer_feedback 时）
- 仅修改审核指出的问题
- 保留审核认可的方面，不要整体推翻重来

## topic 命名规则
- 格式：[主要对象] + [工程动作/属性]，例如"冷却水泵冗余配置"、"HT回路温度控制"
- 同一需求集内唯一，禁止宽泛标题（如"参数"、"安装"）

## requirement_type 选项
reliability, redundancy, maintainability, installation, operation, control,
alarm_protection, parameter, verification, safety_environment, water_treatment,
configuration, cost, other

## 输出格式
{
  "sub_requirements": [
    {
      "sub_id": "01",
      "requirement_type": "redundancy",
      "topic": "冷却水泵冗余配置",
      "text": "主机冷却水系统应配置冗余冷却水泵，单台故障时系统应能维持主机基本冷却需求。",
      "source_phrase": "稳定可靠的冷却能力",
      "implication_type": "direct_implication"
    }
  ]
}
"""


REVIEW_PROMPT = """
你是工程需求质量审核员。
任务：审核拆分器对原始需求识别出的工程方面列表，判断是否合法。
只输出合法 JSON，不输出 Markdown，不输出注释。

## 评价维度
1. 溯源合法性：source_phrase 是否确实存在于原文中（字面包含）
2. 推断合理性：implication_type=direct_implication 是否真的是工程共识，非个人推测
3. 完整性：原文明确提到的重要方面是否都已覆盖
4. 无冗余：是否有两条方面高度重叠
5. 检索可用性：text 是否足够具体，能有效检索

## 通过条件
所有方面 valid=true，且 missing_aspects 为空列表。

## 输出格式
{
  "passed": false,
  "aspect_evaluations": [
    {"aspect_name": "方面名称", "valid": true},
    {"aspect_name": "另一方面", "valid": false, "issue": "source_phrase 不在原文中"}
  ],
  "missing_aspects": ["原文提到但未覆盖的方面描述"],
  "overall_feedback": "给拆分器的修订指令，简洁具体"
}
"""


def _review_aspects(
    raw_text: str,
    aspects: list[dict[str, Any]],
) -> dict[str, Any]:
    """调用 LLM 审核方面列表，返回 review 结果 dict。"""
    cfg = get_config()
    client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
    payload = {
        "original_requirement": raw_text,
        "proposed_aspects": [
            {
                "aspect_name": a.get("topic", ""),
                "source_phrase": a.get("source_phrase", ""),
                "implication_type": a.get("implication_type", ""),
                "text": a.get("text", ""),
            }
            for a in aspects
        ],
    }
    resp = client.chat.completions.create(
        model=cfg.deepseek.model,
        messages=[
            {"role": "system", "content": REVIEW_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        temperature=0,
        max_tokens=800,
        response_format={"type": "json_object"},
    )
    try:
        return _extract_json(resp.choices[0].message.content or "")
    except Exception:
        return {"passed": True, "aspect_evaluations": [], "missing_aspects": [], "overall_feedback": ""}


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```json"):
        text = text.removeprefix("```json").strip()
    if text.startswith("```"):
        text = text.removeprefix("```").strip()
    if text.endswith("```"):
        text = text.removesuffix("```").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError("LLM 返回不是合法 JSON")


def _dedup_topics(subs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """topic 相同时自动加序号区分，防止 agent 侧无法归并。"""
    seen: dict[str, int] = {}
    out = []
    for s in subs:
        topic = s.get("topic", "")
        if topic in seen:
            seen[topic] += 1
            s = dict(s)
            s["topic"] = f"{topic}_{seen[topic]}"
        else:
            seen[topic] = 1
        out.append(s)
    return out


def split_requirement(requirement_id: str, stakeholder: str, raw_text: str) -> list[dict[str, Any]]:
    cfg = get_config()
    if cfg.deepseek.enabled and cfg.deepseek.use_requirement_splitter:
        try:
            client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
            payload = {
                "requirement_id": requirement_id,
                "stakeholder": stakeholder,
                "raw_requirement": raw_text,
            }
            resp = client.chat.completions.create(
                model=cfg.deepseek.model,
                messages=[
                    {"role": "system", "content": SPLIT_PROMPT},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                temperature=cfg.deepseek.temperature,
                max_tokens=cfg.deepseek.max_tokens_split,
                response_format={"type": "json_object"},
            )
            obj = _extract_json(resp.choices[0].message.content or "")
            subs = obj.get("sub_requirements", [])
            cleaned = []
            for i, s in enumerate(subs, start=1):
                if not isinstance(s, dict):
                    continue
                text = safe_text(s.get("text"))
                if not text:
                    continue
                cleaned.append({
                    "sub_id": safe_text(s.get("sub_id")) or f"{i:02d}",
                    "requirement_type": safe_text(s.get("requirement_type")) or infer_type(text),
                    "topic": safe_text(s.get("topic")) or text[:20],
                    "text": text,
                    "split_method": "deepseek",
                })
            if cleaned:
                return _dedup_topics(cleaned)
        except Exception as exc:
            return fallback_split(raw_text, error=str(exc))
    return fallback_split(raw_text)


def infer_type(text: str) -> str:
    if any(x in text for x in ["冗余", "备用", "单台", "故障时", "基本运行", "一用一备"]):
        return "redundancy"
    if any(x in text for x in ["维护费用", "成本", "费用"]):
        return "cost"
    if any(x in text for x in ["维护", "检修", "清洗", "排气", "放水", "补液", "更换", "拆"]):
        return "maintainability"
    if any(x in text for x in ["安装", "施工", "焊接", "布置", "空间", "试压", "冲洗"]):
        return "installation"
    if any(x in text for x in ["报警", "警报", "保护", "降负荷", "停机保护", "高温报警", "低压报警"]):
        return "alarm_protection"
    if any(x in text for x in ["温度", "压力", "流量", "液位", "参数", "限值"]):
        return "parameter"
    if any(x in text for x in ["自动", "手动", "控制", "监控", "传感器", "集控室", "显示", "监测"]):
        return "control"
    if any(x in text for x in ["试验", "检查", "记录", "验收", "图纸", "计算书"]):
        return "verification"
    if any(x in text for x in ["泄漏", "腐蚀", "环保", "废液", "化学品", "烫伤", "误操作"]):
        return "safety_environment"
    # 工况稳定性 → operation（不要判为 reliability）
    if any(x in text for x in ["启动", "低负荷", "满负荷", "负荷变化", "停机后", "工况"]):
        return "operation"
    if any(x in text for x in ["稳定", "可靠", "航行安全", "冷却不足"]):
        return "reliability"
    return "other"


def fallback_split(raw_text: str, error: str = "") -> list[dict[str, Any]]:
    parts = re.split(r"[。；;]\s*", raw_text)
    parts = [p.strip() for p in parts if p.strip()]
    if not parts:
        parts = [raw_text.strip()]
    out = []
    for i, p in enumerate(parts, start=1):
        item = {
            "sub_id": f"{i:02d}",
            "requirement_type": infer_type(p),
            "topic": p[:20],
            "text": p,
            "split_method": "fallback_rule",
        }
        if error:
            item["split_error"] = error
        out.append(item)
    return _dedup_topics(out)
