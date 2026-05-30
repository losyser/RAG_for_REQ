import json
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

    with patch("cooling_rag_mg.config.DeepSeekConfig.make_client") as mk:
        mock_client = MagicMock()
        mk.return_value = mock_client
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

    with patch("cooling_rag_mg.config.DeepSeekConfig.make_client") as mk:
        mock_client = MagicMock()
        mk.return_value = mock_client
        mock_client.chat.completions.create.return_value = _mock_openai_response(review_json)

        result = _review_aspects("主机入口冷却水温度和流量应满足厂家要求。", aspects)

    assert result["passed"] is False
    assert "overall_feedback" in result
    assert result["overall_feedback"] != ""


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

    with patch("cooling_rag_mg.config.DeepSeekConfig.make_client") as mk:
        mock_client = MagicMock()
        mk.return_value = mock_client
        # First call = split, second call = review
        mock_client.chat.completions.create.side_effect = [
            _mock_openai_response(split_json),
            _mock_openai_response(review_json),
        ]
        result = split_requirement("R001", "船东", "系统应在连续运行等工况下稳定运行。")

    assert len(result) == 1
    assert result[0]["source_phrase"] == "连续运行"
    # Only 2 calls (1 split + 1 review)
    assert mock_client.chat.completions.create.call_count == 2


def test_split_with_review_retries_on_fail():
    """不通过时循环重试，第二轮通过后退出。"""
    from cooling_rag_mg.requirement_splitter import split_requirement

    def _split_resp(source_phrase):
        return _mock_openai_response(json.dumps({
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

    with patch("cooling_rag_mg.config.DeepSeekConfig.make_client") as mk:
        mock_client = MagicMock()
        mk.return_value = mock_client
        mock_client.chat.completions.create.side_effect = [
            _split_resp("不存在的词"),   # round 1 split
            fail_review,                 # round 1 review → fail
            _split_resp("温度"),         # round 2 split
            pass_review,                 # round 2 review → pass
        ]
        result = split_requirement("R002", "船东", "主机入口冷却水温度应满足厂家要求。")

    assert result[0]["source_phrase"] == "温度"
    assert mock_client.chat.completions.create.call_count == 4
