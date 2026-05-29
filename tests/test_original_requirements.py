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
