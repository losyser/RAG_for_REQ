"""Offline test launcher: isolate the legacy autouse cache and block networking."""
import os
from pathlib import Path
import socket
import sys

ROOT = Path(r"D:\cooling_rag_multigranular\cooling_rag_multigranular")
WORK = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
from diskcache import Cache
import cooling_rag_mg.llm_cache as cache
cache._cache = Cache(str(WORK / "isolated_test_cache"))


def offline(*args, **kwargs):
    raise RuntimeError("Network disabled for bounded optimization tests")


socket.socket.connect = offline
socket.socket.connect_ex = offline
socket.create_connection = offline
import pytest
args = sys.argv[1:] or [
    "tests/test_bounded_evidence_contracts.py",
    "tests/test_grade_classifier.py", "tests/test_grade_classifier_kb.py",
    "tests/test_kb_value_extractor.py", "tests/test_structured_req_generator.py",
    "tests/test_truncation_config.py", "tests/test_generation_token_limit.py",
    "tests/test_review_routing.py", "tests/test_revision_contracts.py",
    "tests/test_req_generation_v2.py", "tests/test_fill_empty_sets.py",
    "tests/test_evaluation_failure_contract.py", "tests/test_pipeline_passthrough.py",
    "tests/test_numeric_norm.py", "tests/test_grounding.py",
]
try:
    result = pytest.main(["-q", "-p", "no:cacheprovider", "--basetemp", str(WORK / "pytest_tmp_bounded"), *args])
finally:
    cache._cache.close()
raise SystemExit(result)
