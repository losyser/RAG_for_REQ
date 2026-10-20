import importlib.util
from pathlib import Path

def test_judge_error_not_misreported_as_missing_evidence(monkeypatch):
    spec=importlib.util.spec_from_file_location('evaluation59',Path('scripts/59_evaluate_v3.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    import cooling_rag_mg.llm_cache as cache
    def broken(*a,**k): raise RuntimeError('offline failure fixture')
    monkeypatch.setattr(cache,'cached_completion',broken)
    assert m._judge_claim_against_kb('claim',['passage'],None,'fixture')=='error'
    assert m._judge_claim_against_kb('claim',[],None,'fixture')=='not_found'

def test_posthoc_parser_does_not_read_verdict_from_reason():
    spec=importlib.util.spec_from_file_location('posthoc70',Path('scripts/70b_kb_verification_v4.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    assert not any(m.parse_verdicts('80°C | UNSUPPORTED | SUPPORTED is not applicable').values())
    assert m.parse_verdicts('80°C | UNVERIFIABLE | not SUPPORTED')['unverifiable']
