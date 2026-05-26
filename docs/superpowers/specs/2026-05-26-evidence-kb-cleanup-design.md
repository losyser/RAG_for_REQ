# Evidence Knowledge Base Cleanup & Supplement Design

**Date:** 2026-05-26  
**Scope:** `data/processed/evidence_units.jsonl` + downstream JSONL + indexes  
**Goal:** 去冗余 + 补全规范缺口，提升 M6_trace（当前 34.5%）

---

## 1. 问题背景

当前证据库（1,270 条）的结构性缺陷：

- **89% 厂家手册**（project_guide + engine_manual），仅 9% 船级社规范
- 多类需求意图的规范级证据为零或极少（见缺口表）
- 存在完全重复的文本条目（同一段话被拆成多条）
- 27 条 `evidence_strength=background` 条目参与索引但被 applicability_filter 硬过滤，纯噪声

M6_gap = 24.4% 说明约四分之一合理拆分的工程需求在当前证据库中找不到规范支撑，这是证据库问题，不是检索算法问题。

---

## 2. 设计决策

### 2.1 操作层面

直接覆盖 `evidence_units.jsonl`（而非另建文件或修改 evidence.docx）：
- JSONL 是 script 10 的输出产物，随时可从 evidence.docx 重新生成
- 不改任何现有脚本的调用接口
- 新增的 script 36 与现有 script 31/32 结构完全相同，直接追加

### 2.2 去冗余策略

**只做两种删除，拒绝相似度去重：**

| 步骤 | 方法 | 目标 | 风险 |
|---|---|---|---|
| 前缀 MD5 去重 | script 30（已有） | 删完全相同文本开头的副本 | 极低 |
| 删 background 条目 | 新增逻辑并入 script 30 | 删 27 条 evidence_strength=background | 零（被 pipeline 硬过滤） |

**明确不做内容相似度去重**，原因：
- 不同船级社（CCS/DNV/IACS）说同一件事各有独立证据价值
- 相同参数在不同工况下（正常运行/启动/停机）的描述虽然相似但不可合并
- 不同 `can_support` 的条目文本可能高度重叠但检索用途不同
- 宁可冗余，不可残缺

### 2.3 补全策略

**内容来源**：联网检索公开规范条文（IACS、DNV、CCS、ISO、GB/T、MARPOL），提炼关键条款，写入与现有条目完全相同格式的 `_make_unit()` 调用。

**优先补全的 8 类缺口**：

| 优先级 | 缺口类型 | 目标规范来源 | 当前状态 |
|---|---|---|---|
| 🔴 高 | 海水滤器配置/反冲洗 | IACS UR M / DNV / CCS | 0 条 |
| 🔴 高 | 模块化快拆/维修可达 | SOLAS Reg.3-4 / DNV | 1 条 |
| 🔴 高 | 管路焊接/无损检测 | IACS UR W7 / CCS焊接规范 | 无规范级 |
| 🟡 中 | NPSH 汽蚀计算 | ISO 9906 / Hydraulic Institute | 仅厂家文件 |
| 🟡 中 | 材料选型/腐蚀防护 | ISO 8044 / GB/T 10125 | 规范来源仅2条 |
| 🟡 中 | 停机后冷却程序 | IACS M51 / MAN 停机规程 | 规范来源仅1条 |
| 🟡 中 | 系统冲洗程序规范 | DNV / CCS 管路冲洗要求 | 规范来源仅1条 |
| 🟢 低 | MARPOL 冷却水泄漏防控 | MARPOL Annex I/VI | 规范来源仅4条 |

---

## 3. 实现结构

### 3.1 新文件

- `scripts/36_add_supplement_units.py` — 补充规范条目，结构与 script 31/32 相同

### 3.2 改动现有文件

- `scripts/30_deduplicate_evidence.py` — 在写出前增加一行：过滤掉 `evidence_strength == "background"` 的条目

### 3.3 不改动的文件

- `scripts/31_add_evidence_units.py` — 直接运行，补入 2 条 ISO 8861 条目
- `scripts/32_add_verified_units.py` — 所有条目已入库，跳过
- `scripts/33_add_source_chunks_for_new_units.py` — 为新 parent_chunk_id 创建 source_chunk，直接运行
- `scripts/11_build_multigranular_indexes.py` — 最终重建全部索引，直接运行

---

## 4. 执行顺序

```bash
# 工作目录：cooling_rag_multigranular/

# 步骤1：去冗余（前缀去重 + 删 background）
python scripts/30_deduplicate_evidence.py

# 步骤2：补入 ISO 8861（2条，script 31 幂等，已有的跳过）
python scripts/31_add_evidence_units.py

# 步骤3：补入新规范缺口（约20-30条）
python scripts/36_add_supplement_units.py

# 步骤4：为新条目创建 source_chunk
python scripts/33_add_source_chunks_for_new_units.py

# 步骤5：重建全部索引
python scripts/11_build_multigranular_indexes.py
```

---

## 5. 验收标准

| 指标 | 当前值 | 目标 |
|---|---|---|
| evidence_units 总条数 | 1,270 | 约 1,260–1,310（去重 ~37条，新增 ~30条） |
| background 条目 | 27 | 0 |
| ship_rule + standard 条目 | 115 | ≥ 145 |
| 零覆盖 intent（海水滤器反冲洗等） | 4类 | ≤ 1类 |
| 下次实验 M6_trace（预期） | 34.5% | ≥ 45%（证据库覆盖改善） |

---

## 6. 约束与注意事项

- script 36 的所有条目 ID 以 `E-SUPP-` 或已有系列（`E-IACS-`、`E-DNV-` 等）命名，与现有 ID 不重叠
- 每条新条目的 `normalized_summary` 字段必须写中文摘要，供人工审核
- `need_human_review` 字段对联网检索条目设为 `"yes"`，对直接摘录规范原文的设为 `"no"`
- script 33 依赖 `parent_chunk_id` 匹配，新条目的 `parent_chunk_id` 必须是新的（不与现有 source_chunk ID 重叠）
