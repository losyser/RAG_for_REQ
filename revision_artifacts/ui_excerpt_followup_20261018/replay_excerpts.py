"""Compare exact e139d8a compaction with fragment rescue, without model calls."""
from pathlib import Path
from types import ModuleType, SimpleNamespace
import hashlib, json, socket, statistics, subprocess, sys

ROOT = Path(r"D:\cooling_rag_multigranular\cooling_rag_multigranular")
WORK = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); sys.dont_write_bytecode = True
def offline(*a, **k):
    raise RuntimeError("network blocked in replay")
socket.socket.connect = socket.socket.connect_ex = socket.create_connection = offline
from cooling_rag_mg import engineering_requirement_agent as current

def old_module(name, file):
    module = ModuleType(name); module.__package__ = "cooling_rag_mg"
    source = subprocess.check_output(["git", "show", "e139d8a:" + file], cwd=ROOT).decode("utf-8")
    exec(compile(source, "git:e139d8a:" + file, "exec"), module.__dict__)
    return module
old_contract = old_module("old_ui_contracts", "cooling_rag_mg/ui_evidence_contracts.py")
old = old_module("old_ui_agent", "cooling_rag_mg/engineering_requirement_agent.py")
old.retain_ui_evidence = old_contract.retain_ui_evidence
old.prepare_ui_output = old_contract.prepare_ui_output
old.finish_ui_audit = old_contract.finish_ui_audit

captured = []
current.get_config = lambda: SimpleNamespace(deepseek=SimpleNamespace(enabled=True, make_client=lambda: object(), model="offline", temperature=0, max_tokens_requirement_agent=1000))
def completion(*a, **kw):
    captured.append(sum(len(m["content"]) for m in kw["messages"]))
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"engineering_requirements":[]}'))])
current.cached_completion = completion
current.repair_json_with_deepseek = offline
graph = current.build_graph()
rows, lengths = [], []
for path in sorted((ROOT / "data/search_results").glob("batch_*/all_requirements_results.json")):
    for record in json.loads(path.read_text(encoding="utf-8")).get("requirements", []):
        before, after = old.compact_requirement_context(record), current.compact_requirement_context(record)
        old_by_id = {e["id"]: e for e in before["supported_evidence"]}
        source = {}
        for sub in record.get("sub_requirements", []):
            for ev in sub.get("selected_results", []):
                if (ev.get("llm_judge") or {}).get("support_type") in ("direct", "indirect"):
                    source.setdefault(ev["id"], ev.get("text") or "")
        ev_rows = []
        for ev in after["supported_evidence"]:
            raw = source[ev["id"]]
            exact = ev["text"] == "\n\n".join(raw[a:b] for a,b in ev["_source_text_spans"])
            assert exact and hashlib.sha256(raw.encode("utf-8")).hexdigest() == ev["_source_text_sha256"]
            assert len(ev["text"]) <= ev["_text_budget_chars"]
            previous = old_by_id[ev["id"]]["text"]
            if not previous:
                lengths.append(len(raw))
            ev_rows.append({"id": ev["id"], "source_chars": len(raw), "budget_chars": ev["_text_budget_chars"],
                "before_chars": len(previous), "after_chars": len(ev["text"]), "before_nonempty_preserved": not previous or previous == ev["text"],
                "fragment_fallback": ev["_fragment_fallback"], "boundary": ev["_fragment_boundary"],
                "status": ev["_context_status"], "spans": ev["_source_text_spans"], "source_sha256": ev["_source_text_sha256"], "exact_source_match": exact})
        count = len(captured)
        result = graph.invoke({"requirement": {"requirement_id": record.get("requirement_id"), "requirement_text": record.get("raw_requirement_text", "")}, "retrieval_context": record, "errors": []})
        rows.append({"path": str(path.relative_to(ROOT)), "source": record.get("requirement_id"), "evidence": ev_rows,
            "before_retained_chars": sum(e["before_chars"] for e in ev_rows), "after_retained_chars": sum(e["after_chars"] for e in ev_rows),
            "selected_ids_unchanged": list(old_by_id) == [e["id"] for e in ev_rows],
            "total_prompt_chars": captured[-1] if len(captured) > count else None,
            "blocked_by_total_budget": len(captured) == count})
all_e = [e for row in rows for e in row["evidence"]]
summary = {"contexts": len(rows), "no_supported_evidence_contexts": sum(not r["evidence"] for r in rows),
    "before_all_body_empty_with_evidence": sum(bool(r["evidence"]) and r["before_retained_chars"] == 0 for r in rows),
    "after_all_body_empty_with_evidence": sum(bool(r["evidence"]) and r["after_retained_chars"] == 0 for r in rows),
    "before_empty_bodies": sum(e["before_chars"] == 0 for e in all_e), "after_empty_bodies": sum(e["after_chars"] == 0 for e in all_e),
    "all_previous_nonempty_bodies_preserved": all(e["before_nonempty_preserved"] for e in all_e),
    "all_selected_ids_unchanged": all(r["selected_ids_unchanged"] for r in rows),
    "before_total_retained_chars": sum(r["before_retained_chars"] for r in rows), "after_total_retained_chars": sum(r["after_retained_chars"] for r in rows),
    "previously_omitted_source_lengths": {"min": min(lengths), "median": statistics.median(lengths), "max": max(lengths)},
    "budget_chars": sorted(set(e["budget_chars"] for e in all_e)), "prompt_chars_min": min(captured), "prompt_chars_max": max(captured),
    "total_prompt_char_cap": current.UI_MAX_PROMPT_CHARS, "contexts_blocked_by_cap": sum(r["blocked_by_total_budget"] for r in rows)}
manifest_path = WORK / "protected_before.json"
if not manifest_path.exists():
    manifest_path = ROOT / "revision_artifacts/ui_optimization_20261018/protected_before.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
changed = [p for p,h in manifest.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h]
report = {"baseline": "e139d8a", "summary": summary, "contexts": rows, "protected_files": len(manifest), "protected_changed": changed,
          "interpretation": "Structural replay and mock node calls only; fragments are not condition-complete or semantically verified."}
(WORK / "EXCERPT_REPLAY.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
assert not changed and summary["all_previous_nonempty_bodies_preserved"] and summary["all_selected_ids_unchanged"]
