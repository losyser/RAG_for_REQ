"""cooling_rag_mg — multi-granular RAG for ship cooling water requirements."""
from __future__ import annotations
import os
import random


def seed_everything(seed: int) -> None:
    """Set seeds for Python random, numpy, torch, and FAISS thread count.

    Call once at the top of any script that needs deterministic behaviour.
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    try:
        import faiss
        faiss.omp_set_num_threads(1)
    except (ImportError, AttributeError):
        pass


__all__ = ["seed_everything"]
