# RAG 可信度证明 — 实现计划（含进度日志）

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans（本 /loop 内联执行）。每个 step 用 `- [ ]` 复选框跟踪；**完成一项就勾选并 commit**，保证断网后可从未勾选项继续。
> **可微调**：若某 step 执行结果证伪了上游假设（如 Phase 1 数据质量不达标、裁判一致性过低），停下、在「## 微调记录」区登记、调整后续 step 再继续。

**Goal:** 证明「据检索证据生成的工程需求」比「无检索据子需求直接生成」在统一 KB 真值下幻觉/过推断更低。

**Architecture:** 多智能体跨厂商分工（ERNIE 出题 / DeepSeek 拆分 / Qwen 据证据生成 / ERNIE+DeepSeek+reranker+人工裁判）。复用现有三粒度检索与 `grounding.py`；新增证据优先生成与公平可信度评估层。头条 = 配对子集单变量比较（同子需求，唯一差别=上下文有无检索证据）。

**Tech Stack:** Python, OpenAI SDK（DeepSeek/Qwen/ERNIE 兼容端点）, sentence-transformers（BGE-reranker-v2-m3）, scipy/numpy, pytest。

**Spec:** `docs/superpowers/specs/2026-05-30-rag-credibility-replan-design.md`

---

## 进度状态（断网后先读这里）

- [ ] Phase 1 数据集：ERNIE 原始需求 + DeepSeek 拆分（冻结 v1）
- [ ] Phase 2 评估层：claim 抽取 + KB 回溯判定（H_hard/H_soft/OI）+ 多裁判 + 人工校准
- [ ] Phase 3 生成改造：证据优先生成（Qwen），B0/R 两产线
- [ ] Phase 4 主实验：B0 vs R，配对子集 + 端到端率
- [ ] Phase 5 消融：A1/A2/A3
- [ ] Phase 6 论文：重写叙事

当前游标：**Phase 2 / Task 2.1**（Phase 1 Task 1.1/1.2/1.3 ✅；Task 1.4 拆分待用户对数据集放行后再花费 DeepSeek）

> 已完成：1.1 prompt 构造/解析（3 测试）、1.2 KB 查重（4 测试）、1.3 冻结 60 条原始需求 v1（commit）。
> **Task 1.4 共享拆分**需 ~60 次 DeepSeek 调用，依赖 v1 数据集——等用户对 60 条做质量放行后执行。
> 与此并行：**Phase 2 评估层（Task 2.1–2.5）为纯代码、零 API、不依赖数据集**，可先推进（思路干净正确的核心）。
> 运行环境：WSL 下用 `/mnt/d/Users/yando/miniconda3/envs/cooling_rag_env/python.exe`（`python` 不在 PATH）。

---

## File Structure（新增/改动）

| 文件 | 职责 | 状态 |
|---|---|---|
| `cooling_rag_mg/original_requirements.py` | ERNIE 原始需求 prompt 构造 + 解析 + 质量校验（纯逻辑，可 TDD） | 新增 |
| `scripts/41_generate_original_requirements.py` | 调 ERNIE 生成 N≥60 条原始需求 → 冻结 jsonl | 新增 |
| `scripts/42_split_requirements.py` | 调 DeepSeek 拆分冻结原始需求 → 共享拆分 jsonl | 新增 |
| `cooling_rag_mg/credibility_eval.py` | claim 抽取 / KB 回溯判定 / H_hard·H_soft·OI / 聚合 | 新增 |
| `scripts/43_credibility_eval.py` | 跑评估层，多裁判 + reranker，出结果 + 人工校准抽样 | 新增 |
| `cooling_rag_mg/evidence_first_generator.py` | 证据优先生成（Qwen）；B0/R 共用 prompt，仅证据块差异 | 新增（Phase 3） |
| `scripts/44_run_b0_r.py` | 据共享拆分跑 B0 与 R 两产线 | 新增（Phase 3） |
| `tests/test_original_requirements.py` | Phase 1 单测 | 新增 |
| `tests/test_credibility_eval.py` | Phase 2 单测 | 新增 |

**数据产物**（冻结、版本化，进 git）：
- `data/processed/original_requirements_v1.jsonl` — ERNIE 原始需求池
- `data/processed/split_requirements_v1.jsonl` — DeepSeek 共享拆分

---

## Phase 1 — 数据集

### Task 1.1：原始需求 prompt 构造 + 解析（纯逻辑，无 API）

**Files:**
- Create: `cooling_rag_mg/original_requirements.py`
- Test: `tests/test_original_requirements.py`

- [ ] **Step 1：写失败测试** — `tests/test_original_requirements.py`

```python
def test_build_generation_prompt_has_constraints():
    from cooling_rag_mg.original_requirements import build_generation_prompt
    p = build_generation_prompt(n=5, seed_topics=["海水泵冗余", "高温报警"])
    # 关键约束必须在 prompt 里
    assert "不得照抄" in p or "不得复制" in p          # 防 KB 污染
    assert "高层" in p or "运行需要" in p               # 高层运行需要，非工程细节
    assert "5" in p                                     # 数量
    assert "海水泵冗余" in p                            # 主题注入

def test_parse_generated_requirements_assigns_ids():
    from cooling_rag_mg.original_requirements import parse_generated
    raw = '{"requirements":[{"stakeholder":"轮机长","requirement_text":"冷却系统应在单点故障下维持运行。"},{"stakeholder":"船东","requirement_text":"海水温升应可监测。"}]}'
    out = parse_generated(raw, start_index=1, prefix="OR")
    assert out[0]["requirement_id"] == "OR001"
    assert out[1]["requirement_id"] == "OR002"
    assert out[0]["stakeholder"] == "轮机长"
    assert out[0]["requirement_text"].startswith("冷却系统")

def test_parse_generated_skips_empty_text():
    from cooling_rag_mg.original_requirements import parse_generated
    raw = '{"requirements":[{"stakeholder":"x","requirement_text":"  "},{"stakeholder":"y","requirement_text":"有效需求文本。"}]}'
    out = parse_generated(raw, start_index=1, prefix="OR")
    assert len(out) == 1
    assert out[0]["requirement_id"] == "OR001"
```

- [ ] **Step 2：运行测试，确认失败**

Run: `python -m pytest tests/test_original_requirements.py -v`
Expected: FAIL（模块不存在 / ImportError）

- [ ] **Step 3：最小实现** — `cooling_rag_mg/original_requirements.py`

```python
from __future__ import annotations
import json
from typing import Any

_GEN_SYSTEM = """你是船舶主机冷却水系统的资深需求工程师。请生成 {n} 条**高层运行需要**层级的原始干系人需求。
要求：
- 每条是利益相关方的**运行/性能需要**（高层），不是工程实现细节、不含具体数字阈值。
- 语言自然、贴近真实船东/轮机长/船检的口吻，难度与主题要有多样性。
- **不得照抄/复制**任何标准条文或证据库原文，只写需要、不写规范出处。
- 覆盖参考主题（可发散）：{topics}

只输出 JSON：{{"requirements":[{{"stakeholder":"...","requirement_text":"..."}}, ...]}}"""

def build_generation_prompt(n: int, seed_topics: list[str]) -> str:
    return _GEN_SYSTEM.format(n=n, topics="、".join(seed_topics))

def parse_generated(raw: str, start_index: int, prefix: str = "OR") -> list[dict[str, Any]]:
    data = json.loads(raw or "{}")
    out: list[dict[str, Any]] = []
    idx = start_index
    for item in data.get("requirements", []):
        text = (item.get("requirement_text") or "").strip()
        if not text:
            continue
        out.append({
            "requirement_id": f"{prefix}{idx:03d}",
            "stakeholder": (item.get("stakeholder") or "").strip(),
            "requirement_text": text,
        })
        idx += 1
    return out
```

- [ ] **Step 4：运行测试，确认通过**

Run: `python -m pytest tests/test_original_requirements.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5：commit**

```bash
git add cooling_rag_mg/original_requirements.py tests/test_original_requirements.py
git commit -m "feat: 原始需求生成 prompt 构造与解析（Phase 1 Task 1.1）"
```

### Task 1.2：质量校验（防 KB 污染、查重）

**Files:** Modify: `cooling_rag_mg/original_requirements.py`；Test: `tests/test_original_requirements.py`

- [ ] **Step 1：写失败测试**

```python
def test_quality_filter_flags_kb_copy():
    from cooling_rag_mg.original_requirements import quality_check
    kb_texts = ["海水泵应一用一备，备用泵能自动投入。"]
    reqs = [
        {"requirement_id": "OR001", "requirement_text": "海水泵应一用一备，备用泵能自动投入。"},  # 近似照抄
        {"requirement_id": "OR002", "requirement_text": "冷却系统应在单点故障下维持必要冷却能力。"},  # 高层、OK
    ]
    report = quality_check(reqs, kb_texts, sim_threshold=0.8)
    flagged = {r["requirement_id"]: r for r in report}
    assert flagged["OR001"]["kb_copy_suspect"] is True
    assert flagged["OR002"]["kb_copy_suspect"] is False
```

- [ ] **Step 2：运行，确认失败**

Run: `python -m pytest tests/test_original_requirements.py::test_quality_filter_flags_kb_copy -v`
Expected: FAIL

- [ ] **Step 3：最小实现**（用字符 n-gram Jaccard 做轻量查重，零依赖）

```python
def _char_ngrams(s: str, n: int = 4) -> set[str]:
    s = "".join(s.split())
    return {s[i:i+n] for i in range(max(len(s) - n + 1, 0))} or {s}

def _jaccard(a: str, b: str) -> float:
    A, B = _char_ngrams(a), _char_ngrams(b)
    return len(A & B) / len(A | B) if (A | B) else 0.0

def quality_check(reqs: list[dict], kb_texts: list[str], sim_threshold: float = 0.8) -> list[dict]:
    out = []
    for r in reqs:
        text = r.get("requirement_text", "")
        max_sim = max((_jaccard(text, k) for k in kb_texts), default=0.0)
        out.append({
            "requirement_id": r["requirement_id"],
            "max_kb_similarity": round(max_sim, 3),
            "kb_copy_suspect": max_sim >= sim_threshold,
        })
    return out
```

- [ ] **Step 4：运行，确认通过**

Run: `python -m pytest tests/test_original_requirements.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5：commit**

```bash
git add cooling_rag_mg/original_requirements.py tests/test_original_requirements.py
git commit -m "feat: 原始需求质量校验/KB查重（Phase 1 Task 1.2）"
```

### Task 1.3：生成脚本（调 ERNIE，冻结产物）— **需 ERNIE API，花费检查点**

**Files:** Create: `scripts/41_generate_original_requirements.py`

- [ ] **Step 1：实现脚本**（要点：`cfg.ernie.make_client()`；分批生成至 ≥60 条去重；跑 `quality_check` 对 `evidence_units.jsonl` 文本；剔除 `kb_copy_suspect`；写 `data/processed/original_requirements_v1.jsonl`；打印质量报告摘要）。脚本顶部 `sys.path.insert(0, PROJECT_ROOT)`，沿用 `scripts/40` 的样式。
- [ ] **Step 2：⚠️执行前在 loop 里报告**：将调用 ERNIE ~若干次（花费）。运行：
  `python scripts/41_generate_original_requirements.py --n 60`
  Expected: 生成 ≥60 条，0 条 `kb_copy_suspect` 残留，产物落盘。
- [ ] **Step 3：人工/抽样核查**质量（多样性、是否高层、无照抄）。不达标→记入「微调记录」，调 prompt 重跑。
- [ ] **Step 4：commit 冻结产物**

```bash
git add scripts/41_generate_original_requirements.py data/processed/original_requirements_v1.jsonl
git commit -m "data: 冻结 ERNIE 原始需求池 v1（Phase 1 Task 1.3）"
```

### Task 1.4：共享拆分脚本（调 DeepSeek）— **需 DeepSeek API**

**Files:** Create: `scripts/42_split_requirements.py`

- [ ] **Step 1：实现**：读 `original_requirements_v1.jsonl`，对每条用现有 `requirement_splitter.py`（DeepSeek）拆分，写 `data/processed/split_requirements_v1.jsonl`：每行 `{"source_requirement_id","stakeholder","requirement_text","sub_requirements":[{"sub_requirement_id","requirement_type","topic","text",...}]}`。**两组共用此产物**。
- [ ] **Step 2：运行** `python scripts/42_split_requirements.py`，Expected：每条 1–4 子需求，落盘。
- [ ] **Step 3：commit**

```bash
git add scripts/42_split_requirements.py data/processed/split_requirements_v1.jsonl
git commit -m "data: 冻结共享子需求拆分 v1（Phase 1 Task 1.4）"
```

- [ ] **Phase 1 完成**：勾选顶部「进度状态」Phase 1，游标移到 Phase 2 / Task 2.1。

---

## Phase 2 — 评估层（公平可信度，破循环）

裁判判定枚举统一为 `"support" | "contradict" | "not_found"`。H_hard=contradict 占比；H_soft=not_found 占比；总幻觉=两者之和。

### Task 2.1：claim 抽取（LLM，可 mock TDD）

**Files:** Create: `cooling_rag_mg/credibility_eval.py`；Test: `tests/test_credibility_eval.py`

- [ ] **Step 1：写失败测试**

```python
from unittest.mock import MagicMock

def _resp(content):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))], model="m")

def test_extract_claims_parses_list():
    from cooling_rag_mg.credibility_eval import extract_claims
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"claims":["海水泵应一用一备","备用泵应能自动投入"]}')
    ]
    claims = extract_claims("海水泵应一用一备且备用泵自动投入。", client, model="m")
    assert claims == ["海水泵应一用一备", "备用泵应能自动投入"]

def test_extract_claims_empty_on_failure():
    from cooling_rag_mg.credibility_eval import extract_claims
    client = MagicMock()
    client.chat.completions.create.side_effect = [Exception("boom")]
    assert extract_claims("x", client, model="m") == []
```

- [ ] **Step 2：运行，确认失败** — `python -m pytest tests/test_credibility_eval.py -v` → FAIL
- [ ] **Step 3：最小实现**（`credibility_eval.py` 顶部）

```python
from __future__ import annotations
import json
from typing import Any

_CLAIM_PROMPT = """从下面这条工程需求(shall)中抽取所有**原子事实性 claim**（具体参数、阈值、标准引用、设计规则）。
不要抽取空泛的意图。只输出 JSON：{{"claims":["...", ...]}}
工程需求：{shall}"""

def extract_claims(shall: str, client: Any, model: str, temperature: float = 0.0) -> list[str]:
    from cooling_rag_mg.llm_cache import cached_completion
    try:
        resp = cached_completion(
            client, model=model,
            messages=[{"role": "user", "content": _CLAIM_PROMPT.format(shall=shall)}],
            temperature=temperature, max_tokens=400,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content
        claims = json.loads(content or "{}").get("claims", [])
        return [str(c).strip() for c in claims if str(c).strip()]
    except Exception:
        return []
```

- [ ] **Step 4：运行，确认通过** → PASS（2 passed）
- [ ] **Step 5：commit**

```bash
git add cooling_rag_mg/credibility_eval.py tests/test_credibility_eval.py
git commit -m "feat: claim 抽取（Phase 2 Task 2.1）"
```

### Task 2.2：单条 claim 的 KB 回溯判定

**Files:** Modify: `cooling_rag_mg/credibility_eval.py`；Test: `tests/test_credibility_eval.py`

- [ ] **Step 1：写失败测试**

```python
def test_verify_claim_verdicts():
    from cooling_rag_mg.credibility_eval import verify_claim_against_kb
    # kb_search: claim -> 返回若干 KB 段落文本
    def kb_search(q, k):
        return ["海水泵应一用一备，备用泵自动投入。"]
    # judge: (claim, passages) -> verdict
    def judge(claim, passages):
        return "support" if "一用一备" in claim else "not_found"
    assert verify_claim_against_kb("海水泵一用一备", kb_search, judge, top_k=3) == "support"
    assert verify_claim_against_kb("冷却水流量≥999 m3/h", kb_search, judge, top_k=3) == "not_found"

def test_verify_claim_no_passage_is_not_found():
    from cooling_rag_mg.credibility_eval import verify_claim_against_kb
    assert verify_claim_against_kb("任意", lambda q, k: [], lambda c, p: "support", top_k=3) == "not_found"
```

- [ ] **Step 2：运行，确认失败** → FAIL
- [ ] **Step 3：最小实现**

```python
def verify_claim_against_kb(claim: str, kb_search, judge, top_k: int = 5) -> str:
    """返回 'support' | 'contradict' | 'not_found'。无召回段落 → not_found。"""
    passages = kb_search(claim, top_k)
    if not passages:
        return "not_found"
    verdict = judge(claim, passages)
    return verdict if verdict in {"support", "contradict", "not_found"} else "not_found"
```

- [ ] **Step 4：运行，确认通过** → PASS
- [ ] **Step 5：commit**

```bash
git add cooling_rag_mg/credibility_eval.py tests/test_credibility_eval.py
git commit -m "feat: claim KB 回溯判定（Phase 2 Task 2.2）"
```

### Task 2.3：单条 shall 的 H_hard / H_soft / OI 打分

**Files:** Modify: `cooling_rag_mg/credibility_eval.py`；Test: `tests/test_credibility_eval.py`

- [ ] **Step 1：写失败测试**

```python
def test_score_shall_hard_soft():
    from cooling_rag_mg.credibility_eval import score_shall
    # 三个 claim：一个 support、一个 contradict、一个 not_found
    verdicts = {"c1": "support", "c2": "contradict", "c3": "not_found"}
    out = score_shall(
        shall="s",
        extract=lambda s: ["c1", "c2", "c3"],
        verify=lambda c: verdicts[c],
    )
    assert out["n_claims"] == 3
    assert out["h_hard"] == 1/3      # contradict
    assert out["h_soft"] == 1/3      # not_found
    assert out["hallucination"] == 2/3

def test_score_shall_no_claims_returns_none():
    from cooling_rag_mg.credibility_eval import score_shall
    out = score_shall(shall="s", extract=lambda s: [], verify=lambda c: "support")
    assert out["n_claims"] == 0
    assert out["h_hard"] is None and out["h_soft"] is None
```

- [ ] **Step 2：运行，确认失败** → FAIL
- [ ] **Step 3：最小实现**

```python
def score_shall(shall: str, extract, verify) -> dict:
    """extract: shall->list[claim]; verify: claim->verdict。
    无 claim → 比率为 None（该 shall 不计入幻觉率均值）。"""
    claims = extract(shall)
    n = len(claims)
    if n == 0:
        return {"n_claims": 0, "h_hard": None, "h_soft": None, "hallucination": None}
    verdicts = [verify(c) for c in claims]
    hard = sum(1 for v in verdicts if v == "contradict") / n
    soft = sum(1 for v in verdicts if v == "not_found") / n
    return {"n_claims": n, "h_hard": hard, "h_soft": soft, "hallucination": hard + soft}
```

- [ ] **Step 4：运行，确认通过** → PASS
- [ ] **Step 5：commit**

```bash
git add cooling_rag_mg/credibility_eval.py tests/test_credibility_eval.py
git commit -m "feat: shall 级 H_hard/H_soft 打分（Phase 2 Task 2.3）"
```

### Task 2.4：OI 过推断判定（与 H 区分）

- [ ] OI 判定：裁判判 shall 是否「超出原始需求+KB 授权范围、凭空加义务」。新增 `judge_over_inference(shall, source_requirement, kb_passages, client, model) -> bool`。写 mock 测试（over=True/False 两例）→ 实现 → commit。（与 Task 2.1 同款 LLM 调用模式，prompt 聚焦「范围蔓延」而非事实错。）

### Task 2.5：按 source_requirement 聚合 + 配对子集比较

- [ ] 新增 `aggregate_by_source(per_shall_rows) -> {src: {h_hard_mean, h_soft_mean, oi_rate, ...}}`，对 None 比率剔除后取均值；**配对子集** = R 产出 shall 的子需求集合上 B0/R 对齐。复用 `grounding.paired_compare` 做 Wilcoxon+bootstrap。写测试（含 None 剔除、伪重复去重按 src 均值）→ 实现 → commit。

### Task 2.6：评估脚本 + 多裁判 + 人工校准抽样 — **需 API**

**Files:** Create: `scripts/43_credibility_eval.py`

- [ ] kb_search 用现有 evidence_units 索引（`index_store` / `HybridIndexSearcher`，大 top_k 兜底软幻觉）。judge 用 NLI 式 LLM（ERNIE + DeepSeek 双裁判，跨生成者 Qwen），reranker 给 G 契合度。
- [ ] 跨裁判一致性（多数投票 + 报 κ）。
- [ ] **人工校准**：抽 ~50 条 claim 导出 `data/search_results/credibility_calibration_sample.csv`（claim、召回段落、各裁判 verdict、空白人工列），供人工裁定后回读比对。
- [ ] 产物 `data/search_results/credibility_eval.json`。运行前在 loop 报告花费。
- [ ] commit 脚本（产物视体量决定是否进 git）。

- [ ] **Phase 2 完成**：勾选顶部 Phase 2，游标移到 Phase 3。

---

## Phase 3 — 生成改造（证据优先）·路线图（待 Phase 1/2 产物就绪后细化为 TDD task）

**目标**：`cooling_rag_mg/evidence_first_generator.py` — Qwen 生成；B0 与 R **共用基础 prompt**（同模型/温度/格式/「无依据不得编造数字」安全条款），唯一差别：R 上下文注入检索证据块 + 「以证据为唯一事实源、未覆盖参数不得编造」；B0 无证据块。R 对**无证据子需求弃权**（记入 Cov）。`scripts/44_run_b0_r.py` 据 `split_requirements_v1.jsonl` 跑两产线，落盘 `B0_results.json` / `R_results.json`（沿用 result_sets 结构以复用评估层）。
**细化时机**：Phase 1/2 完成、确认评估层判定可靠后，把本节展开为 Task 3.1–3.x（prompt 构造测试、弃权逻辑测试、两产线脚本）。

## Phase 4 — 主实验 · 路线图
对 B0/R 跑 Phase 2 评估层：出 H_hard/H_soft/OI/G/Rel/Cov；**头条 = 配对子集**（R 产出的子需求上 B0 对齐）+ 端到端率作补充；人工校准核验裁判无偏。落 `data/search_results/main_experiment/`。

## Phase 5 — 消融 · 路线图
A1（仅扁平单粒度）/A2（关 ranker）/A3（关 profile），均走「据证据生成」，与 R 同评估层比较。如实纳入既有 grounding 结论（扁平≥多粒度逐条契合度）。

## Phase 6 — 论文 · 路线图
重写 `paper/paper.tex` 叙事：头条「RAG 证据约束降幻觉、提工程可信度」；多粒度/ranker/profile 进消融与讨论；更新 STATUS.md 与 memory。

---

## 微调记录（执行中发现问题就追加）

### 2026-05-30 · Task 1.3 首跑只得 36 条（目标 60）
- **现象**：ERNIE 生成 batch 6–19 累计去重后始终 36 条，零新增；部分 batch JSON 截断（`Expecting ',' delimiter`）。
- **根因**：(1) 用了 `cached_completion`——相同 prompt 命中缓存返回同一批，去重后全丢；缓存是为可复现打分设计，不适合多样性采样。(2) `max_tokens=2000` 对 12 条详细需求不够，JSON 被截断。
- **质量结论**：已得 36 条内容合格（高层需要、stakeholder 多样、最大 KB 相似度 0.022），不弃，作为种子。
- **微调**：生成阶段**直连 client（不走缓存）**；加「不要与已有需求重复」反重复后缀；batch-size→10、max_tokens→3000。改完重跑补足到 ≥60。
