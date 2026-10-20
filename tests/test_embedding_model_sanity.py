# Regression: D:/models/bge-m3 shipped without root-level tokenizer files, so transformers built a
# degenerate tokenizer that mapped every Chinese sentence to one unknown token (identical embeddings).
import os

import pytest

MODEL = os.getenv("BGE_M3_MODEL_PATH", "D:/models/bge-m3")


@pytest.mark.skipif(not os.path.isdir(MODEL), reason="embedding model not available")
def test_bge_m3_tokenizer_splits_chinese_and_embeddings_differ():
    import numpy as np
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(MODEL, device="cpu")
    assert len(m.tokenizer.tokenize("冷却水温度高报警")) > 1
    e = m.encode(["冷却水温度高报警", "膨胀水箱液位"], normalize_embeddings=True)
    assert float(e[0] @ e[1]) < 0.95
