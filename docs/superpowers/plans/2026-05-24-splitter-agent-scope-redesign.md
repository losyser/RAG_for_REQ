# 拆分器 v2 + 审核循环 + Agent 范围约束 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让工程需求 Agent 的输出严格锚定到原始需求涵盖的工程方面，禁止凭空添加原文未提及的内容，同时引入拆分审核循环保证方面识别质量。

**Architecture:** 拆分器 v2 以工程方面识别替换句界切分，每个方面携带 `source_phrase`（原文溯源）和 `implication_type`；新增审核 Agent 在检索前验证方面合法性，最多循环 N 轮；`compact_requirement_context()` 将验证通过的方面列表以 `allowed_engineering_aspects` 传给 Agent；Agent prompt 新增【F】范围约束节，`normalize_agent_output()` 做兜底校验。

**Tech Stack:** Python 3.11, DeepSeek API (OpenAI SDK), pytest (新增 tests/ 目录)

---

## 文件结构

| 文件 | 变化 |
|---|---|
| `cooling_rag_mg/config.py` | 新增 `splitter_review_max_rounds: int` |
| `cooling_rag_mg/requirement_splitter.py` | 新 SPLIT_PROMPT + REVIEW_PROMPT + `_review_aspects()` + 修订循环 |
| `cooling_rag_mg/pipeline.py` | `build_sub_payload()` 透传 `source_phrase`、`implication_type` |
| `cooling_rag_mg/engineering_requirement_agent.py` | `compact_requirement_context()` + Agent prompt + `normalize_agent_output()` |
| `tests/test_splitter_review.py` | 新建：审核循环逻辑单元测试 |
| `tests/test_scope_validation.py` | 新建：`normalize_agent_output` 范围校验测试 |
| `tests/test_compact_context.py` | 新建：`allowed_engineering_aspects` 字段测试 |

---

## Task 1：config.py — 新增 `splitter_review_max_rounds`

**Files:**
- Modify: `cooling_rag_mg/config.py:71-86`

- [ ] **Step 1: 在 `DeepSeekConfig` 中添加字段**

在 `max_tokens_requirement_agent` 行之后添加：

```python
    splitter_review_max_rounds: int = int(os.getenv("SPLITTER_REVIEW_MAX_ROUNDS", "3"))
```

完整修改后的 `DeepSeekConfig`（第 71-86 行区域）：
```python
@dataclass(frozen=True)
class DeepSeekConfig:
    api_key: str = os.getenv("api_key", os.getenv("DEEPSEEK_API_KEY", "")).strip()
    base_url: str = os.getenv("base_url", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")).strip()
    model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    use_requirement_splitter: bool = os.getenv("USE_REQUIREMENT_SPLITTER", "1").strip() != "0"
    use_evidence_judge: bool = os.getenv("USE_EVIDENCE_JUDGE", "1").strip() != "0"
    temperature: float = float(os.getenv("DEEPSEEK_TEMPERATURE", "0.1"))
    max_tokens_split: int = int(os.getenv("MAX_TOKENS_SPLIT", "1200"))
    max_tokens_judge: int = int(os.getenv("MAX_TOKENS_JUDGE", "2800"))
    max_tokens_requirement_agent: int = int(os.getenv("MAX_TOKENS_REQUIREMENT_AGENT", "6000"))
    splitter_review_max_rounds: int = int(os.getenv("SPLITTER_REVIEW_MAX_ROUNDS", "3"))

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)
```

- [ ] **Step 2: 验证配置可以读取**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -c "
from cooling_rag_mg.config import get_config
cfg = get_config()
print('splitter_review_max_rounds:', cfg.deepseek.splitter_review_max_rounds)
"
```

期望输出：`splitter_review_max_rounds: 3`

---

## Task 2：requirement_splitter.py — 新 SPLIT_PROMPT

**Files:**
- Modify: `cooling_rag_mg/requirement_splitter.py:12-65`

- [ ] **Step 1: 替换 `SPLIT_PROMPT` 全文**

用以下内容完整替换文件中 `SPLIT_PROMPT = """` 到其对应 `"""` 的全部内容：

```python
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
```

- [ ] **Step 2: 语法检查**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -c "import cooling_rag_mg.requirement_splitter; print('OK')"
```

期望：`OK`

---

## Task 3：requirement_splitter.py — 新增 REVIEW_PROMPT 和 `_review_aspects()`

**Files:**
- Modify: `cooling_rag_mg/requirement_splitter.py`（在 SPLIT_PROMPT 之后、`_extract_json` 之前插入）

- [ ] **Step 1: 写 tests/test_splitter_review.py（先写测试）**

新建 `tests/` 目录和测试文件：

```bash
mkdir -p /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular/tests
touch /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular/tests/__init__.py
```

```python
# tests/test_splitter_review.py
from unittest.mock import patch, MagicMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cooling_rag_mg.requirement_splitter import _review_aspects


def _mock_openai_response(content: str):
    resp = MagicMock()
    resp.choices[0].message.content = content
    return resp


def test_review_passes_valid_aspects():
    """审核 Agent 对合法方面列表返回 passed=True。"""
    aspects = [
        {
            "sub_id": "01", "requirement_type": "redundancy",
            "topic": "冷却水泵冗余配置",
            "text": "主机冷却水系统应配置冗余冷却水泵。",
            "source_phrase": "稳定可靠的冷却能力",
            "implication_type": "direct_implication",
        }
    ]
    review_json = '{"passed": true, "aspect_evaluations": [{"aspect_name": "冷却水泵冗余配置", "valid": true}], "missing_aspects": [], "overall_feedback": ""}'

    with patch("cooling_rag_mg.requirement_splitter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(review_json)

        result = _review_aspects("主机冷却水系统应保证稳定可靠的冷却能力。", aspects)

    assert result["passed"] is True
    assert result["missing_aspects"] == []


def test_review_fails_on_scope_creep():
    """审核 Agent 对超出范围的方面返回 passed=False 并给出 feedback。"""
    aspects = [
        {
            "sub_id": "01", "requirement_type": "parameter",
            "topic": "倾斜工况适应性",
            "text": "系统应在横倾15°工况下正常工作。",
            "source_phrase": "倾斜工况",
            "implication_type": "explicit",
        }
    ]
    review_json = (
        '{"passed": false, '
        '"aspect_evaluations": [{"aspect_name": "倾斜工况适应性", "valid": false, '
        '"issue": "source_phrase 不存在于原文"}], '
        '"missing_aspects": [], '
        '"overall_feedback": "删除倾斜工况适应性"}'
    )

    with patch("cooling_rag_mg.requirement_splitter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(review_json)

        result = _review_aspects("主机入口冷却水温度和流量应满足厂家要求。", aspects)

    assert result["passed"] is False
    assert "overall_feedback" in result
    assert result["overall_feedback"] != ""
```

- [ ] **Step 2: 运行测试，确认因缺少 `_review_aspects` 而失败**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_splitter_review.py -v 2>&1 | head -20
```

期望：`ImportError: cannot import name '_review_aspects'`

- [ ] **Step 3: 在 `requirement_splitter.py` 中添加 `REVIEW_PROMPT` 和 `_review_aspects()`**

在 `SPLIT_PROMPT` 结束后、`_extract_json` 函数之前插入：

```python
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
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_splitter_review.py -v
```

期望：`2 passed`

---

## Task 4：requirement_splitter.py — 修订循环集成到 `split_requirement()`

**Files:**
- Modify: `cooling_rag_mg/requirement_splitter.py:103-143`（`split_requirement` 函数）

- [ ] **Step 1: 写循环逻辑测试**

在 `tests/test_splitter_review.py` 末尾追加：

```python
def test_split_with_review_exits_on_pass():
    """通过时循环只跑一轮就退出。"""
    from cooling_rag_mg.requirement_splitter import split_requirement

    split_json = json.dumps({
        "sub_requirements": [{
            "sub_id": "01",
            "requirement_type": "operation",
            "topic": "冷却水工况稳定性",
            "text": "冷却水系统应在连续运行等工况下稳定运行。",
            "source_phrase": "连续运行",
            "implication_type": "explicit",
        }]
    })
    review_json = '{"passed": true, "aspect_evaluations": [{"aspect_name": "冷却水工况稳定性", "valid": true}], "missing_aspects": [], "overall_feedback": ""}'

    with patch("cooling_rag_mg.requirement_splitter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        # 第一次调用=拆分，第二次调用=审核
        mock_client.chat.completions.create.side_effect = [
            _mock_openai_response(split_json),
            _mock_openai_response(review_json),
        ]
        result = split_requirement("R001", "船东", "系统应在连续运行等工况下稳定运行。")

    assert len(result) == 1
    assert result[0]["source_phrase"] == "连续运行"
    # 只调用了 2 次（1 拆分 + 1 审核）
    assert mock_client.chat.completions.create.call_count == 2


def test_split_with_review_retries_on_fail():
    """不通过时循环重试，第二轮通过后退出。"""
    import json as _json
    from cooling_rag_mg.requirement_splitter import split_requirement

    def _split_resp(source_phrase):
        return _mock_openai_response(_json.dumps({
            "sub_requirements": [{
                "sub_id": "01", "requirement_type": "parameter",
                "topic": "参数限值", "text": "温度应满足要求。",
                "source_phrase": source_phrase,
                "implication_type": "explicit",
            }]
        }))

    fail_review = _mock_openai_response(
        '{"passed": false, "aspect_evaluations": [{"aspect_name": "参数限值", "valid": false, "issue": "source_phrase 不在原文"}], "missing_aspects": [], "overall_feedback": "修正 source_phrase"}'
    )
    pass_review = _mock_openai_response(
        '{"passed": true, "aspect_evaluations": [{"aspect_name": "参数限值", "valid": true}], "missing_aspects": [], "overall_feedback": ""}'
    )

    with patch("cooling_rag_mg.requirement_splitter.OpenAI") as mock_cls:
        mock_client = MagicMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            _split_resp("不存在的词"),   # 第1轮 拆分
            fail_review,                 # 第1轮 审核 → 失败
            _split_resp("温度"),         # 第2轮 拆分
            pass_review,                 # 第2轮 审核 → 通过
        ]
        result = split_requirement("R002", "船东", "主机入口冷却水温度应满足厂家要求。")

    assert result[0]["source_phrase"] == "温度"
    assert mock_client.chat.completions.create.call_count == 4
```

在测试文件顶部补充 import：
```python
import json
```

- [ ] **Step 2: 运行新测试，确认失败（函数尚未有循环）**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_splitter_review.py::test_split_with_review_exits_on_pass -v 2>&1 | tail -10
```

期望：FAIL（`source_phrase` 不在结果中）

- [ ] **Step 3: 改写 `split_requirement()` 加入循环**

用以下代码完整替换 `split_requirement` 函数（第 103-143 行）：

```python
def split_requirement(requirement_id: str, stakeholder: str, raw_text: str) -> list[dict[str, Any]]:
    cfg = get_config()
    if not (cfg.deepseek.enabled and cfg.deepseek.use_requirement_splitter):
        return fallback_split(raw_text)

    try:
        client = OpenAI(api_key=cfg.deepseek.api_key, base_url=cfg.deepseek.base_url)
        feedback: str | None = None
        prev_aspects: list[dict[str, Any]] | None = None

        for attempt in range(max(1, cfg.deepseek.splitter_review_max_rounds)):
            # ── 拆分阶段 ──
            payload: dict[str, Any] = {
                "requirement_id": requirement_id,
                "stakeholder": stakeholder,
                "raw_requirement": raw_text,
            }
            if prev_aspects is not None:
                payload["previous_aspects"] = prev_aspects
            if feedback is not None:
                payload["reviewer_feedback"] = feedback

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
            aspects = _clean_aspects(obj.get("sub_requirements", []))

            if not aspects:
                break

            # ── 审核阶段 ──
            review = _review_aspects(raw_text, aspects)
            if review.get("passed", True):
                return _dedup_topics(aspects)

            feedback = review.get("overall_feedback", "")
            prev_aspects = aspects

        # 超过上限：使用最后一轮结果，追加警告标记
        if aspects:
            for a in aspects:
                a["review_warning"] = f"审核未通过，已达最大修订轮数({cfg.deepseek.splitter_review_max_rounds})"
            return _dedup_topics(aspects)

    except Exception as exc:
        return fallback_split(raw_text, error=str(exc))

    return fallback_split(raw_text)
```

- [ ] **Step 4: 将 `_clean_aspects()` 抽取函数插到 `_dedup_topics` 之前**

`_clean_aspects` 负责把 LLM 原始输出标准化（合并原来 `split_requirement` 内的 cleaned 列表逻辑）：

```python
def _clean_aspects(subs: list[Any]) -> list[dict[str, Any]]:
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
            "source_phrase": safe_text(s.get("source_phrase")) or "",
            "implication_type": safe_text(s.get("implication_type")) or "explicit",
            "split_method": "deepseek_v2",
        })
    return cleaned
```

- [ ] **Step 5: 运行全部测试**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_splitter_review.py -v
```

期望：`4 passed`

- [ ] **Step 6: 确认 `fallback_split` 不受影响**

```bash
python -c "
from cooling_rag_mg.requirement_splitter import fallback_split
result = fallback_split('系统应具备冷却能力；并具备冗余配置。')
print([r['text'] for r in result])
"
```

期望：两条子需求，均无 `source_phrase` 字段或 `source_phrase` 为空

- [ ] **Step 7: Commit**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
git add cooling_rag_mg/requirement_splitter.py cooling_rag_mg/config.py tests/
git commit -m "feat: splitter v2 — aspect-based split with source_phrase + review loop"
```

---

## Task 5：pipeline.py — 透传 `source_phrase` 和 `implication_type`

**Files:**
- Modify: `cooling_rag_mg/pipeline.py`（`build_sub_payload` 函数）

- [ ] **Step 1: 写测试**

新建 `tests/test_pipeline_passthrough.py`：

```python
# tests/test_pipeline_passthrough.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cooling_rag_mg.pipeline import build_sub_payload


def test_build_sub_payload_passes_source_phrase():
    sub = {
        "sub_id": "01",
        "requirement_type": "redundancy",
        "topic": "冷却水泵冗余配置",
        "text": "系统应配置冗余冷却水泵。",
        "source_phrase": "稳定可靠的冷却能力",
        "implication_type": "direct_implication",
        "split_method": "deepseek_v2",
    }
    result = build_sub_payload("R001", 1, sub)
    assert result["source_phrase"] == "稳定可靠的冷却能力"
    assert result["implication_type"] == "direct_implication"


def test_build_sub_payload_defaults_missing_fields():
    sub = {
        "sub_id": "01",
        "requirement_type": "operation",
        "topic": "工况适应性",
        "text": "系统应适应各工况。",
        "split_method": "fallback_rule",
    }
    result = build_sub_payload("R002", 1, sub)
    assert result["source_phrase"] == ""
    assert result["implication_type"] == ""
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_pipeline_passthrough.py -v 2>&1 | tail -10
```

期望：`KeyError: 'source_phrase'`

- [ ] **Step 3: 修改 `build_sub_payload`**

找到 `pipeline.py` 中的 `build_sub_payload` 函数，在 return dict 中追加两个字段：

```python
def build_sub_payload(requirement_id: str, idx: int, sub: dict[str, Any]) -> dict[str, Any]:
    sub_raw_id = sub.get("sub_id") or f"{idx:02d}"
    sub_id = f"{requirement_id}-{str(sub_raw_id).zfill(2)}"
    return {
        "sub_requirement_id": sub_id,
        "requirement_type": sub.get("requirement_type", "other"),
        "topic": sub.get("topic", ""),
        "text": sub.get("text", ""),
        "split_method": sub.get("split_method", ""),
        "split_error": sub.get("split_error", ""),
        "source_phrase": sub.get("source_phrase", ""),
        "implication_type": sub.get("implication_type", ""),
    }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_pipeline_passthrough.py -v
```

期望：`2 passed`

- [ ] **Step 5: Commit**

```bash
git add cooling_rag_mg/pipeline.py tests/test_pipeline_passthrough.py
git commit -m "feat: pass source_phrase and implication_type through pipeline"
```

---

## Task 6：`compact_requirement_context()` — 输出 `allowed_engineering_aspects`

**Files:**
- Modify: `cooling_rag_mg/engineering_requirement_agent.py`（`compact_requirement_context` 函数，约第 345-413 行）

- [ ] **Step 1: 写测试**

新建 `tests/test_compact_context.py`：

```python
# tests/test_compact_context.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_context(sub_requirements):
    return {
        "requirement_id": "R001",
        "stakeholder": "船东",
        "raw_requirement_text": "系统应保证稳定可靠的冷却能力。",
        "sub_requirements": sub_requirements,
    }


def test_allowed_aspects_extracted_from_sub_requirements():
    from cooling_rag_mg.engineering_requirement_agent import compact_requirement_context

    subs = [
        {
            "requirement_type": "redundancy",
            "topic": "冷却水泵冗余配置",
            "text": "系统应配置冗余泵。",
            "source_phrase": "稳定可靠的冷却能力",
            "implication_type": "direct_implication",
            "selected_results": [],
        },
        {
            "requirement_type": "parameter",
            "topic": "温度控制范围",
            "text": "温度应满足厂家要求。",
            "source_phrase": "温度",
            "implication_type": "explicit",
            "selected_results": [],
        },
    ]
    ctx = compact_requirement_context(_make_context(subs))

    aspects = ctx["allowed_engineering_aspects"]
    assert len(aspects) == 2
    assert aspects[0]["topic"] == "冷却水泵冗余配置"
    assert aspects[0]["source_phrase"] == "稳定可靠的冷却能力"
    assert aspects[0]["implication_type"] == "direct_implication"
    assert aspects[1]["topic"] == "温度控制范围"


def test_aspects_without_source_phrase_excluded():
    """fallback 产生的无溯源方面不应出现在 allowed_engineering_aspects 中。"""
    from cooling_rag_mg.engineering_requirement_agent import compact_requirement_context

    subs = [
        {
            "requirement_type": "operation",
            "topic": "工况适应性",
            "text": "系统应适应各工况。",
            "source_phrase": "",          # fallback 产生，无溯源
            "implication_type": "",
            "selected_results": [],
        },
    ]
    ctx = compact_requirement_context(_make_context(subs))
    # fallback 无 source_phrase，不进入 allowed_aspects
    assert ctx["allowed_engineering_aspects"] == []
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_compact_context.py -v 2>&1 | tail -10
```

期望：`KeyError: 'allowed_engineering_aspects'`

- [ ] **Step 3: 修改 `compact_requirement_context()` 返回值**

在 `engineering_requirement_agent.py` 中找到 `compact_requirement_context` 函数的 `return {` 块，
在 `"sub_requirements_hidden_from_generation": True,` 之前插入 `allowed_engineering_aspects`：

```python
    # 从已验证的子需求中提取允许方面（只保留有 source_phrase 的条目）
    allowed_aspects = [
        {
            "topic": sub.get("topic", ""),
            "source_phrase": sub.get("source_phrase", ""),
            "implication_type": sub.get("implication_type", "explicit"),
        }
        for sub in requirement_context.get("sub_requirements", []) or []
        if sub.get("source_phrase")
    ]

    return {
        "requirement_id": requirement_context.get("requirement_id", ""),
        "stakeholder": requirement_context.get("stakeholder", ""),
        "raw_requirement_text": requirement_context.get("raw_requirement_text", ""),
        "generation_basis": "original_requirement_and_supported_evidence_only",
        "supported_evidence_by_topic": grouped_evidence,
        "supported_evidence": supported,
        "background_evidence_for_reference_only": background,
        "evidence_gap_summary": gaps,
        "sub_requirement_type_distribution": sub_type_dist,
        "allowed_engineering_aspects": allowed_aspects,
        "sub_requirements_hidden_from_generation": True,
    }
```

- [ ] **Step 4: 运行测试确认通过**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_compact_context.py -v
```

期望：`2 passed`

- [ ] **Step 5: Commit**

```bash
git add cooling_rag_mg/engineering_requirement_agent.py tests/test_compact_context.py
git commit -m "feat: compact_requirement_context outputs allowed_engineering_aspects"
```

---

## Task 7：Agent Prompt — 新增【F】范围约束节

**Files:**
- Modify: `cooling_rag_mg/engineering_requirement_agent.py`（`ENGINEERING_REQUIREMENT_PROMPT`，第 29-227 行）

- [ ] **Step 1: 在 `ENGINEERING_REQUIREMENT_PROMPT` 中插入【F】节**

找到 prompt 中的 `## 【A】数值安全规则` 行，在其**正上方**插入以下内容（保持缩进与现有 prompt 一致）：

```
## 【F】范围约束（最高优先级，凌驾于其他所有规则）

### F1 允许方面列表
输入中 retrieval_context.allowed_engineering_aspects 列出了本次可以生成工程需求的全部工程方面。
每条方面包含：
- topic：方面名称
- source_phrase：原始需求中支撑该方面的词句
- implication_type：explicit（原文明确）或 direct_implication（工程直接隐含）

### F2 生成规则
- engineering_requirements 必须且只能覆盖 allowed_engineering_aspects 中列出的方面
- 每条 engineering_requirement 的 topic 字段必须与 allowed_engineering_aspects 中的
  topic 值完全一致（逐字复用，不得改写），以便系统自动范围校验
- 每条 engineering_requirement 在 engineering_rationale 中必须写明：
  "本条覆盖方面【topic】，来自原始需求「source_phrase」"
- 若有证据涉及 allowed_engineering_aspects 之外的方面，将其记录在 evidence_gaps，
  不得生成对应的 engineering_requirements 条目
- 若 allowed_engineering_aspects 为空列表，则按原始需求文本本身的结构生成，不受此约束

### F3 禁止行为
✗ 添加 allowed_engineering_aspects 中未列出的任何工程方面
✗ 以"工程完整性"或"证据支撑"为由扩展范围
✗ 将 evidence_gaps 中的信息转化为 engineering_requirements 条目

---

```

- [ ] **Step 2: 确认 prompt 合法（Python 语法）**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -c "
from cooling_rag_mg.engineering_requirement_agent import ENGINEERING_REQUIREMENT_PROMPT
assert '【F】范围约束' in ENGINEERING_REQUIREMENT_PROMPT
assert 'allowed_engineering_aspects' in ENGINEERING_REQUIREMENT_PROMPT
print('OK, prompt length:', len(ENGINEERING_REQUIREMENT_PROMPT))
"
```

期望：`OK, prompt length: <数字>`

- [ ] **Step 3: Commit**

```bash
git add cooling_rag_mg/engineering_requirement_agent.py
git commit -m "feat: add scope constraint section F to engineering agent prompt"
```

---

## Task 8：`normalize_agent_output()` — 兜底范围校验

**Files:**
- Modify: `cooling_rag_mg/engineering_requirement_agent.py`（`normalize_agent_output`）

- [ ] **Step 1: 写测试**

新建 `tests/test_scope_validation.py`：

```python
# tests/test_scope_validation.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from cooling_rag_mg.engineering_requirement_agent import normalize_agent_output


def _base_er(topic: str, er_id: str = "ER-R001-01") -> dict:
    return {
        "id": er_id,
        "parent_id": "ER-R001",
        "level": 1,
        "requirement_type": "redundancy",
        "topic": topic,
        "shall_statement": f"系统应满足{topic}要求。",
        "engineering_rationale": f"本条覆盖方面【{topic}】。",
        "acceptance_criteria": ["满足设计要求。"],
        "verification_method": "review",
        "evidence_ids": [],
        "support_status": "need_confirmation",
        "applicability_constraints": [],
        "risk_if_unmet": "",
    }


def _base_obj(ers, allowed_aspects):
    return {
        "requirement_set_id": "ER-R001",
        "source_requirement_id": "R001",
        "stakeholder": "船东",
        "allowed_engineering_aspects": allowed_aspects,
        "engineering_requirements": ers,
        "relationships": [],
        "evidence_gaps": [],
        "confirmation_items": [],
    }


def test_scope_violation_moved_to_evidence_gaps():
    """topic 不在 allowed_aspects 中的条目应移入 evidence_gaps。"""
    allowed = [{"topic": "冷却水泵冗余配置", "source_phrase": "稳定可靠", "implication_type": "direct_implication"}]
    ers = [
        _base_er("冷却水泵冗余配置", "ER-R001-01"),
        _base_er("倾斜工况适应性", "ER-R001-02"),   # 超范围
    ]
    result = normalize_agent_output(_base_obj(ers, allowed), "R001")

    remaining = [r["topic"] for r in result["engineering_requirements"]]
    assert "冷却水泵冗余配置" in remaining
    assert "倾斜工况适应性" not in remaining

    gap_types = [g["gap_type"] for g in result["evidence_gaps"]]
    assert "scope_violation" in gap_types


def test_no_allowed_aspects_skips_validation():
    """allowed_engineering_aspects 为空时不做范围校验，所有 ER 保留。"""
    ers = [_base_er("任意方面")]
    result = normalize_agent_output(_base_obj(ers, []), "R001")
    assert len(result["engineering_requirements"]) == 1


def test_all_valid_topics_preserved():
    """所有 topic 都在 allowed_aspects 中时，无条目被移除。"""
    allowed = [
        {"topic": "温度控制范围", "source_phrase": "温度", "implication_type": "explicit"},
        {"topic": "冷却水泵冗余配置", "source_phrase": "稳定可靠", "implication_type": "direct_implication"},
    ]
    ers = [
        _base_er("温度控制范围", "ER-R001-01"),
        _base_er("冷却水泵冗余配置", "ER-R001-02"),
    ]
    result = normalize_agent_output(_base_obj(ers, allowed), "R001")
    assert len(result["engineering_requirements"]) == 2
    assert result["evidence_gaps"] == []
```

- [ ] **Step 2: 运行测试确认失败**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/test_scope_validation.py -v 2>&1 | tail -15
```

期望：`test_scope_violation_moved_to_evidence_gaps` FAIL（违规条目未被移除）

- [ ] **Step 3: 在 `normalize_agent_output()` 末尾、`obj["generated_at"]` 之前，加入范围校验**

找到以下代码块（orphan collapse 之后）：

```python
    obj["generated_at"] = datetime.now().isoformat(timespec="seconds")
```

在其**正上方**插入：

```python
    # ── 兜底范围校验：topic 必须在 allowed_engineering_aspects 中 ──
    allowed_topics = {
        a["topic"]
        for a in obj.get("allowed_engineering_aspects", []) or []
        if a.get("topic")
    }
    if allowed_topics:
        valid_reqs = []
        for req in obj["engineering_requirements"]:
            if req.get("topic", "") in allowed_topics:
                valid_reqs.append(req)
            else:
                obj.setdefault("evidence_gaps", []).append({
                    "related_requirement_id": req.get("id", ""),
                    "gap_type": "scope_violation",
                    "description": (
                        f"topic '{req.get('topic', '')}' 不在 allowed_engineering_aspects 列表中，"
                        "已从工程需求中移除。若确需覆盖该方面，请在原始需求中补充相应内容。"
                    ),
                    "suggested_document_update": "在原始需求中明确提及该工程方面。",
                })
        obj["engineering_requirements"] = valid_reqs
```

- [ ] **Step 4: 运行全部测试确认通过**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/ -v
```

期望：所有测试通过（`test_splitter_review.py`、`test_pipeline_passthrough.py`、`test_compact_context.py`、`test_scope_validation.py`）

- [ ] **Step 5: normalize_agent_output 接收 allowed_aspects 的传入口**

`normalize_agent_output` 从 `obj` 参数里读取 `allowed_engineering_aspects`，但目前 `call_deepseek` 节点的 prompt payload 没有把该字段写进去，需要在 `call_deepseek` node 里把 `allowed_engineering_aspects` 也带入 LLM 输入，同时在 `parse_and_validate` node 里把它附加回 `obj` 以供 `normalize_agent_output` 使用。

在 `engineering_requirement_agent.py` 的 `call_deepseek` 函数内，找到：

```python
        payload = {
            "original_requirement": state.get("requirement", {}),
            "retrieval_context": state.get("compact_context", {}),
        }
```

确认 `compact_context` 中已经包含 `allowed_engineering_aspects`（Task 6 已完成），LLM 会在 prompt 中看到该字段，无需额外修改。

在 `parse_and_validate` 函数内，找到 `obj = normalize_agent_output(obj, requirement_id)` 这行，
在其**之前**插入：

```python
            # 把 compact_context 中的 allowed_aspects 注入 obj，供范围校验使用
            compact = state.get("compact_context", {}) or {}
            obj["allowed_engineering_aspects"] = compact.get("allowed_engineering_aspects", [])
```

- [ ] **Step 6: 再次运行全部测试**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python -m pytest tests/ -v
```

期望：所有测试继续通过

- [ ] **Step 7: Commit**

```bash
git add cooling_rag_mg/engineering_requirement_agent.py tests/test_scope_validation.py
git commit -m "feat: normalize_agent_output scope validation — scope_violation moved to evidence_gaps"
```

---

## Task 9：集成冒烟验证

**Files:**
- Read: `scripts/13_smoke_test.py`（不修改，用于验证）

- [ ] **Step 1: 确认冒烟测试脚本可访问**

```bash
cd /mnt/d/cooling_rag_multigranular/cooling_rag_multigranular
python scripts/13_smoke_test.py 2>&1 | tail -20
```

期望：脚本正常完成，无 ImportError 或 AttributeError

- [ ] **Step 2: 检查拆分器新字段在实际输出中存在**

```bash
python -c "
import json, os, sys
# 读取最新一次 smoke test 或 batch 的检索结果
import glob
files = sorted(glob.glob('data/search_results/batch_*/all_requirements_results.json'))
if not files:
    print('No batch files found, skip')
    sys.exit(0)
with open(files[-1]) as f:
    data = json.load(f)
for req in data.get('requirements', [])[:2]:
    for sub in req.get('sub_requirements', [])[:2]:
        print(sub.get('sub_requirement_id'), '|', sub.get('source_phrase', '(missing)'), '|', sub.get('implication_type', '(missing)'))
"
```

期望：每条子需求输出 `source_phrase` 字段（可能为空字符串若使用 fallback，但字段应存在）

- [ ] **Step 3: 最终 commit**

```bash
git add .
git commit -m "chore: verify integration smoke test passes after scope redesign"
```

---

## 自检清单

- [x] **Spec coverage**
  - 拆分器 v2 prompt（Task 2）✓
  - 审核 Agent + REVIEW_PROMPT（Task 3）✓
  - 修订循环 max_rounds（Task 4）✓
  - `source_phrase` / `implication_type` 透传（Task 5）✓
  - `allowed_engineering_aspects` 字段（Task 6）✓
  - Agent prompt【F】节（Task 7）✓
  - `normalize_agent_output` 范围校验（Task 8）✓
  - `config.py` 新增字段（Task 1）✓

- [x] **Placeholder scan**：无 TBD / TODO，所有步骤含完整代码

- [x] **Type consistency**
  - `source_phrase: str` — 在 Task 2/3/4/5/6 中一致
  - `allowed_engineering_aspects: list[dict]` — 在 Task 6/7/8 中一致
  - `_review_aspects(raw_text: str, aspects: list[dict]) -> dict` — Task 3/4 一致
  - `_clean_aspects(subs: list) -> list[dict]` — Task 4 新增，Task 4 内部一致
