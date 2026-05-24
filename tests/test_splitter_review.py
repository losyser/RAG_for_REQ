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
