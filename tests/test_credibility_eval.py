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


def test_verify_claim_verdicts():
    from cooling_rag_mg.credibility_eval import verify_claim_against_kb

    def kb_search(q, k):
        return ["海水泵应一用一备，备用泵自动投入。"]

    def judge(claim, passages):
        return "support" if "一用一备" in claim else "not_found"

    assert verify_claim_against_kb("海水泵一用一备", kb_search, judge, top_k=3) == "support"
    assert verify_claim_against_kb("冷却水流量≥999 m3/h", kb_search, judge, top_k=3) == "not_found"


def test_verify_claim_no_passage_is_not_found():
    from cooling_rag_mg.credibility_eval import verify_claim_against_kb
    assert verify_claim_against_kb("任意", lambda q, k: [], lambda c, p: "support", top_k=3) == "not_found"


def test_score_shall_hard_soft():
    from cooling_rag_mg.credibility_eval import score_shall
    verdicts = {"c1": "support", "c2": "contradict", "c3": "not_found"}
    out = score_shall(
        shall="s",
        extract=lambda s: ["c1", "c2", "c3"],
        verify=lambda c: verdicts[c],
    )
    assert out["n_claims"] == 3
    assert out["h_hard"] == 1 / 3
    assert out["h_soft"] == 1 / 3
    assert out["hallucination"] == 2 / 3


def test_score_shall_no_claims_returns_none():
    from cooling_rag_mg.credibility_eval import score_shall
    out = score_shall(shall="s", extract=lambda s: [], verify=lambda c: "support")
    assert out["n_claims"] == 0
    assert out["h_hard"] is None and out["h_soft"] is None


def test_judge_over_inference_true_false():
    from cooling_rag_mg.credibility_eval import judge_over_inference
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _resp('{"over_inference": true}'),
        _resp('{"over_inference": false}'),
    ]
    assert judge_over_inference("shall 加了原始需求没要求的冗余", "原始需求", ["证据"], client, model="m") is True
    assert judge_over_inference("shall 忠于原始需求", "原始需求", ["证据"], client, model="m") is False


def test_judge_over_inference_none_on_failure():
    from cooling_rag_mg.credibility_eval import judge_over_inference
    client = MagicMock()
    client.chat.completions.create.side_effect = [Exception("boom")]
    assert judge_over_inference("s", "src", ["e"], client, model="m") is None
