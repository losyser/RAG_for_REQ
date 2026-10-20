"""Read-only saved-input replay; writes only this batch's diagnostic JSON."""
import collections
import copy
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import types

ROOT = Path(r"D:\cooling_rag_multigranular\cooling_rag_multigranular")
WORK = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
def offline(*a, **kw):
    raise RuntimeError("network disabled for saved-input replay")
socket.socket.connect = socket.socket.connect_ex = socket.create_connection = offline
from cooling_rag_mg import engineering_requirement_agent as current
from cooling_rag_mg.ui_evidence_contracts import diagnose_numeric_selection

baseline = types.ModuleType("ui_baseline_d0afe01")
code = subprocess.check_output(["git", "show", "d0afe01:cooling_rag_mg/engineering_requirement_agent.py"], cwd=ROOT).decode("utf-8")
exec(compile(code, "git:d0afe01:engineering_requirement_agent.py", "exec"), baseline.__dict__)

contexts = []
for path in sorted((ROOT / "data/search_results").glob("batch_*/all_requirements_results.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    for record in data.get("requirements", []):
        old = baseline.compact_requirement_context(copy.deepcopy(record))
        new = current.compact_requirement_context(copy.deepcopy(record))
        before = {e["id"]: e for e in old["supported_evidence"]}
        after = {e["id"]: e for e in new["supported_evidence"]}
        contexts.append({"path": str(path.relative_to(ROOT)), "source": record.get("requirement_id"),
            "same_selected_ids": list(before) == list(after),
            "before_ellipsis_only": sum(e["text"] == "..." for e in before.values()),
            "after_nonempty_real_text": sum(e["text"] not in ("", "...") for e in after.values()),
            "after_empty_over_budget": sum(not e["text"] and e.get("_context_status") == "partial_unknown" for e in after.values()),
            "after_partial": sum(e.get("_context_status") == "partial_unknown" for e in after.values()),
            "selected": len(after),
            "examples": [{"id": eid, "before": before[eid]["text"], "after": ev["text"], "context_status": ev["_context_status"]} for eid, ev in list(after.items())[:2]]})

normalizations = []
for path in sorted((ROOT / "data/search_results").glob("batch_*/engineering_requirements_*/engineering_requirements.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    retrieval_path = path.parent.parent / "all_requirements_results.json"
    retrieval = json.loads(retrieval_path.read_text(encoding="utf-8")) if retrieval_path.exists() else {}
    lookup = {r.get("requirement_id"): r for r in retrieval.get("requirements", [])}
    for record in data.get("requirement_sets", []):
        rid = record.get("source_requirement_id", "")
        result = {"path": str(path.relative_to(ROOT)), "source": rid}
        try:
            old = baseline.normalize_agent_output(copy.deepcopy(record), rid)
            result["before_rows"] = len(old["engineering_requirements"])
        except Exception as exc:
            result["before_error"] = str(exc)
        scope = current.compact_requirement_context(lookup[rid])["supported_evidence"] if rid in lookup else None
        try:
            new = current.normalize_agent_output(copy.deepcopy(record), rid, evidence_scope=scope)
            result.update({"after_rows": len(new["engineering_requirements"]), "reference_scope_available": scope is not None,
                "issues": dict(collections.Counter(i["code"] for i in new["_validation_report"]["issues"])),
                "semantic_support": new["_validation_report"]["semantic_support"]})
        except Exception as exc:
            result["after_error"] = str(exc)
        normalizations.append(result)

kb = {u["id"]: u for u in map(json.loads, (ROOT / "data/processed/evidence_units_v3_audited.jsonl").read_text(encoding="utf-8").splitlines())}
v4 = json.loads((ROOT / "data/search_results/exp_v4/rag_v4_results.json").read_text(encoding="utf-8"))
selection = []
for record in v4["result_sets"]:
    ev = [{**kb[eid], "_extracted_values": values} for eid, values in record.get("_evidence_values", {}).items() if eid in kb]
    selection.append({"source": record["source_requirement_id"], **diagnose_numeric_selection(ev)})

manifest = json.loads((WORK / "protected_before.json").read_text(encoding="utf-8"))
changed = [p for p, h in manifest.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h]
tracked = json.loads((WORK / "tracked_before.json").read_text(encoding="utf-8"))
allowed = {"cooling_rag_mg/engineering_requirement_agent.py", "cooling_rag_mg/coverage_retrieval.py"}
unrelated = [p for p, h in tracked.items() if p not in allowed and hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != h]
metadata_missing = {field: sum(not (u.get(field) or (u.get("metadata") or {}).get(field)) for u in kb.values()) for field in ("source_document", "location", "manufacturer", "engine_model", "applicable_condition")}
report = {"baseline": "d0afe01", "no_generation": True, "contexts": contexts, "normalizations": normalizations,
    "selection_policy_unchanged": selection, "kb_metadata_missing_counts_not_error_labels": metadata_missing,
    "kb_units": len(kb), "protected_files": len(manifest), "protected_changed": changed, "unrelated_tracked_changed": unrelated,
    "summary": {"contexts": len(contexts), "selected_evidence_occurrences": sum(r["selected"] for r in contexts),
        "before_ellipsis_only": sum(r["before_ellipsis_only"] for r in contexts),
        "after_nonempty_real_text": sum(r["after_nonempty_real_text"] for r in contexts),
        "after_empty_over_budget": sum(r["after_empty_over_budget"] for r in contexts),
        "all_selected_ids_unchanged": all(r["same_selected_ids"] for r in contexts),
        "saved_output_sets": len(normalizations), "before_errors": sum("before_error" in r for r in normalizations),
        "after_errors": sum("after_error" in r for r in normalizations),
        "reference_scope_available_sets": sum(r.get("reference_scope_available", False) for r in normalizations),
        "sets_with_reference_risks": sum(bool(r.get("issues", {}).get("reference_not_in_supplied_support_context")) for r in normalizations),
        "v4_sets_with_omitted_non_numeric": sum(bool(r["omitted_non_numeric_ids"]) for r in selection)}}
(WORK / "SAVED_REPLAY.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
print("metadata missing:", metadata_missing)
assert not changed and not unrelated
