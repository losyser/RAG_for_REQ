# -*- coding: utf-8 -*-
"""
Script 25: Generate a pool of 100 stakeholder requirements for experiment sampling.

Each of the 16 stakeholder types gets ~6-7 requirements covering different
aspects of the ship main engine cooling water system.

Output: data/processed/requirement_pool_100.jsonl
  Each line: {"requirement_id": "P001", "stakeholder": "...", "requirement_text": "..."}

Usage:
  python scripts/25_generate_requirement_pool.py [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.jsonl import write_jsonl
from openai import OpenAI

# ── 现有 30 条需求（作为少样本示例，避免 LLM 重复生成） ──────────────────────
_EXISTING: dict[str, list[str]] = {
    "船东代表": [
        "主机冷却水系统应具备较高运行可靠性，不能因冷却能力不足、冷却水循环中断或温度失控影响推进装置安全运行。",
        "主机冷却水系统应具有较好的运行经济性。在满足主机及各冷却用户需求的前提下，配置应避免明显过大选型，减少长期运行能耗。",
    ],
    "主机厂家": [
        "主机入口和出口冷却水温度、压力、流量应满足主机厂家技术文件要求。",
        "高温冷却水回路和低温冷却水回路应满足主机在启动、正常运行、低负荷、负荷快速变化和停机后冷却阶段的温度控制要求。",
    ],
    "系统设计方": [
        "主机冷却水系统应明确区分高温冷却水回路、低温冷却水回路和海水侧边界。",
        "主机冷却水系统应在设计阶段明确各冷却用户的热负荷、流量需求和压力损失。",
    ],
    "船厂建造方": [
        "冷却水系统管路布置应清楚、紧凑并便于施工。",
        "冷却水系统管路安装应考虑排气、放水、冲洗和检修需要。",
    ],
    "设备采购方": [
        "冷却水泵、冷却器、温控阀等关键设备的选型应满足主机厂家、船级社和项目技术规格书要求。",
        "冷却器、冷却水泵、温控阀等设备的采购资料应完整，包括型号、容量、材料、接口和厂家技术文件。",
    ],
    "轮机长": [
        "冷却水系统应便于运行监测。集控室应能清楚显示冷却水温度、压力、液位、泵运行状态等关键参数。",
        "冷却水系统应便于船员进行日常巡视和状态判断。主要设备应具备清楚的现场标识。",
    ],
    "自动化工程师": [
        "冷却水泵、温控阀、传感器和必要的流量信号应接入监控系统，支持关键运行参数采集和异常报警。",
        "冷却水系统的报警、联锁和保护逻辑应与主机控制系统、机舱监测报警系统协调一致。",
    ],
    "安全负责人": [
        "冷却水系统应设置必要的报警与保护功能，冷却水高温、低压、低液位、泵故障等情况应能被及时发现。",
        "冷却水系统应降低高温介质、旋转设备、带压管路和化学处理液对人员造成伤害的风险。",
    ],
    "维修人员": [
        "冷却水系统应便于维护和检修，冷却器、泵、滤器、温控阀等设备周围应留有合理维护空间。",
        "冷却水系统应支持故障隔离和局部检修，主要设备应具备合理的隔离条件。",
    ],
    "调试人员": [
        "冷却水系统应具备可实施的冲洗、排气、补水、压力试验和调试条件。",
        "冷却水系统调试时应验证泵组运行、阀门动作、温控调节、报警触发和主要冷却用户参数响应。",
    ],
    "船级社验船师": [
        "冷却水系统的设计、材料、设备选型、报警保护、试验验证和技术文件应满足船级社审查要求。",
        "冷却水系统应满足适用船级社规则对备用冷却水供应、泵组配置和试验验证的要求。",
    ],
    "材料工程师": [
        "冷却水系统管路、阀门、冷却器等材料应适用于冷却介质、温度、压力和腐蚀环境。",
        "海水侧管路、阀门、冷却器和相关附件应考虑海水腐蚀、海生物附着和材料相容性。",
    ],
    "运维管理人员": [
        "冷却液与水质管理应满足主机厂家和项目维护文件要求，冷却液浓度和防腐剂状态应可检查。",
        "冷却水系统应便于建立运行维护记录，相关数据应能形成可追溯的运行维护数据。",
    ],
    "船厂质量检验人员": [
        "冷却水系统安装完成后，应对管路连接、阀门方向、支架固定、传感器安装等进行检查并形成记录。",
        "冷却水系统安装和试验完成后，应检查管路密性、支架固定、传感器安装等，发现问题应在交船前整改。",
    ],
    "环保负责人": [
        "冷却水系统应减少冷却液泄漏、海水泄漏和化学品误排放风险，满足项目环保要求。",
    ],
    "项目管理方": [
        "冷却水系统的需求、设计、采购、施工、调试和验收资料应保持一致，变更应可追踪。",
    ],
}

# 每个利益相关方需要额外生成的需求数量（确保总数达到100）
_TARGETS: dict[str, int] = {
    "船东代表":         5,
    "主机厂家":         5,
    "系统设计方":       5,
    "船厂建造方":       5,
    "设备采购方":       5,
    "轮机长":           5,
    "自动化工程师":     5,
    "安全负责人":       5,
    "维修人员":         5,
    "调试人员":         5,
    "船级社验船师":     5,
    "材料工程师":       5,
    "运维管理人员":     5,
    "船厂质量检验人员": 5,
    "环保负责人":       7,   # 现有1条，补至8条
    "项目管理方":       7,   # 现有1条，补至8条
}  # 总新增 = 14×5 + 2×7 = 84，加上现有30 = ~84+30=114 → 取前100


_GEN_PROMPT = """\
You are a marine engineering requirements specialist for ship main engine cooling water systems.

Generate exactly {n} NEW stakeholder requirements from the perspective of: {stakeholder}

These requirements must be:
1. About the ship main engine (propulsion engine) COOLING WATER SYSTEM only
2. Different from the existing requirements below — cover NEW aspects, sub-topics, or conditions
3. Written in Chinese, 1-3 sentences each, clear engineering language
4. Realistic and technically specific to this domain

Existing requirements for this stakeholder (do NOT repeat these topics):
{existing}

Output ONLY a JSON array of strings, one requirement per element. No other text.
Example format: ["需求1文字...", "需求2文字..."]
"""


def _generate_batch(
    client: OpenAI,
    model: str,
    stakeholder: str,
    n: int,
    existing: list[str],
    max_tokens: int,
) -> list[str]:
    existing_str = "\n".join(f"- {r}" for r in existing)
    prompt = _GEN_PROMPT.format(
        n=n,
        stakeholder=stakeholder,
        existing=existing_str,
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
    )
    content = resp.choices[0].message.content or "{}"
    # LLM may return {"requirements": [...]} or just [...]
    obj = json.loads(content)
    if isinstance(obj, list):
        return [str(r) for r in obj]
    for key in ("requirements", "result", "data", "items"):
        if isinstance(obj.get(key), list):
            return [str(r) for r in obj[key]]
    # fallback: collect all list values
    for v in obj.values():
        if isinstance(v, list):
            return [str(r) for r in v]
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="Regenerate even if pool file already exists")
    args = parser.parse_args()

    cfg = get_config()
    output_path = cfg.paths.processed_dir / "requirement_pool_100.jsonl"

    if output_path.exists() and not args.force:
        existing_pool = [json.loads(l) for l in output_path.read_text(encoding="utf-8").splitlines() if l.strip()]
        print(f"Pool already exists: {len(existing_pool)} requirements → {output_path}")
        print("Use --force to regenerate.")
        return

    client = OpenAI(
        api_key=cfg.deepseek.api_key,
        base_url=cfg.deepseek.base_url,
    )

    all_reqs: list[dict] = []
    counter = 1

    # 先把现有 30 条加入池
    print("Adding existing 30 requirements to pool...")
    for stakeholder, existing_list in _EXISTING.items():
        for text in existing_list:
            all_reqs.append({
                "requirement_id": f"P{counter:03d}",
                "stakeholder": stakeholder,
                "requirement_text": text,
            })
            counter += 1

    print(f"  Added {counter - 1} existing requirements\n")

    # 为每个利益相关方生成新需求
    for stakeholder, n_new in _TARGETS.items():
        existing = _EXISTING.get(stakeholder, [])
        print(f"Generating {n_new} for [{stakeholder}]...", end=" ", flush=True)
        try:
            new_reqs = _generate_batch(
                client, cfg.deepseek.model, stakeholder, n_new, existing,
                max_tokens=1024,
            )
            if not new_reqs:
                print("✗ empty response")
                continue
            added = 0
            for text in new_reqs[:n_new]:
                text = text.strip()
                if not text:
                    continue
                all_reqs.append({
                    "requirement_id": f"P{counter:03d}",
                    "stakeholder": stakeholder,
                    "requirement_text": text,
                })
                counter += 1
                added += 1
            print(f"OK {added} added (pool={len(all_reqs)})")
        except Exception as exc:
            print(f"FAIL {exc}")

    # 截取前100条（按生成顺序）
    pool = all_reqs[:100]
    write_jsonl(str(output_path), pool)

    print(f"\nPool saved: {len(pool)} requirements → {output_path}")
    print("\nStakeholder distribution:")
    from collections import Counter
    dist = Counter(r["stakeholder"] for r in pool)
    for s, n in sorted(dist.items(), key=lambda x: -x[1]):
        print(f"  {s}: {n}")


if __name__ == "__main__":
    main()
