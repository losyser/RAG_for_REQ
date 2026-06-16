"""Tests for Phase 4 quality evaluation fixes."""
from unittest.mock import MagicMock


def _resp(content):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


# ── quality_judge: 5-dimension schema ────────────────────────────────────────

def test_dims_is_four_without_groundedness():
    from cooling_rag_mg.quality_judge import DIMS
    assert "groundedness" not in DIMS
    assert len(DIMS) == 4
    assert set(DIMS) == {"completeness", "actionability", "consistency", "verifiability"}


def test_parse_pairwise_handles_four_dims():
    from cooling_rag_mg.quality_judge import parse_pairwise
    raw = '{"completeness":"A","actionability":"B","consistency":"tie","verifiability":"A"}'
    result = parse_pairwise(raw)
    assert set(result.keys()) == {"completeness", "actionability", "consistency", "verifiability"}
    assert result["completeness"] == "A"
    assert result["actionability"] == "B"


def test_judge_pair_returns_four_dims():
    from cooling_rag_mg.quality_judge import judge_pair
    client = MagicMock()
    client.chat.completions.create.return_value = _resp(
        '{"completeness":"A","actionability":"tie","consistency":"tie","verifiability":"A"}'
    )
    result = judge_pair("原始需求", r_text="R内容", b0_text="B0内容",
                        r_on_left=True, client=client, model="qwen")
    assert set(result.keys()) == {"completeness", "actionability", "consistency", "verifiability"}
    assert "groundedness" not in result


def test_prompt_contains_actionability_guidance():
    from cooling_rag_mg.quality_judge import _PROMPT
    assert "待按" in _PROMPT or "待确认" in _PROMPT    # anti-specificity-bias instruction
    assert "groundedness" not in _PROMPT


# ── credibility_eval: OI fair split ─────────────────────────────────────────

def test_judge_over_inference_rag_uses_evidence_prompt():
    from cooling_rag_mg.credibility_eval import judge_over_inference
    client = MagicMock()
    client.chat.completions.create.return_value = _resp('{"over_inference": false}')
    result = judge_over_inference(
        shall="管路应采用铜镍合金。",
        source_requirement="管路需耐腐蚀",
        kb_passages=["copper-nickel alloy is preferred for seawater piping"],
        client=client, model="qwen", arm="rag",
    )
    assert result is False
    # check evidence was in the prompt
    call_content = client.chat.completions.create.call_args[1]["messages"][0]["content"]
    assert "copper-nickel" in call_content


def test_judge_over_inference_norag_omits_evidence_from_prompt():
    from cooling_rag_mg.credibility_eval import judge_over_inference
    client = MagicMock()
    client.chat.completions.create.return_value = _resp('{"over_inference": false}')
    judge_over_inference(
        shall="应按设计压力1.5倍做水压试验。",
        source_requirement="管路应定期检查完整性",
        kb_passages=[],         # no-RAG has no passages
        client=client, model="qwen", arm="no-rag",
    )
    call_content = client.chat.completions.create.call_args[1]["messages"][0]["content"]
    # no-RAG prompt should NOT have "证据（已检索到的支撑文本）" block
    assert "证据（已检索到的支撑文本）" not in call_content
    # but should include the fair-OI guidance
    assert "没有检索证据" in call_content or "无额外参考资料" in call_content


def test_judge_over_inference_empty_passages_uses_norag_prompt():
    """Empty kb_passages (even without arm kwarg) should trigger no-RAG path."""
    from cooling_rag_mg.credibility_eval import judge_over_inference
    client = MagicMock()
    client.chat.completions.create.return_value = _resp('{"over_inference": true}')
    result = judge_over_inference(
        shall="应在主机停机后冷却水泵继续运行10分钟。",
        source_requirement="停机后保护",
        kb_passages=[],     # empty → no-RAG path regardless of arm default
        client=client, model="qwen",
    )
    assert result is True
    call_content = client.chat.completions.create.call_args[1]["messages"][0]["content"]
    assert "证据（已检索到的支撑文本）" not in call_content


def test_judge_over_inference_returns_none_on_parse_failure():
    from cooling_rag_mg.credibility_eval import judge_over_inference
    client = MagicMock()
    client.chat.completions.create.return_value = _resp('{"result": "yes"}')  # wrong key
    result = judge_over_inference("shall", "source", [], client, "qwen")
    assert result is None


def test_judge_over_inference_returns_none_on_api_error():
    from cooling_rag_mg.credibility_eval import judge_over_inference
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("timeout")
    result = judge_over_inference("shall", "source", ["ev"], client, "qwen")
    assert result is None
