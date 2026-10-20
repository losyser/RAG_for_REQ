# tests/test_ea_notes.py
"""The EA/XMI export must carry the derivation type and the review route in the
element notes, so the exported diagram shows not only the grade but also why each
requirement is sent to a given review tier."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("ea", Path("scripts/92_export_ea_native_xmi.py"))
ea = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ea)


def test_er_notes_carry_derivation_and_route():
    ns = ea.er_notes(
        "TCV set point 79 °C", "79 °C nominal", "B", "Test", "E-LT-COMP-006",
        derivation="Direct", route="ENGINEER_CONFIRM",
        route_reason="cites manufacturer/operational guidance only (tier-b)",
    )
    assert "Grade: B" in ns
    assert "Derivation: Direct" in ns
    assert "Route: ENGINEER_CONFIRM" in ns
    assert "tier-b" in ns


def test_er_notes_deferred_item():
    ns = ea.er_notes(
        "alarm", "as specified", "C", "Inspection", "",
        derivation="Deferred", route="OPEN_ITEM",
        route_reason="value deferred to named source document",
    )
    assert "Derivation: Deferred" in ns
    assert "Route: OPEN_ITEM" in ns
