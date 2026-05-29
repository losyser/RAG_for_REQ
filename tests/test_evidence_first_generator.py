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
