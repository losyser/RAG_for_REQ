# RAG vs no-RAG 工程需求质量与可靠性 — 实现计划（含进度日志）

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans（内联执行）。每个 step 用 `- [ ]` 跟踪；**完成一项就勾选并 commit**，断网可从未勾选项续作。执行中若结果证伪上游假设，停下登记「微调记录」再调整。

**Goal:** 证明 RAG 转化路径（Kimi 检索内容→覆盖检索→DeepSeek 据证据生成）比 no-RAG（DeepSeek 强基线直接生成）产出质量更高、更可靠的工程需求。

**Architecture:** 四模型跨厂商（ERNIE 出题 / Kimi 检索内容 / DeepSeek 两组生成 / Qwen 裁判）。复用冻结 60 原始需求与 `credibility_eval.py` 可靠性逻辑；新增 Kimi 查询生成、覆盖优先检索、两条生成产线、盲评质量裁判。

**Tech Stack:** Python, OpenAI SDK（DeepSeek/Qwen/ERNIE/Kimi 兼容端点）, BGE-M3 + FAISS + BM25, scipy/numpy, pytest。

**Spec:** `docs/superpowers/specs/2026-05-30-rag-vs-norag-quality-design.md`
**运行环境:** WSL 下用 `/mnt/d/Users/yando/miniconda3/envs/cooling_rag_env/python.exe`（`python` 不在 PATH）。

---

## 进度状态（断网后先读这里）

- [x] Task 1 KimiConfig（config.py + 测试）
- [x] Task 2 Kimi 检索内容生成（retrieval_query_gen.py）
- [x] Task 3 覆盖优先检索（coverage_retrieval.py）
- [x] Task 4 no-RAG 强基线 + RAG 据证据生成（req_generation_v2.py）
- [x] Task 5 盲评质量裁判（quality_judge.py，左右交换）
- [x] Task 6 两条产线脚本（scripts/45）+ 跑数 ← 全量 60 源已跑完并 commit（ba67878）
- [x] Task 7 评估脚本（scripts/46 + quality_eval.py）+ 全量跑 ← 代码 90a2582 / 数据 2517381，73 测试绿
- [ ] Task 8 消融（去 Kimi / 覆盖vs精准）+ 论文叙事 ← **暂缓,待用户对 Task 7 结果拍方向**

当前游标：**等用户定论**（Task 7 结果不支持原命题，见下）

### Task 7 结果与悬而未决（用户『暂时保存，思考一会』，勿擅自推进）
全量 n=60：
- H_hard 矛盾率（主）：no-RAG 0.003 vs RAG 0.002，**p=0.500 打平**。
- H_soft：0.852 vs 0.396 p<.001；OI：0.799 vs 0.153 p<.001。
- 质量盲评（配对/左右交换/跨厂商/引用不进维度）：R/B0/tie=**16/84/140，各维 no-RAG 完胜**；位置偏置降tie 36/23/24/21。
- 描述：no-RAG 325shall/0溯源/57%数字/长68；RAG 572shall/100%溯源/40%数字/长55。

**判断**：两个最抗偏置指标（H_hard、盲评质量）不支持甚至反对原命题。RAG 仅赢 OI/H_soft，**疑循环度量**（OI 要求"证据授权"，no-RAG 无证据→结构性必输；H_soft 受 KB 覆盖支配）。浮现叙事=质量-可靠性张力（方向与原设想相反）。

**待用户选方向**：①人工校准核验（CSV 已导出 exp_v2/）②接受张力叙事重构命题③修 OI 去循环重判④排查盲评冗长/具体性偏置。

### 微调记录（Task 6 全量跑）
- 首次全量跑暴露 2 类静默失败：① Kimi 偶发 ```json``` 围栏 → parse_queries 失败 → OR048 零查询零证据却凭空生成；② DeepSeek 证据多时输出 >2000 token 被截断 → parse_requirements 返回 []（OR015/OR052 有 30+ 证据却 0 ER）。
- 修复（commit fd884e4）：新增 `json_utils.loads_lenient`（剥围栏+抽首个 {} 块）；`_gen` max_tokens 2000→4000 统一全数据集（避免混杂变量）。删旧产物重跑。
- 规范产物（commit ba67878）：no-RAG 60 源 325 ER（57% shall 含数字，强基线未阉割）；RAG 60 源 572 ER（0 空源、0 零证据源、平均 32.0 证据/源、40% 含数字，据证据更保守）。

---

## File Structure（新增/改动）

| 文件 | 职责 | 状态 |
|---|---|---|
| `cooling_rag_mg/config.py` | 加 `KimiConfig`（OpenAI 兼容） | 改 |
| `cooling_rag_mg/retrieval_query_gen.py` | Kimi 由原始需求生成检索内容（关键词+中/英句）的 prompt 构造与解析 | 新 |
| `cooling_rag_mg/coverage_retrieval.py` | 多查询并集的覆盖优先检索（evidence_units 索引） | 新 |
| `cooling_rag_mg/req_generation_v2.py` | no-RAG 强基线生成 + RAG 据证据生成（消息构造+解析） | 新 |
| `cooling_rag_mg/quality_judge.py` | 盲评两两对比（左右交换、多维胜/平/负） | 新 |
| `scripts/45_run_pipelines_v2.py` | 跑 no-RAG / RAG 两产线 → `exp_v2/{norag,rag}_results.json` | 新 |
| `scripts/46_evaluate_v2.py` | 可靠性(复用 credibility_eval,裁判=Qwen)+盲评质量+描述性+校准 | 新 |
| `tests/test_retrieval_query_gen.py` / `test_coverage_retrieval.py` / `test_req_generation_v2.py` / `test_quality_judge.py` | 单测 | 新 |

**产物**：`data/search_results/exp_v2/{norag,rag}_results.json`、`quality_eval_v2.json`、`reliability_eval_v2.json`、`quality_calibration_v2.csv`。

---

## Task 1：KimiConfig

**Files:** Modify `cooling_rag_mg/config.py`；Test `tests/test_kimi_config.py`

- [ ] **Step 1：写失败测试** — `tests/test_kimi_config.py`

```python
def test_kimi_config(monkeypatch):
    monkeypatch.setenv("KIMI_API_KEY", "sk-kimi-test")
    from cooling_rag_mg.config import get_config
    cfg = get_config()
    assert cfg.kimi.api_key == "sk-kimi-test"
    assert cfg.kimi.base_url.endswith("moonshot.cn/v1")
    assert cfg.kimi.model.startswith("moonshot")
    assert cfg.kimi.enabled is True
```

- [ ] **Step 2：运行确认失败** — `python -m pytest tests/test_kimi_config.py -v` → FAIL（无 cfg.kimi）
- [ ] **Step 3：实现** — 在 `config.py` 仿 `QwenConfig` 加：

```python
@dataclass(frozen=True)
class KimiConfig:
    api_key: str = field(default_factory=lambda: os.getenv("KIMI_API_KEY", "").strip())
    base_url: str = field(default_factory=lambda: os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1").strip())
    model: str = field(default_factory=lambda: os.getenv("KIMI_MODEL", "moonshot-v1-8k"))
    temperature: float = field(default_factory=lambda: float(os.getenv("KIMI_TEMPERATURE", "0.3")))
    timeout: float = field(default_factory=lambda: float(os.getenv("KIMI_TIMEOUT", "60.0")))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def make_client(self) -> "OpenAI":
        from openai import OpenAI
        return OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout)
```
并在 `AppConfig` 加 `kimi: KimiConfig = field(default_factory=KimiConfig)`。

- [ ] **Step 4：运行确认通过** — PASS
- [ ] **Step 5：commit** — `git add cooling_rag_mg/config.py tests/test_kimi_config.py && git commit -m "feat: KimiConfig（Task 1）"`

---

## Task 2：Kimi 检索内容生成

**Files:** Create `cooling_rag_mg/retrieval_query_gen.py`；Test `tests/test_retrieval_query_gen.py`

- [ ] **Step 1：写失败测试**

```python
from unittest.mock import MagicMock
def _resp(c): return MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="kimi")

def test_build_query_prompt_asks_zh_en_keywords_sentences():
    from cooling_rag_mg.retrieval_query_gen import build_query_prompt
    p = build_query_prompt("海水泵应一用一备")
    assert "关键词" in p and ("英文" in p or "English" in p) and "海水泵应一用一备" in p

def test_parse_queries_flattens_keywords_and_sentences():
    from cooling_rag_mg.retrieval_query_gen import parse_queries
    raw = '{"keywords":["海水泵","seawater pump"],"sentences":["海水泵应冗余","seawater pump shall be redundant"]}'
    qs = parse_queries(raw)
    assert "海水泵" in qs and "seawater pump shall be redundant" in qs
    assert len(qs) == 4 and len(set(qs)) == 4   # 去重、合并

def test_parse_queries_empty_on_failure():
    from cooling_rag_mg.retrieval_query_gen import parse_queries
    assert parse_queries("not json") == []

def test_generate_queries_calls_kimi():
    from cooling_rag_mg.retrieval_query_gen import generate_queries
    client = MagicMock()
    client.chat.completions.create.side_effect = [_resp('{"keywords":["海水泵"],"sentences":["seawater pump redundancy"]}')]
    qs = generate_queries("海水泵应一用一备", client, model="kimi")
    assert qs == ["海水泵", "seawater pump redundancy"]
```

- [ ] **Step 2：运行确认失败** → FAIL
- [ ] **Step 3：实现** — `cooling_rag_mg/retrieval_query_gen.py`

```python
from __future__ import annotations
import json
from typing import Any

_QUERY_PROMPT = """你是船舶冷却水系统检索助手。针对下面的原始需求，生成用于在中英文混合文档库中**检索证据**的内容，追求覆盖率。
- keywords：组成对象/部件/工程方面等关键词（中英文都给）。
- sentences：适合语义检索的完整句子（中英文都给）。
只输出 JSON：{{"keywords":["..."],"sentences":["..."]}}
原始需求：{req}"""

def build_query_prompt(requirement_text: str) -> str:
    return _QUERY_PROMPT.format(req=requirement_text)

def parse_queries(raw: str) -> list[str]:
    try:
        obj = json.loads(raw or "{}")
    except Exception:
        return []
    out: list[str] = []
    for key in ("keywords", "sentences"):
        for x in obj.get(key, []) or []:
            s = str(x).strip()
            if s and s not in out:
                out.append(s)
    return out

def generate_queries(requirement_text: str, client: Any, model: str, temperature: float = 0.3) -> list[str]:
    from cooling_rag_mg.llm_cache import cached_completion
    try:
        resp = cached_completion(client, model=model,
            messages=[{"role": "user", "content": build_query_prompt(requirement_text)}],
            temperature=temperature, max_tokens=500, response_format={"type": "json_object"})
        return parse_queries(resp.choices[0].message.content or "{}")
    except Exception:
        return []
```

- [ ] **Step 4：运行确认通过** → PASS（4 passed）
- [ ] **Step 5：commit** — `git add cooling_rag_mg/retrieval_query_gen.py tests/test_retrieval_query_gen.py && git commit -m "feat: Kimi 检索内容生成（Task 2）"`

---

## Task 3：覆盖优先检索

**Files:** Create `cooling_rag_mg/coverage_retrieval.py`；Test `tests/test_coverage_retrieval.py`

- [ ] **Step 1：写失败测试**

```python
def test_coverage_retrieve_unions_and_dedups():
    from cooling_rag_mg.coverage_retrieval import coverage_retrieve
    # fake searcher：按 query 返回不同候选；union 后按 id 去重
    class FakeSearcher:
        def vector_search(self, q, k):
            return {"a": [{"id":"E1","text":"t1"}], "b": [{"id":"E2","text":"t2"}]}.get(q, [])
        def bm25_search(self, q, k):
            return {"a": [{"id":"E2","text":"t2"}], "b": [{"id":"E3","text":"t3"}]}.get(q, [])
    out = coverage_retrieve(["a","b"], FakeSearcher(), per_query_k=10, max_total=10)
    ids = sorted(d["id"] for d in out)
    assert ids == ["E1","E2","E3"]   # 并集去重

def test_coverage_retrieve_empty_queries():
    from cooling_rag_mg.coverage_retrieval import coverage_retrieve
    class S:  # 不会被调用
        def vector_search(self,q,k): return []
        def bm25_search(self,q,k): return []
    assert coverage_retrieve([], S(), per_query_k=10, max_total=10) == []
```

- [ ] **Step 2：运行确认失败** → FAIL
- [ ] **Step 3：实现** — `cooling_rag_mg/coverage_retrieval.py`

```python
from __future__ import annotations
from typing import Any
from cooling_rag_mg.hybrid_fusion import rrf_fuse

def coverage_retrieve(queries: list[str], searcher: Any, per_query_k: int = 20, max_total: int = 60) -> list[dict]:
    """对多条 query 各自 vector+bm25+rrf，按 id 取并集去重（覆盖率优先）。保留首次出现。"""
    seen: dict[str, dict] = {}
    for q in queries:
        vec = searcher.vector_search(q, per_query_k)
        bm = searcher.bm25_search(q, per_query_k)
        for cand in rrf_fuse([vec, bm]):
            cid = cand.get("id") or cand.get("chunk_id")
            if cid and cid not in seen:
                seen[cid] = cand
            if len(seen) >= max_total:
                break
    return list(seen.values())
```

- [ ] **Step 4：运行确认通过** → PASS
- [ ] **Step 5：commit** — `git add cooling_rag_mg/coverage_retrieval.py tests/test_coverage_retrieval.py && git commit -m "feat: 覆盖优先检索（Task 3）"`

> 注：真实 searcher 用 `HybridIndexSearcher(load_index(indexes_dir/'evidence_units'), device=...)`（见 `experiment_runner._build_flat_retrieval_payload`）。rrf_fuse 兼容空列表。

---

## Task 4：no-RAG 强基线 + RAG 据证据生成

**Files:** Create `cooling_rag_mg/req_generation_v2.py`；Test `tests/test_req_generation_v2.py`

要点：no-RAG 强基线 prompt **不阉割**——要求充分运用领域知识、产出完整具体可指导施工的工程需求（含必要参数），但保持工程严谨、不可臆造无依据的硬性安全/法规阈值。RAG prompt 据证据生成、先判证据相关性、未覆盖不臆造。两者各自解析为 `engineering_requirements` 列表（含 shall_statement；RAG 附 evidence_ids，no-RAG 空）。

- [ ] **Step 1：写失败测试**

```python
from unittest.mock import MagicMock
def _resp(c): return MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="ds")

def test_norag_prompt_is_strong_not_polisher():
    from cooling_rag_mg.req_generation_v2 import build_norag_messages
    m = build_norag_messages("海水泵应一用一备")
    sys = m[0]["content"]
    assert "海水泵应一用一备" in m[1]["content"]
    assert ("完整" in sys and "具体" in sys)          # 要求完整具体
    assert ("润色" in sys)                              # 明确否定"仅润色"（如"不要仅做语言润色"）

def test_rag_messages_carry_evidence():
    from cooling_rag_mg.req_generation_v2 import build_rag_messages
    m = build_rag_messages("海水泵应一用一备", ["海水泵一用一备", "备用泵自动投入"])
    u = m[1]["content"]
    assert "海水泵一用一备" in u and "备用泵自动投入" in u and "证据" in u

def test_parse_and_tag_attaches_evidence_ids():
    from cooling_rag_mg.req_generation_v2 import parse_requirements
    raw = '{"engineering_requirements":[{"shall_statement":"应一用一备。"}, "坏元素"]}'
    out = parse_requirements(raw, evidence_ids=["E1"])
    assert len(out) == 1 and out[0]["shall_statement"] == "应一用一备。"
    assert out[0]["evidence_ids"] == ["E1"]

def test_generate_norag_returns_list():
    from cooling_rag_mg.req_generation_v2 import generate_norag
    client = MagicMock()
    client.chat.completions.create.side_effect = [_resp('{"engineering_requirements":[{"shall_statement":"应一用一备。"}]}')]
    out = generate_norag("海水泵应一用一备", client, model="ds")
    assert out[0]["shall_statement"] == "应一用一备。" and out[0]["evidence_ids"] == []
```

- [ ] **Step 2：运行确认失败** → FAIL
- [ ] **Step 3：实现** — `cooling_rag_mg/req_generation_v2.py`

```python
from __future__ import annotations
import json
from typing import Any

_NORAG_SYSTEM = """你是资深船舶主机冷却水系统工程师。把用户给的原始需求，转化为**完整、具体、可直接指导工程建设**的结构化工程需求(shall)。
要求：
- 充分运用你的专业领域知识，给出完整覆盖、具体可操作的工程需求，必要时给出工程上合理的参数/配置/验证方式。
- 这是**专业工程转化，不是语言润色**——不要只把原话换个说法，要补足工程上应当明确的内容。
- 保持工程严谨：对没有把握的强制性安全/法规限值，按工程惯例给出并标注需校核，不要臆造精确法规编号。
只输出 JSON：{"engineering_requirements":[{"shall_statement":"...","verification_method":"...","acceptance_criteria":["..."]}]}"""

_RAG_SYSTEM = """你是资深船舶主机冷却水系统工程师。依据**检索到的证据**，把原始需求转化为完整、具体、可指导工程的结构化工程需求(shall)。
要求：
- 先判断每条证据与需求的相关性，只用相关证据；据证据给出具体工程要求与参数。
- 证据未覆盖的具体参数不要臆造，可写"待按厂家技术数据/规则条款确认"。
- 这是专业工程转化，不是语言润色。
只输出 JSON：{"engineering_requirements":[{"shall_statement":"...","verification_method":"...","acceptance_criteria":["..."]}]}"""

def build_norag_messages(requirement_text: str) -> list[dict]:
    return [{"role": "system", "content": _NORAG_SYSTEM},
            {"role": "user", "content": f"原始需求：{requirement_text}"}]

def build_rag_messages(requirement_text: str, evidence_texts: list[str]) -> list[dict]:
    block = "\n".join(f"[E{i+1}] {t}" for i, t in enumerate(evidence_texts))
    return [{"role": "system", "content": _RAG_SYSTEM},
            {"role": "user", "content": f"原始需求：{requirement_text}\n\n证据：\n{block}"}]

def parse_requirements(raw: str, evidence_ids: list[str]) -> list[dict]:
    try:
        ers = json.loads(raw or "{}").get("engineering_requirements", [])
    except Exception:
        return []
    if not isinstance(ers, list):
        return []
    out = []
    for er in ers:
        if not isinstance(er, dict):
            continue
        er["evidence_ids"] = list(evidence_ids)
        er.setdefault("shall_statement", "")
        out.append(er)
    return out

def _gen(messages, evidence_ids, client, model, temperature, max_tokens=2000):
    from cooling_rag_mg.llm_cache import cached_completion
    try:
        resp = cached_completion(client, model=model, messages=messages,
            temperature=temperature, max_tokens=max_tokens, response_format={"type": "json_object"})
        return parse_requirements(resp.choices[0].message.content or "{}", evidence_ids)
    except Exception:
        return []

def generate_norag(requirement_text: str, client: Any, model: str, temperature: float = 0.2) -> list[dict]:
    return _gen(build_norag_messages(requirement_text), [], client, model, temperature)

def generate_rag(requirement_text: str, evidence_texts: list[str], evidence_ids: list[str],
                 client: Any, model: str, temperature: float = 0.2) -> list[dict]:
    return _gen(build_rag_messages(requirement_text, evidence_texts), evidence_ids, client, model, temperature)
```

- [ ] **Step 4：运行确认通过** → PASS（4 passed）
- [ ] **Step 5：commit** — `git add cooling_rag_mg/req_generation_v2.py tests/test_req_generation_v2.py && git commit -m "feat: no-RAG 强基线 + RAG 据证据生成（Task 4）"`

---

## Task 5：盲评质量裁判（左右交换）

**Files:** Create `cooling_rag_mg/quality_judge.py`；Test `tests/test_quality_judge.py`

维度：completeness / actionability / consistency / verifiability。裁判对 A/B 两份逐维判 `A`/`B`/`tie`。左右交换双评后归一到 R-vs-B0（消位置偏置）。

- [ ] **Step 1：写失败测试**

```python
from unittest.mock import MagicMock
def _resp(c): return MagicMock(choices=[MagicMock(message=MagicMock(content=c))], model="qwen")

DIMS = ["completeness","actionability","consistency","verifiability"]

def test_parse_pairwise():
    from cooling_rag_mg.quality_judge import parse_pairwise
    raw = '{"completeness":"A","actionability":"B","consistency":"tie","verifiability":"A"}'
    d = parse_pairwise(raw)
    assert d == {"completeness":"A","actionability":"B","consistency":"tie","verifiability":"A"}

def test_judge_pair_normalizes_to_target_when_R_is_A():
    # 当 R 放在 A 位：A 胜=R 胜
    from cooling_rag_mg.quality_judge import judge_pair
    client = MagicMock()
    client.chat.completions.create.side_effect = [_resp('{"completeness":"A","actionability":"tie","consistency":"B","verifiability":"A"}')]
    res = judge_pair("原始需求", r_text="R内容", b0_text="B0内容", r_on_left=True, client=client, model="qwen")
    # 归一为 R 视角：A->R, B->B0
    assert res["completeness"]=="R" and res["consistency"]=="B0" and res["actionability"]=="tie"

def test_judge_pair_normalizes_when_R_is_B():
    from cooling_rag_mg.quality_judge import judge_pair
    client = MagicMock()
    client.chat.completions.create.side_effect = [_resp('{"completeness":"A","actionability":"B","consistency":"tie","verifiability":"B"}')]
    res = judge_pair("原始需求", r_text="R内容", b0_text="B0内容", r_on_left=False, client=client, model="qwen")
    # R 在 B 位：A->B0, B->R
    assert res["completeness"]=="B0" and res["verifiability"]=="R" and res["consistency"]=="tie"
```

- [ ] **Step 2：运行确认失败** → FAIL
- [ ] **Step 3：实现** — `cooling_rag_mg/quality_judge.py`

```python
from __future__ import annotations
import json
from typing import Any

DIMS = ["completeness", "actionability", "consistency", "verifiability"]
_PROMPT = """你是船舶冷却水系统资深评审。下面是同一原始需求的两份工程需求方案 A 和 B。
就每个维度判断哪份更好（更完整 completeness、更具体可操作 actionability、更内部一致 consistency、更可验证 verifiability）。
不要因为某份"带证据引用"而偏向它，只看工程需求本身质量。
原始需求：{req}
方案A：{a}
方案B：{b}
只输出 JSON：{{"completeness":"A|B|tie","actionability":"A|B|tie","consistency":"A|B|tie","verifiability":"A|B|tie"}}"""

def parse_pairwise(raw: str) -> dict:
    try:
        obj = json.loads(raw or "{}")
    except Exception:
        return {d: "tie" for d in DIMS}
    out = {}
    for d in DIMS:
        v = str(obj.get(d, "tie")).strip().upper()
        out[d] = v if v in {"A", "B"} else "tie"
    return out

def judge_pair(requirement_text, r_text, b0_text, r_on_left, client, model, temperature=0.0) -> dict:
    """R 与 B0 盲评；r_on_left 决定 R 放 A 还是 B 位。返回每维 'R'/'B0'/'tie'。"""
    from cooling_rag_mg.llm_cache import cached_completion
    a, b = (r_text, b0_text) if r_on_left else (b0_text, r_text)
    try:
        resp = cached_completion(client, model=model,
            messages=[{"role": "user", "content": _PROMPT.format(req=requirement_text, a=a, b=b)}],
            temperature=temperature, max_tokens=200, response_format={"type": "json_object"})
        raw = parse_pairwise(resp.choices[0].message.content or "{}")
    except Exception:
        raw = {d: "tie" for d in DIMS}
    # 归一到 R 视角
    def norm(v):
        if v == "tie":
            return "tie"
        win_is_left = (v == "A")
        return "R" if (win_is_left == r_on_left) else "B0"
    return {d: norm(raw[d]) for d in DIMS}
```

- [ ] **Step 4：运行确认通过** → PASS
- [ ] **Step 5：commit** — `git add cooling_rag_mg/quality_judge.py tests/test_quality_judge.py && git commit -m "feat: 盲评质量裁判 左右交换（Task 5）"`

---

## Task 6：两条产线脚本 + 跑数 — **需 Kimi/DeepSeek API**

**Files:** Create `scripts/45_run_pipelines_v2.py`

要点（含 `--limit` 冒烟）：
- 读 `original_requirements_v1.jsonl`（60 条）。
- no-RAG：`generate_norag(req_text, ds_client, ds_model)`。
- RAG：`generate_queries(req_text, kimi_client, kimi_model)` → 构建 evidence_units `HybridIndexSearcher` → `coverage_retrieve(queries, searcher, per_query_k=20, max_total=60)` → 取证据 text/id → `generate_rag(req_text, ev_texts, ev_ids, ds_client, ds_model)`。
- result_set 结构同旧版：`{"source_requirement_id","engineering_requirements":[...],"_arm","_n_queries","_n_evidence"}`。
- 熔断：连续 5 个 no-RAG 空结果即 `sys.exit(2)`（防 API 静默失败，见上一版 Qwen 欠费教训）。
- 落 `data/search_results/exp_v2/{norag,rag}_results.json`。

- [ ] Step 1 实现脚本（沿用 `scripts/44` 样式与熔断）。
- [ ] Step 2 `--limit 2` 冒烟：确认 no-RAG 出完整具体需求、RAG 有 evidence_ids、检索覆盖>旧版。
- [ ] Step 3 全量跑（后台，直接重定向使退出码反映 python）。
- [ ] Step 4 校验：两组 0 空 shall、no-RAG 含具体参数占比明显>0（验证未被阉割）、RAG 覆盖率。
- [ ] Step 5 commit 脚本 + 产物。

---

## Task 7：评估脚本 — **需 Qwen API**

**Files:** Create `scripts/46_evaluate_v2.py`

- [ ] **可靠性**（复用 `credibility_eval.py`，裁判=Qwen）：对两组每条 shall：`extract_claims`（DeepSeek）→ `kb_search`（evidence_units 索引，复用 scripts/43 的 `_make_kb_search`）→ `judge_claim_llm`（**Qwen**）→ `score_shall`（矛盾率=H_hard 主、查无率=H_soft 描述）；`judge_over_inference`（Qwen）。`aggregate_by_source` + `paired_compare`（配对单位=源需求）。
- [ ] **质量盲评**（`quality_judge`）：对每个源需求把该源的 no-RAG 全部 shall 拼为 b0_text、RAG 全部 shall 拼为 r_text；`judge_pair` 跑两次（`r_on_left=True/False`）取**一致维度**（不一致计 tie，记位置偏置率）；汇总各维 R 胜率/平/负 + 总胜率。
- [ ] **描述性**：可溯源率、覆盖率、具体参数占比、篇幅。
- [ ] **校准抽样**：质量盲评抽 ~40 对（含分歧对）导出 `quality_calibration_v2.csv`（含原始需求、两份内容、各维 auto 判、空白 human 列）。
- [ ] 落 `reliability_eval_v2.json` + `quality_eval_v2.json`。先 `--limit` 冒烟报花费再全量。
- [ ] commit。

---

## Task 8：消融 + 论文 · 路线图

- [ ] 消融①去 Kimi：用原始需求直接 `coverage_retrieve`（单查询）跑 RAG，对比看 Kimi 贡献。
- [ ] 消融②覆盖 vs 精准：`per_query_k`/`max_total` 调小 + 加 applicability 过滤，对比。
- [ ] 论文叙事：据质量胜率 + 矛盾率 + 人工校准，定论"RAG 路径是否更优"。

---

## 微调记录（执行中发现问题就追加）

_（暂无）_
