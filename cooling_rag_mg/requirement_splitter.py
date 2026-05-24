from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from cooling_rag_mg.config import get_config
from cooling_rag_mg.text_utils import safe_text

SPLIT_PROMPT = """
你是船舶主机冷却水系统需求工程助手。
你的任务是把一个利益相关方的原始需求拆成工程子需求，供后续证据检索使用。
不要生成检索关键词。不要生成证据判断。不要输出 Markdown。只输出合法 JSON。

## 核心原则：宁少勿多
每个原始需求最多拆出 4 条子需求。拆分的目的是区分不同的工程关注点，不是穷举所有细节。
如果拿不准要不要拆，就不拆，合并为一条。

## 应该拆分的情况（满足其中之一才拆）
1. 工程类型完全不同，例如"冗余配置"（redundancy）和"安装布置"（installation）必须分开，因为检索时需要找完全不同的证据。
2. 工程对象完全不同且独立，例如"冷却水泵"和"冷却器"各有独立的工程要求，可以分开。

## 禁止拆分的情况（以下情况必须合并为一条）
3. 同一工程目标在不同工况下的表达，一律合并为一条 operation 类型，在 text 中列举所有工况。
   例："启动、低负荷、满负荷、快速负荷变化、停机后冷却各工况下参数稳定" → 1 条，不是 5 条。
4. 对同一系统多个参数或部件的监测要求，按功能归并（过程参数 / 设备状态），最多 2 条。
   例："集控室监测温度、压力、液位、泵状态、阀门状态、冷却器状态" → 最多 2 条，不是 6 条。
5. 对同一部件的多项并列要求（如"冷却器应便于拆卸、清洗、更换"），合并为一条 maintainability。
6. 原文列举多个部件但工程目的相同（如"冷却器、滤器、泵周围应留有足够空间"），合并为一条。

## topic 命名规则
- 格式：[主要对象] + [工程动作/属性]，例如"冷却水泵冗余配置"、"过程参数监测"
- 必须唯一，同一需求集内不能重名
- 禁止使用宽泛标题：不能只写"监测"、"参数稳定性"、"安装要求"

## requirement_type 选择
只能从以下值选择：
reliability, redundancy, maintainability, installation, operation, control,
alarm_protection, parameter, verification, safety_environment, water_treatment,
configuration, cost, other

- 工况稳定性（任何工况下保持参数/运行稳定）→ operation
- 监测/显示/集控室/传感器接入 → control
- 温度/压力/流量具体限值 → parameter
- 冗余/备用/一用一备 → redundancy
- 安装/施工/布置/冲洗/试压/焊接/支架 → installation
- 报警/保护/停机/降负荷 → alarm_protection
- 维护/检修/清洗/拆卸/更换/检修空间 → maintainability
- 泄漏/腐蚀/烫伤/环保/误操作 → safety_environment
- 图纸/计算书/审查/验收/船级社文件 → verification

## 输出格式
{
  "sub_requirements": [
    {
      "sub_id": "01",
      "requirement_type": "reliability",
      "topic": "冷却水系统运行稳定性",
      "text": "主机冷却水系统应运行稳定，不能因冷却不足影响航行安全。"
    }
  ]
}
"""


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
