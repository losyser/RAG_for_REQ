"""Phase 3：证据优先生成。B0 与 R 共用同一 system base，唯一差别 = R 的证据块。"""


def test_b0_and_r_share_identical_system():
    from cooling_rag_mg.evidence_first_generator import build_generation_messages
    sub = {"sub_requirement_id": "OR001-01", "text": "海水泵应具备冗余"}
    m_b0 = build_generation_messages(sub, evidence_texts=None, source_requirement="原始需求X")
    m_r = build_generation_messages(sub, evidence_texts=["证据A", "证据B"], source_requirement="原始需求X")
    # 单变量：system 完全一致；安全条款在两边都在
    assert m_b0[0]["role"] == "system" and m_r[0]["role"] == "system"
    assert m_b0[0]["content"] == m_r[0]["content"]
    assert "不得编造" in m_b0[0]["content"]


def test_r_user_message_carries_evidence_block():
    from cooling_rag_mg.evidence_first_generator import build_generation_messages
    sub = {"sub_requirement_id": "OR001-01", "text": "海水泵应具备冗余"}
    m_r = build_generation_messages(sub, evidence_texts=["海水泵一用一备", "备用泵自动投入"], source_requirement="X")
    user = m_r[1]["content"]
    assert "海水泵应具备冗余" in user          # 共享子需求上下文
    assert "海水泵一用一备" in user            # 证据注入
    assert "备用泵自动投入" in user
    assert "证据" in user                       # 证据块标记


def test_b0_user_message_has_no_evidence_block():
    from cooling_rag_mg.evidence_first_generator import build_generation_messages
    sub = {"sub_requirement_id": "OR001-01", "text": "海水泵应具备冗余"}
    m_b0 = build_generation_messages(sub, evidence_texts=None, source_requirement="X")
    user = m_b0[1]["content"]
    assert "海水泵应具备冗余" in user          # 共享子需求上下文
    assert "证据：" not in user                 # 无证据块（唯一差别）


def test_should_abstain_only_R_without_evidence():
    from cooling_rag_mg.evidence_first_generator import should_abstain
    # R 无证据 → 弃权；R 有证据 → 不弃权；B0 永不弃权
    assert should_abstain(arm="R", evidence_texts=[]) is True
    assert should_abstain(arm="R", evidence_texts=["e"]) is False
    assert should_abstain(arm="B0", evidence_texts=[]) is False


from unittest.mock import MagicMock


def _resp(content):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))], model="qwen")


def test_R_returns_none_when_abstains():
    from cooling_rag_mg.evidence_first_generator import generate_for_sub
    out = generate_for_sub(
        {"sub_requirement_id": "OR001-01", "text": "x"}, evidence_ids=[], evidence_texts=[],
        source_requirement="src", arm="R", client=MagicMock(), model="qwen",
    )
    assert out is None


def test_R_generates_and_attaches_evidence_ids():
    from cooling_rag_mg.evidence_first_generator import generate_for_sub
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"engineering_requirements":[{"shall_statement":"海水泵应一用一备。","verification_method":"inspection"}]}')
    ]
    out = generate_for_sub(
        {"sub_requirement_id": "OR001-01", "text": "海水泵冗余"},
        evidence_ids=["E-A-001", "E-A-002"], evidence_texts=["一用一备", "自动投入"],
        source_requirement="src", arm="R", client=client, model="qwen",
    )
    assert len(out) == 1
    assert out[0]["shall_statement"] == "海水泵应一用一备。"
    assert out[0]["evidence_ids"] == ["E-A-001", "E-A-002"]


def test_skips_non_dict_engineering_requirements():
    """LLM 偶尔把 engineering_requirements 里塞非 dict 元素（字符串等）——跳过，不崩。"""
    from cooling_rag_mg.evidence_first_generator import generate_for_sub
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"engineering_requirements":["误返回的字符串", {"shall_statement":"正常一条。"}]}')
    ]
    out = generate_for_sub(
        {"sub_requirement_id": "OR001-01", "text": "x"}, evidence_ids=["E1"], evidence_texts=["e"],
        source_requirement="src", arm="R", client=client, model="qwen",
    )
    assert len(out) == 1
    assert out[0]["shall_statement"] == "正常一条。"
    assert out[0]["evidence_ids"] == ["E1"]


def test_non_list_engineering_requirements_returns_empty():
    """engineering_requirements 不是 list（模型乱返回）→ 返回 []，不崩。"""
    from cooling_rag_mg.evidence_first_generator import generate_for_sub
    client = MagicMock()
    client.chat.completions.create.side_effect = [_resp('{"engineering_requirements": "not a list"}')]
    out = generate_for_sub(
        {"sub_requirement_id": "OR001-01", "text": "x"}, evidence_ids=[], evidence_texts=[],
        source_requirement="src", arm="B0", client=client, model="qwen",
    )
    assert out == []


def test_B0_attaches_empty_evidence_ids():
    from cooling_rag_mg.evidence_first_generator import generate_for_sub
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"engineering_requirements":[{"shall_statement":"海水泵宜冗余。"}]}')
    ]
    out = generate_for_sub(
        {"sub_requirement_id": "OR001-01", "text": "海水泵冗余"},
        evidence_ids=[], evidence_texts=[],
        source_requirement="src", arm="B0", client=client, model="qwen",
    )
    assert len(out) == 1
    assert out[0]["evidence_ids"] == []
