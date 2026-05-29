# Grounding Score 基础设施 + 动作 A 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 接入 Qwen/文心两个独立 LLM 后端，并实现"证据-需求语义契合度（grounding score）"指标，在现有 T=0 batch 的 G2/G3/G4 上横向对比，判定"多粒度检索是否提供更对口证据"这一原始命题成立或证伪。

**Architecture:** 新增一个领域无关的 `cooling_rag_mg/grounding.py` 模块（证据文本查找、ER 提取、reranker 客观分、LLM 蕴含分、聚合、配对统计），由 `scripts/40_grounding_score.py` CLI 驱动，读取已有 batch 结果 → 输出 `grounding_score.json` + LaTeX 表。后端配置扩展 `config.py`。每条有证据的 ER 取 `(shall, evidence_text)` 对算两种分（reranker + LLM），per-ER 均值聚合，再按 `source_requirement_id` 聚合后做 G2 vs G3 配对检验。

**Tech Stack:** Python 3.11、sentence-transformers（CrossEncoder 加载 bge-reranker-v2-m3）、openai SDK（Qwen/文心 OpenAI 兼容接口）、scipy/numpy（Wilcoxon + bootstrap）、pytest、diskcache（复用现有 `llm_cache`）。

---

## 前置准备（执行任何 Task 前完成一次）

- [ ] **P1：确认 `.env` 含三套后端凭证**（DeepSeek 已有；Qwen/文心本次新增）

`.env` 应包含（值已由用户提供，勿写入代码/spec/plan）：
```
DEEPSEEK_API_KEY=...
QWEN_API_KEY=...
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
ERNIE_API_KEY=...
ERNIE_BASE_URL=https://qianfan.baidubce.com/v2
```

- [ ] **P2：下载 reranker 模型**（约 568 MB，一次性）

Run（Windows conda 环境）：
```bat
D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe -c "from sentence_transformers import CrossEncoder; CrossEncoder('BAAI/bge-reranker-v2-m3')"
```
Expected: 模型下载到 HuggingFace 缓存，无报错。若离线，先手动下载到本地路径并在 Task 5 用本地路径替换。

> 说明：所有 `python` 命令均指 `D:\Users\yando\miniconda3\envs\cooling_rag_env\python.exe`（项目唯一环境）。下文为简洁写作 `python`。

---

## File Structure

| 文件 | 责任 |
|---|---|
| `cooling_rag_mg/config.py`（修改） | 新增 `QwenConfig`、`ErnieConfig`，挂到 `AppConfig` |
| `cooling_rag_mg/grounding.py`（新建） | grounding score 全部核心逻辑：证据查找 / ER 提取 / reranker / LLM 蕴含 / 聚合 / 配对统计 |
| `scripts/40_grounding_score.py`（新建） | CLI：读 batch → 算分 → 输出 json + LaTeX |
| `tests/test_grounding.py`（新建） | 单元测试 |

---

## Task 1: 多模型后端配置

**Files:**
- Modify: `cooling_rag_mg/config.py`（在 `DeepSeekConfig` 后、`AppConfig` 前插入两个类；修改 `AppConfig`）
- Test: `tests/test_grounding.py`

- [ ] **Step 1: 写失败测试**

```python
# tests/test_grounding.py
import os
from cooling_rag_mg.config import get_config


def test_qwen_ernie_config_present(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "sk-qwen-test")
    monkeypatch.setenv("ERNIE_API_KEY", "bce-ernie-test")
    cfg = get_config()
    assert cfg.qwen.api_key == "sk-qwen-test"
    assert cfg.qwen.model == "qwen-max"
    assert cfg.qwen.base_url.endswith("/compatible-mode/v1")
    assert cfg.qwen.enabled is True
    assert cfg.ernie.api_key == "bce-ernie-test"
    assert cfg.ernie.base_url.endswith("qianfan.baidubce.com/v2")
    assert cfg.ernie.enabled is True
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/test_grounding.py::test_qwen_ernie_config_present -v`
Expected: FAIL — `AttributeError: 'AppConfig' object has no attribute 'qwen'`

- [ ] **Step 3: 实现两个后端配置类**

在 `cooling_rag_mg/config.py` 中 `DeepSeekConfig` 类之后插入：

```python
@dataclass(frozen=True)
class QwenConfig:
    api_key: str = field(default_factory=lambda: os.getenv("QWEN_API_KEY", "").strip())
    base_url: str = field(default_factory=lambda: os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").strip())
    model: str = field(default_factory=lambda: os.getenv("QWEN_MODEL", "qwen-max"))
    temperature: float = field(default_factory=lambda: float(os.getenv("QWEN_TEMPERATURE", "0.0")))
    timeout: float = field(default_factory=lambda: float(os.getenv("QWEN_TIMEOUT", "60.0")))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def make_client(self) -> "OpenAI":
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)


@dataclass(frozen=True)
class ErnieConfig:
    api_key: str = field(default_factory=lambda: os.getenv("ERNIE_API_KEY", "").strip())
    base_url: str = field(default_factory=lambda: os.getenv("ERNIE_BASE_URL", "https://qianfan.baidubce.com/v2").strip())
    model: str = field(default_factory=lambda: os.getenv("ERNIE_MODEL", "ernie-4.5-turbo-128k"))
    temperature: float = field(default_factory=lambda: float(os.getenv("ERNIE_TEMPERATURE", "0.0")))
    timeout: float = field(default_factory=lambda: float(os.getenv("ERNIE_TIMEOUT", "60.0")))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def make_client(self) -> "OpenAI":
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
```

修改 `AppConfig`：

```python
@dataclass(frozen=True)
class AppConfig:
    paths: Paths = field(default_factory=Paths)
    model: ModelConfig = field(default_factory=ModelConfig)
    deepseek: DeepSeekConfig = field(default_factory=DeepSeekConfig)
    qwen: QwenConfig = field(default_factory=QwenConfig)
    ernie: ErnieConfig = field(default_factory=ErnieConfig)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/test_grounding.py::test_qwen_ernie_config_present -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add cooling_rag_mg/config.py tests/test_grounding.py
git commit -m "feat: add Qwen and ERNIE OpenAI-compatible backend configs"
```

---

## Task 2: API 连通冒烟测试（手动验证后端可用）

**Files:** 无新文件，纯验证。目的是在投入算分前确认 base_url/model 正确。

- [ ] **Step 1: 写临时连通脚本并运行**

Run（直接命令行验证，不进 git）：
```bash
python -c "
from cooling_rag_mg.config import get_config
cfg = get_config()
for name, c in [('qwen', cfg.qwen), ('ernie', cfg.ernie)]:
    r = c.make_client().chat.completions.create(
        model=c.model,
        messages=[{'role':'user','content':\"只回复两个字：连通\"}],
        max_tokens=10, temperature=0.0)
    print(name, '->', r.model, '|', r.choices[0].message.content)
"
```
Expected: 两行输出，各含模型返回的"连通"。

- [ ] **Step 2: 若报错，按错误调整 `.env`**

- `model not found` / `InvalidParameter`：调整 `QWEN_MODEL`（备选 `qwen-plus`）或 `ERNIE_MODEL`（备选 `ernie-3.5-8k`、`ernie-4.0-turbo-8k`）。
- `401`/`AuthenticationError`：检查 key。
- `base_url` 404：核对 P1 中的 base_url。

重跑 Step 1 直到两个后端都返回内容。**此 Task 无提交。**

---

## Task 3: 证据文本查找表

**Files:**
- Create: `cooling_rag_mg/grounding.py`
- Test: `tests/test_grounding.py`

- [ ] **Step 1: 写失败测试**

```python
# 追加到 tests/test_grounding.py
def test_load_evidence_text_map(tmp_path):
    from cooling_rag_mg.jsonl import write_jsonl
    from cooling_rag_mg.grounding import load_evidence_text_map
    p = tmp_path / "units.jsonl"
    write_jsonl(p, [
        {"id": "E-A-001", "text": "海水泵应一用一备。"},
        {"id": "E-A-002", "text": "冷却水高温报警阈值见厂家数据。"},
    ])
    m = load_evidence_text_map(p)
    assert m["E-A-001"] == "海水泵应一用一备。"
    assert m["E-A-002"].startswith("冷却水高温报警")
    assert "E-MISSING" not in m
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_grounding.py::test_load_evidence_text_map -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cooling_rag_mg.grounding'`

- [ ] **Step 3: 实现**

```python
# cooling_rag_mg/grounding.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from cooling_rag_mg.jsonl import read_jsonl


def load_evidence_text_map(units_path: str | Path) -> dict[str, str]:
    """evidence_id -> evidence text，来自 evidence_units.jsonl。"""
    return {u["id"]: (u.get("text") or "") for u in read_jsonl(units_path)}
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_grounding.py::test_load_evidence_text_map -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add cooling_rag_mg/grounding.py tests/test_grounding.py
git commit -m "feat: add evidence text lookup for grounding score"
```

---

## Task 4: 提取有证据的工程需求（ER）

**Files:**
- Modify: `cooling_rag_mg/grounding.py`
- Test: `tests/test_grounding.py`

- [ ] **Step 1: 写失败测试**

```python
def test_iter_grounded_ers():
    from cooling_rag_mg.grounding import iter_grounded_ers
    result_sets = [{
        "source_requirement_id": "P001",
        "engineering_requirements": [
            {"shall_statement": "应一用一备。", "evidence_ids": ["E-A-001"]},
            {"shall_statement": "无证据条目。", "evidence_ids": []},
            {"shall_statement": "", "evidence_ids": ["E-A-002"]},  # 空 shall 跳过
        ],
    }]
    out = list(iter_grounded_ers(result_sets))
    assert out == [("P001", "应一用一备。", ["E-A-001"])]
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_grounding.py::test_iter_grounded_ers -v`
Expected: FAIL — `ImportError: cannot import name 'iter_grounded_ers'`

- [ ] **Step 3: 实现**

追加到 `cooling_rag_mg/grounding.py`：

```python
def iter_grounded_ers(
    result_sets: list[dict[str, Any]],
) -> Iterator[tuple[str, str, list[str]]]:
    """产出 (source_requirement_id, shall_statement, evidence_ids)，仅限二者皆非空的 ER。"""
    for rs in result_sets:
        src = str(rs.get("source_requirement_id") or "")
        for er in rs.get("engineering_requirements") or []:
            ev = [e for e in (er.get("evidence_ids") or []) if e]
            shall = (er.get("shall_statement") or "").strip()
            if ev and shall:
                yield src, shall, ev
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_grounding.py::test_iter_grounded_ers -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add cooling_rag_mg/grounding.py tests/test_grounding.py
git commit -m "feat: extract evidence-backed ERs for grounding scoring"
```

---

## Task 5: Reranker 客观分

**Files:**
- Modify: `cooling_rag_mg/grounding.py`
- Test: `tests/test_grounding.py`

设计：`RerankerScorer` 包装 CrossEncoder；`score_er_pairs` 对一条 ER 的所有 `(shall, evidence_text)` 对打分并返回均值。测试用假 scorer 注入，避免加载真实模型。

- [ ] **Step 1: 写失败测试**

```python
def test_mean_pair_score_reranker():
    from cooling_rag_mg.grounding import mean_pair_score

    class FakeScorer:
        def score_pairs(self, pairs):
            # 返回与 pair 数等长的分数；这里用 evidence 长度模拟
            return [float(len(ev)) for _, ev in pairs]

    score = mean_pair_score(FakeScorer(), "shall x", ["aa", "aaaa"])
    assert score == 3.0  # (2 + 4) / 2
    assert mean_pair_score(FakeScorer(), "shall x", []) == 0.0
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_grounding.py::test_mean_pair_score_reranker -v`
Expected: FAIL — `ImportError: cannot import name 'mean_pair_score'`

- [ ] **Step 3: 实现 scorer 与聚合**

追加到 `cooling_rag_mg/grounding.py`：

```python
class RerankerScorer:
    """CrossEncoder 包装，输出 (query, passage) 相关性分。独立于检索所用的 BGE-M3 dense 信号。"""

    def __init__(self, model_path: str = "BAAI/bge-reranker-v2-m3", device: str = "cpu") -> None:
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_path, device=device)

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        if not pairs:
            return []
        return [float(s) for s in self.model.predict(pairs)]


def mean_pair_score(scorer: Any, shall: str, evidence_texts: list[str]) -> float:
    """一条 ER 的 grounding 分 = 其所有 (shall, evidence) 对得分的均值。"""
    pairs = [(shall, ev) for ev in evidence_texts if ev]
    if not pairs:
        return 0.0
    scores = scorer.score_pairs(pairs)
    return float(sum(scores) / len(scores)) if scores else 0.0
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_grounding.py::test_mean_pair_score_reranker -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add cooling_rag_mg/grounding.py tests/test_grounding.py
git commit -m "feat: add CrossEncoder reranker grounding scorer"
```

---

## Task 6: LLM 蕴含分（Qwen / 文心）

**Files:**
- Modify: `cooling_rag_mg/grounding.py`
- Test: `tests/test_grounding.py`

设计：`LLMEntailmentScorer` 暴露与 `RerankerScorer` 相同的 `score_pairs` 接口（返回 1.0/0.5/0.0 列表），从而可直接复用 `mean_pair_score`。复用 `llm_cache.cached_completion`。

- [ ] **Step 1: 写失败测试**

```python
def test_llm_entailment_scorer():
    from unittest.mock import MagicMock
    from cooling_rag_mg.grounding import LLMEntailmentScorer

    client = MagicMock()
    # 依次返回 support / partial / none
    contents = ['{"verdict": "support"}', '{"verdict": "partial"}', '{"verdict": "none"}']
    client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="qwen-max")
        for c in contents
    ]
    scorer = LLMEntailmentScorer(client, model="qwen-max")
    scores = scorer.score_pairs([("s", "e1"), ("s", "e2"), ("s", "e3")])
    assert scores == [1.0, 0.5, 0.0]
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_grounding.py::test_llm_entailment_scorer -v`
Expected: FAIL — `ImportError: cannot import name 'LLMEntailmentScorer'`

- [ ] **Step 3: 实现**

追加到 `cooling_rag_mg/grounding.py`：

```python
import json

_ENTAIL_PROMPT = """你是船舶冷却水系统的需求-证据核对专家。判断下面这条"证据"是否支持这条"工程需求(shall)"。
- support：证据直接给出该需求所需的参数、约束或规则依据。
- partial：证据与需求相关，但不足以直接支撑该义务。
- none：证据与需求无实质支撑关系。

工程需求(shall)：{shall}
证据：{evidence}

只输出 JSON，无解释：{{"verdict": "support" 或 "partial" 或 "none"}}"""

_VERDICT_SCORE = {"support": 1.0, "partial": 0.5, "none": 0.0}


class LLMEntailmentScorer:
    """用独立 LLM（Qwen/文心）判证据对 shall 的支持度 → 1.0/0.5/0.0。接口与 RerankerScorer 对齐。"""

    def __init__(self, client: Any, model: str, temperature: float = 0.0) -> None:
        self.client = client
        self.model = model
        self.temperature = temperature

    def _score_one(self, shall: str, evidence: str) -> float:
        from cooling_rag_mg.llm_cache import cached_completion
        try:
            resp = cached_completion(
                self.client,
                model=self.model,
                messages=[{"role": "user", "content": _ENTAIL_PROMPT.format(shall=shall, evidence=evidence)}],
                temperature=self.temperature,
                max_tokens=50,
                response_format={"type": "json_object"},
            )
            obj = json.loads(resp.choices[0].message.content or "{}")
            return _VERDICT_SCORE.get(str(obj.get("verdict", "")).strip().lower(), 0.0)
        except Exception:
            return 0.0

    def score_pairs(self, pairs: list[tuple[str, str]]) -> list[float]:
        return [self._score_one(shall, ev) for shall, ev in pairs]
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_grounding.py::test_llm_entailment_scorer -v`
Expected: PASS（注意 conftest 已自动清空缓存，mock 才会被真正调用）

- [ ] **Step 5: 提交**

```bash
git add cooling_rag_mg/grounding.py tests/test_grounding.py
git commit -m "feat: add LLM entailment grounding scorer (Qwen/ERNIE)"
```

---

## Task 7: per-ER 与 per-source-req 聚合

**Files:**
- Modify: `cooling_rag_mg/grounding.py`
- Test: `tests/test_grounding.py`

设计：`score_result_sets` 用一个 scorer 对一组 result_sets 算 per-ER 分，并按 `source_requirement_id` 聚合为 per-source-req 均值（配对检验的单位）。

- [ ] **Step 1: 写失败测试**

```python
def test_score_result_sets_aggregates_by_source():
    from cooling_rag_mg.grounding import score_result_sets

    class FakeScorer:
        def score_pairs(self, pairs):
            return [1.0 for _ in pairs]  # 全部满分

    result_sets = [{
        "source_requirement_id": "P001",
        "engineering_requirements": [
            {"shall_statement": "a", "evidence_ids": ["E1"]},
            {"shall_statement": "b", "evidence_ids": ["E2", "E3"]},
        ],
    }]
    text_map = {"E1": "t1", "E2": "t2", "E3": "t3"}
    per_src = score_result_sets(result_sets, text_map, FakeScorer())
    assert per_src == {"P001": 1.0}  # 两条 ER 均为 1.0，均值 1.0
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_grounding.py::test_score_result_sets_aggregates_by_source -v`
Expected: FAIL — `ImportError: cannot import name 'score_result_sets'`

- [ ] **Step 3: 实现**

追加到 `cooling_rag_mg/grounding.py`：

```python
def score_result_sets(
    result_sets: list[dict[str, Any]],
    text_map: dict[str, str],
    scorer: Any,
) -> dict[str, float]:
    """返回 {source_requirement_id: 该 source req 下所有有证据 ER 的 grounding 分均值}。"""
    by_src: dict[str, list[float]] = {}
    for src, shall, ev_ids in iter_grounded_ers(result_sets):
        ev_texts = [text_map.get(e, "") for e in ev_ids]
        er_score = mean_pair_score(scorer, shall, ev_texts)
        by_src.setdefault(src, []).append(er_score)
    return {src: float(sum(v) / len(v)) for src, v in by_src.items() if v}
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_grounding.py::test_score_result_sets_aggregates_by_source -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add cooling_rag_mg/grounding.py tests/test_grounding.py
git commit -m "feat: aggregate grounding scores per source requirement"
```

---

## Task 8: G2 vs G3 配对统计

**Files:**
- Modify: `cooling_rag_mg/grounding.py`
- Test: `tests/test_grounding.py`

设计：`paired_compare` 接收两个 `{key: score}` 字典（key = `(batch_id, source_req)`），在交集 key 上对齐配对，返回 mean、配对 Wilcoxon p、bootstrap 均值差 95% CI。连续值版本（区别于 `27_statistics.py` 的比例版本）。

- [ ] **Step 1: 写失败测试**

```python
def test_paired_compare():
    from cooling_rag_mg.grounding import paired_compare
    a = {"k1": 0.9, "k2": 0.8, "k3": 1.0, "only_a": 0.5}
    b = {"k1": 0.6, "k2": 0.5, "k3": 0.4, "only_b": 0.1}
    res = paired_compare(a, b)
    assert res["n_pairs"] == 3          # 仅交集 k1/k2/k3
    assert round(res["mean_a"], 3) == 0.9
    assert round(res["mean_b"], 3) == 0.5
    assert res["mean_diff"] > 0          # a 系统性高于 b
    assert "pvalue" in res and "ci_low" in res and "ci_high" in res
```

- [ ] **Step 2: 运行确认失败**

Run: `python -m pytest tests/test_grounding.py::test_paired_compare -v`
Expected: FAIL — `ImportError: cannot import name 'paired_compare'`

- [ ] **Step 3: 实现**

追加到 `cooling_rag_mg/grounding.py`：

```python
def paired_compare(
    scores_a: dict[str, float],
    scores_b: dict[str, float],
    *,
    n_boot: int = 10000,
    seed: int = 42,
) -> dict[str, float]:
    """在两个 {key: score} 的交集 key 上配对比较。返回 mean、配对 Wilcoxon p、bootstrap 均值差 CI。"""
    import numpy as np
    from scipy import stats

    keys = sorted(set(scores_a) & set(scores_b))
    a = np.array([scores_a[k] for k in keys], dtype=float)
    b = np.array([scores_b[k] for k in keys], dtype=float)
    n = len(keys)

    if n == 0:
        return {"n_pairs": 0, "mean_a": float("nan"), "mean_b": float("nan"),
                "mean_diff": float("nan"), "pvalue": float("nan"),
                "ci_low": float("nan"), "ci_high": float("nan")}

    diff = a - b
    if n < 2 or np.allclose(diff, 0.0):
        pvalue = 1.0
    else:
        pvalue = float(stats.wilcoxon(a, b, zero_method="wilcox",
                                      correction=False, alternative="two-sided").pvalue)

    rng = np.random.default_rng(seed)
    boots = np.array([rng.choice(diff, size=n, replace=True).mean() for _ in range(n_boot)])
    lo, hi = np.percentile(boots, [2.5, 97.5])

    return {
        "n_pairs": n,
        "mean_a": float(a.mean()),
        "mean_b": float(b.mean()),
        "mean_diff": float(diff.mean()),
        "pvalue": pvalue,
        "ci_low": float(lo),
        "ci_high": float(hi),
    }
```

- [ ] **Step 4: 运行确认通过**

Run: `python -m pytest tests/test_grounding.py::test_paired_compare -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add cooling_rag_mg/grounding.py tests/test_grounding.py
git commit -m "feat: add paired Wilcoxon + bootstrap CI for grounding comparison"
```

---

## Task 9: CLI 脚本 + LaTeX 输出 + 集成运行

**Files:**
- Create: `scripts/40_grounding_score.py`
- Test: 集成运行（无单元测试；逻辑已被 Task 3–8 覆盖）

设计：遍历指定 batch 的 `experiment/` 目录，对每个 batch 的 G2/G3/G4 用 reranker scorer（默认）算 per-source-req 分，key = `f"{batch_name}::{src}"` 跨 batch 合并；G2 vs G3、G2 vs G4 做 `paired_compare`；输出 `grounding_score.json` + `grounding_score_table.tex`。`--llm qwen|ernie` 可选追加 LLM 蕴含分（默认仅 reranker，省 API）。

- [ ] **Step 1: 写 CLI 脚本**

```python
# scripts/40_grounding_score.py
# -*- coding: utf-8 -*-
"""动作 A：证据-需求语义契合度（grounding score）。

读取已有 batch 的 G2/G3/G4 结果，对每条有证据的 ER 算 (shall, evidence) 契合度，
按 source_requirement_id 聚合，G2 vs G3 / G2 vs G4 配对检验。

用法：
  python scripts/40_grounding_score.py                      # reranker 分，自动找完整 batch
  python scripts/40_grounding_score.py --llm qwen           # 追加 Qwen 蕴含分
  python scripts/40_grounding_score.py --batches DIR1 DIR2  # 指定 batch
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from cooling_rag_mg.config import get_config
from cooling_rag_mg.grounding import (
    LLMEntailmentScorer, RerankerScorer, load_evidence_text_map,
    paired_compare, score_result_sets,
)


def _find_batches(search_dir: Path) -> list[Path]:
    out = []
    for exp in sorted(search_dir.glob("batch_*/experiment")):
        if (exp / "G2_results.json").exists() and (exp / "G3_results.json").exists():
            out.append(exp)
    return out


def _load_sets(exp_dir: Path, group: str) -> list:
    p = exp_dir / f"{group}_results.json"
    return json.loads(p.read_text(encoding="utf-8")).get("result_sets", []) if p.exists() else []


def _scored_by_group(exp_dirs, text_map, scorer, groups):
    """返回 {group: {f'{batch}::{src}': score}}。"""
    merged = {g: {} for g in groups}
    for exp in exp_dirs:
        batch = exp.parent.name
        for g in groups:
            per_src = score_result_sets(_load_sets(exp, g), text_map, scorer)
            for src, sc in per_src.items():
                merged[g][f"{batch}::{src}"] = sc
    return merged


def _latex(label, res) -> str:
    return (f"{label} & {res['mean_a']:.3f} & {res['mean_b']:.3f} & "
            f"{res['mean_diff']:+.3f} & [{res['ci_low']:+.3f}, {res['ci_high']:+.3f}] & "
            f"{res['pvalue']:.3f} \\\\")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batches", nargs="*", help="experiment 目录；缺省自动找完整 batch")
    ap.add_argument("--llm", choices=["qwen", "ernie"], help="追加 LLM 蕴含分（默认仅 reranker）")
    args = ap.parse_args()

    cfg = get_config()
    text_map = load_evidence_text_map(cfg.paths.evidence_units_jsonl)

    exp_dirs = [Path(b) for b in args.batches] if args.batches else _find_batches(cfg.paths.search_results_dir)
    if not exp_dirs:
        print("未找到含 G2/G3 的 batch。先运行 scripts/26_run_three_rounds.py。")
        sys.exit(1)
    print(f"[grounding] {len(exp_dirs)} 个 batch")

    groups = ["G2", "G3", "G4"]
    scorers = {"reranker": RerankerScorer(device=cfg.model.device)}
    if args.llm:
        c = cfg.qwen if args.llm == "qwen" else cfg.ernie
        if not c.enabled:
            print(f"{args.llm} 未配置 API key（.env）。"); sys.exit(1)
        scorers[args.llm] = LLMEntailmentScorer(c.make_client(), model=c.model, temperature=c.temperature)

    out: dict = {"batches": [e.parent.name for e in exp_dirs], "scorers": {}}
    latex_lines = []
    for sname, scorer in scorers.items():
        by_group = _scored_by_group(exp_dirs, text_map, scorer, groups)
        cmp_g3 = paired_compare(by_group["G2"], by_group["G3"])
        cmp_g4 = paired_compare(by_group["G2"], by_group["G4"])
        out["scorers"][sname] = {"G2_vs_G3": cmp_g3, "G2_vs_G4": cmp_g4,
                                 "group_means": {g: (sum(by_group[g].values()) / len(by_group[g])
                                                     if by_group[g] else float("nan")) for g in groups}}
        latex_lines.append(f"% {sname}")
        latex_lines.append(_latex(f"{sname} G2$\\to$G3", cmp_g3))
        latex_lines.append(_latex(f"{sname} G2$\\to$G4", cmp_g4))
        print(f"[{sname}] G2={out['scorers'][sname]['group_means']['G2']:.3f} "
              f"G3={out['scorers'][sname]['group_means']['G3']:.3f} "
              f"G2vsG3 diff={cmp_g3['mean_diff']:+.3f} p={cmp_g3['pvalue']:.3f} "
              f"CI[{cmp_g3['ci_low']:+.3f},{cmp_g3['ci_high']:+.3f}] n={cmp_g3['n_pairs']}")

    out_json = cfg.paths.search_results_dir / "grounding_score.json"
    out_json.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    out_tex = cfg.paths.search_results_dir / "grounding_score_table.tex"
    header = ("% grounding score: mean_A mean_B diff CI p\n"
              "\\begin{tabular}{lccccc}\n\\toprule\n"
              "Comparison & A & B & $\\Delta$ & 95\\% CI & $p$\\\\\n\\midrule\n")
    out_tex.write_text(header + "\n".join(latex_lines) + "\n\\bottomrule\n\\end{tabular}\n", encoding="utf-8")
    print(f"-> {out_json}\n-> {out_tex}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 集成运行（reranker，无 API 成本）**

Run: `python scripts/40_grounding_score.py`
Expected: 打印每个 scorer 的 G2/G3 均值与 G2→G3 差值/p/CI；生成 `data/search_results/grounding_score.json` 与 `grounding_score_table.tex`。**这一步的输出就是判定原始命题的关键数据。**

- [ ] **Step 3: 集成运行（追加 Qwen 蕴含分）**

Run: `python scripts/40_grounding_score.py --llm qwen`
Expected: 多打印一组 `qwen` 结果。首次运行会调 Qwen API（受 `llm_cache` 缓存）。

- [ ] **Step 4: 判读结果并记录**

- 若 **reranker 与 qwen 两个 scorer 的 G2→G3 `mean_diff` 均显著为正（p<0.05、CI 不含 0）** → 原始命题成立（spec 分支甲）。
- 若 **无显著差异** → 证伪（spec 分支乙，转 KB 覆盖瓶颈叙事）。
将结论与 `grounding_score.json` 摘要追加到 `STATUS.md`。

- [ ] **Step 5: 提交**

```bash
git add scripts/40_grounding_score.py
git commit -m "feat: add grounding-score CLI (action A) with reranker + LLM scorers"
```

---

## Self-Review 记录

- **Spec 覆盖**：本计划实现 spec 动作 A 全流程（reranker + LLM 双测法、per-ER→per-source-req 聚合、G2/G3/G4 配对检验、LaTeX 输出）+ Qwen/文心后端基础设施（B/D/F/G 后续计划依赖）。动作 B–G 不在本计划，留待 A 结果出来后分别规划。
- **判定逻辑**：Task 9 Step 4 明确 G2→G3 显著正差为"成立"，否则"证伪"，与 spec 决策留痕一致（不调参凑结果）。
- **类型一致**：`RerankerScorer` 与 `LLMEntailmentScorer` 同享 `score_pairs(pairs)->list[float]` 接口，故 `mean_pair_score`/`score_result_sets` 对两者通用；`paired_compare` 的返回键（`mean_a/mean_b/mean_diff/pvalue/ci_low/ci_high/n_pairs`）在 Task 8 定义、Task 9 `_latex` 消费，键名一致。
- **配对单位**：明确为 `(batch, source_requirement_id)`，解决 G2/G3 的 ER 不一一对应问题。
- **无占位符**：所有步骤含完整可运行代码与确切命令。reranker 模型名 `BAAI/bge-reranker-v2-m3`、API base_url/model 默认值均给出，Task 2 提供报错时的调整路径。
