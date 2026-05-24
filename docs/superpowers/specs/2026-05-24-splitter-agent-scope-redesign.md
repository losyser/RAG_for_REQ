# 设计文档：拆分器 v2 + 审核循环 + Agent 范围约束

**日期**：2026-05-24  
**状态**：待实现  
**涉及文件**：`requirement_splitter.py`、`engineering_requirement_agent.py`、`pipeline.py`（只读）、`config.py`

---

## 一、问题陈述

当前系统存在两层缺陷，导致工程需求输出超出原始需求范围：

### 第一层：拆分器做句界切分，不做工程方面分解

| 需求 | 当前行为 | 问题 |
|---|---|---|
| R001（单句） | R001-01 逐字复制原文 | 无检索意义，子需求等于原文 |
| R002（两从句） | 在句号处机械切断 | 语义分组正确但有时仍近似复制 |
| R005（单句） | R005-01 逐字复制原文 | 同 R001 |

### 第二层：Agent 以证据为主锚生成工程需求，超出原始范围

典型案例：
- R002 原始未提倾斜工况，Agent 却生成了"横倾15°、纵倾7.5°"的工程需求（`ER-R002-01-06`）——原文无任何对应词句
- R005 原始只说采购资料，Agent 却生成了海试要求——原文完全未提试验
- R001 生成冗余泵配置在新设计下是允许的（direct_implication），但当前缺乏溯源机制，无法区分合法推断与凭空添加

### 确定的边界规则

**允许**：对原始需求明确提到或工程上直接隐含的方面进行工程化展开（"可靠冷却" → 冗余泵配置，任何熟悉该领域的工程师都会认同）

**禁止**：添加原始需求完全未涉及、需要额外推断的方面（"倾斜工况"对于一条参数限值需求属于凭空添加）

---

## 二、设计方案：方案一

审核循环封装在拆分器内部，pipeline.py 和检索引擎接口不变。

### 整体数据流

```
原始需求
  │
  ▼
拆分器 v2（工程方面识别，含 source_phrase 溯源）
  │  候选方面列表
  ▼
审核 Agent（溯源检查 + 完整性检查）
  ├─ 通过 ──────────────────────────────────┐
  └─ 不通过 → feedback → 拆分器 v2 修订    │
             （最多 max_rounds=3 轮）        │
                                            ▼
                              validated sub_requirements
                              （含 source_phrase、implication_type）
                                            │
                                            ▼
                              检索引擎（接口不变）
                                            │
                                            ▼
                         compact_requirement_context()
                         新增 allowed_engineering_aspects
                                            │
                                            ▼
                         工程需求 Agent（以方面列表为硬边界）
                                            │
                                            ▼
                         normalize_agent_output()（兜底校验）
                                            │
                                            ▼
                              工程需求输出（不超出原始范围）
```

---

## 三、组件详细设计

### 3.1 拆分器 v2（`requirement_splitter.py`）

#### 输出格式变化

在现有子需求结构上新增两个字段，检索引擎接口完全不变：

```json
{
  "sub_requirement_id": "R001-01",
  "requirement_type": "redundancy",
  "topic": "冷却水泵冗余配置",
  "text": "主机冷却水系统应配置冗余冷却水泵，确保单台故障时系统仍能维持主机基本冷却需求。",
  "source_phrase": "稳定可靠的冷却能力",
  "implication_type": "direct_implication"
}
```

**新字段说明**：
- `source_phrase`：原始需求中直接支撑该方面的词句（必须是原文摘录，不得改写）
- `implication_type`：`"explicit"`（原文明确提到）或 `"direct_implication"`（工程直接隐含）

#### 新 Prompt 核心规则

```
任务：从工程角度分解原始需求，识别其涵盖的各工程方面。

规则：
1. 每个方面必须对应原文中的 source_phrase（原文直接摘录）
2. implication_type 使用 direct_implication 的条件：
   任何熟悉该工程领域的工程师看到原文，都会无歧义地认同该推断，
   且不依赖个人偏好或经验差异
3. 若找不到原文支撑，禁止生成该方面
4. 不得将同一方面拆成多条，不得合并不同方面
5. 每条 text 字段应具有检索意义（足够具体，能构造有效 BM25/向量 query）
6. 修订模式下：收到 feedback 时，针对具体问题修订，保留评审认可的方面
```

#### 修订循环逻辑（伪代码）

```python
def split_with_review(original_req, cfg):
    feedback = None
    prev_aspects = None
    for attempt in range(cfg.splitter_review_max_rounds):
        aspects = _call_splitter_llm(original_req, prev_aspects, feedback)
        review = _call_reviewer_llm(original_req, aspects)
        if review["passed"]:
            return aspects
        feedback = review["overall_feedback"]
        prev_aspects = aspects

    # 超过上限：使用最后一轮结果，标记警告
    for aspect in aspects:
        aspect["review_warning"] = f"未通过审核，已达最大修订轮数({cfg.splitter_review_max_rounds})"
    return aspects
```

---

### 3.2 审核 Agent（新增，在 `requirement_splitter.py` 内）

**输入**：原始需求文本 + 候选方面列表

**评价维度**：

| 维度 | 检查内容 |
|---|---|
| 溯源合法性 | source_phrase 是否确实存在于原文中 |
| 推断合理性 | direct_implication 是否是工程共识而非个人推测 |
| 完整性 | 原文明确提到的方面是否都被覆盖 |
| 无冗余 | 是否存在重复或高度重叠的条目 |
| 检索可用性 | text 字段是否足够具体，能有效检索 |

**输出格式**：

```json
{
  "passed": false,
  "aspect_evaluations": [
    {
      "aspect_name": "倾斜工况适应性",
      "valid": false,
      "issue": "source_phrase '倾斜工况' 不存在于原文，属于超出范围添加"
    },
    {
      "aspect_name": "温度控制范围",
      "valid": true
    }
  ],
  "missing_aspects": [
    "停机后冷却 — 原文明确提到'停机后冷却等工况'但未生成对应子需求"
  ],
  "overall_feedback": "删除'倾斜工况适应性'；补充'停机后冷却'方面"
}
```

**通过条件**：所有 `aspect_evaluations` 均为 `valid=true`，且 `missing_aspects` 为空。

---

### 3.3 `compact_requirement_context()` 变化

从 validated sub_requirements 提取允许方面，追加到 context：

```python
allowed_aspects = [
    {
        "topic": sub.get("topic", ""),
        "source_phrase": sub.get("source_phrase", ""),
        "implication_type": sub.get("implication_type", "explicit"),
    }
    for sub in requirement_context.get("sub_requirements", []) or []
    if sub.get("source_phrase")   # 只传有溯源的方面
]
```

context 新增字段：

```json
{
  "allowed_engineering_aspects": [
    {"topic": "温度控制范围",  "source_phrase": "温度...控制范围",    "implication_type": "explicit"},
    {"topic": "冷却水泵冗余", "source_phrase": "稳定可靠的冷却能力", "implication_type": "direct_implication"},
    {"topic": "停机后冷却",   "source_phrase": "停机后冷却等工况",   "implication_type": "explicit"}
  ],
  "sub_requirements_hidden_from_generation": true
}
```

`sub_requirements_hidden_from_generation` 保持 `true`，避免 Agent 受子需求文字干扰而复制。

---

### 3.4 Agent Prompt 新增【F】范围约束节

插入位置：现有【A】数值安全规则之前（最高优先级）。

```
## 【F】范围约束（最高优先级，凌驾于其他所有规则）

### F1 允许方面列表
输入中 allowed_engineering_aspects 列出了本次可以生成工程需求的全部工程方面。
每条方面包含 topic（方面名）、source_phrase（原始需求中对应的词句）、
implication_type（explicit 或 direct_implication）。

### F2 生成规则
- engineering_requirements 必须且只能覆盖 allowed_engineering_aspects 中列出的方面
- 每条 engineering_requirement 的 topic 字段必须与 allowed_engineering_aspects 中的
  topic 值**完全一致**（逐字复用，不得改写），以便系统自动校验
- 每条 engineering_requirement 在 engineering_rationale 中必须写明：
  "本条覆盖方面【topic】，来自原始需求「source_phrase」"
- 若有证据涉及 allowed_engineering_aspects 之外的方面，记录在 evidence_gaps，
  不得生成对应的 engineering_requirements 条目

### F3 禁止行为
✗ 添加 allowed_engineering_aspects 中未列出的任何工程方面
✗ 以"工程完整性"或"证据支撑"为由扩展范围
✗ 将 evidence_gaps 中发现的问题转化为 engineering_requirements 条目
```

---

### 3.5 `normalize_agent_output()` 兜底校验

在现有校验逻辑后追加：

```python
# 范围校验：engineering_requirement 的 topic 必须精确匹配 allowed_aspects 中的某个 topic
# Agent prompt F2 要求逐字复用 topic，因此精确匹配是可靠的
allowed_topics = {a["topic"] for a in context.get("allowed_engineering_aspects", [])}
if allowed_topics:
    for req in obj["engineering_requirements"]:
        topic = req.get("topic", "")
        if topic and topic not in allowed_topics:
            req["scope_violation"] = True
            req["scope_violation_reason"] = f"topic '{topic}' 不在 allowed_engineering_aspects 列表中"
            # 移入 evidence_gaps 而非直接删除（保留可审查性）
            obj.setdefault("evidence_gaps", []).append({
                "related_requirement_id": req.get("id", ""),
                "gap_type": "scope_violation",
                "description": req["scope_violation_reason"],
                "suggested_document_update": "若确需覆盖该方面，请在原始需求中补充相关内容。"
            })
    obj["engineering_requirements"] = [
        r for r in obj["engineering_requirements"] if not r.get("scope_violation")
    ]
```

---

### 3.6 `config.py` 变化

新增一个配置项（DeepSeek 配置组内）：

```python
splitter_review_max_rounds: int = 3
```

---

## 四、改动范围汇总

| 文件 | 改动内容 | 接口变化 |
|---|---|---|
| `requirement_splitter.py` | 新 prompt + 输出增加两字段 + 审核 Agent + 修订循环 | 无（调用方无感知） |
| `engineering_requirement_agent.py` | Agent prompt 新增【F】节 + `normalize_agent_output()` 兜底校验 | 无 |
| `compact_requirement_context()` | 追加 `allowed_engineering_aspects` 字段 | 仅新增字段 |
| `config.py` | 新增 `splitter_review_max_rounds` | 新增配置项 |
| `pipeline.py` | **不改动** | — |
| 检索引擎 | **不改动** | — |

---

## 五、关键不变量

- 审核循环对 `pipeline.py` 完全透明，`PipelineServices` 接口不变
- 子需求的检索格式（`sub_requirement_id`、`requirement_type`、`text`）不变，检索引擎不需要感知新字段
- `scope_violation` 的条目移入 `evidence_gaps` 而非静默删除，保留人工审查能力
- `review_warning` 标记达到上限时的降级情况，不阻断流程
