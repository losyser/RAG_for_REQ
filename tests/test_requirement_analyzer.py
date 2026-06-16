"""Tests for requirement_analyzer — all offline (no API calls)."""
from unittest.mock import MagicMock


def _resp(content: str):
    return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])


# ── parse_pairs ──────────────────────────────────────────────────────────────

def test_parse_pairs_valid():
    from cooling_rag_mg.requirement_analyzer import parse_pairs
    raw = '[{"component":"pipe","intent":"material"},{"component":"pipe","intent":"corrosion_protection"}]'
    pairs = parse_pairs(raw)
    assert ("pipe", "material") in pairs
    assert ("pipe", "corrosion_protection") in pairs


def test_parse_pairs_deduplicates():
    from cooling_rag_mg.requirement_analyzer import parse_pairs
    raw = '[{"component":"pipe","intent":"material"},{"component":"pipe","intent":"material"}]'
    assert len(parse_pairs(raw)) == 1


def test_parse_pairs_rejects_invalid_taxonomy_pair():
    from cooling_rag_mg.requirement_analyzer import parse_pairs
    # coolant × welding does not exist in taxonomy
    raw = '[{"component":"coolant","intent":"welding"}]'
    assert parse_pairs(raw) == []


def test_parse_pairs_handles_wrapped_dict():
    from cooling_rag_mg.requirement_analyzer import parse_pairs
    raw = '{"pairs":[{"component":"expansion_tank","intent":"level_control"}]}'
    pairs = parse_pairs(raw)
    assert ("expansion_tank", "level_control") in pairs


def test_parse_pairs_empty_on_bad_json():
    from cooling_rag_mg.requirement_analyzer import parse_pairs
    assert parse_pairs("not json at all") == []


def test_parse_pairs_empty_list():
    from cooling_rag_mg.requirement_analyzer import parse_pairs
    assert parse_pairs("[]") == []


# ── analyze_requirement ──────────────────────────────────────────────────────

def test_analyze_requirement_returns_valid_pairs():
    from cooling_rag_mg.requirement_analyzer import analyze_requirement
    client = MagicMock()
    client.chat.completions.create.return_value = _resp(
        '[{"component":"cooling_water_pump","intent":"redundancy"},'
        ' {"component":"cooling_water_pump","intent":"auto_start"}]'
    )
    pairs = analyze_requirement("海水泵应一用一备", client, model="ds")
    assert ("cooling_water_pump", "redundancy") in pairs
    assert ("cooling_water_pump", "auto_start") in pairs


def test_analyze_requirement_returns_empty_on_api_error():
    from cooling_rag_mg.requirement_analyzer import analyze_requirement
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("network error")
    assert analyze_requirement("任意需求", client, model="ds") == []


def test_analyze_requirement_filters_bad_pairs_from_llm():
    from cooling_rag_mg.requirement_analyzer import analyze_requirement
    client = MagicMock()
    # LLM hallucinated an invalid pair alongside a valid one
    client.chat.completions.create.return_value = _resp(
        '[{"component":"pipe","intent":"material"},'
        ' {"component":"sea_chest","intent":"nonexistent_intent"}]'
    )
    pairs = analyze_requirement("管路材料要求", client, model="ds")
    assert ("pipe", "material") in pairs
    assert all(i != "nonexistent_intent" for _, i in pairs)


# ── components_and_intents ───────────────────────────────────────────────────

def test_components_and_intents_splits_correctly():
    from cooling_rag_mg.requirement_analyzer import components_and_intents
    pairs = [("pipe", "material"), ("pipe", "corrosion_protection"),
             ("cooler", "cleaning")]
    comps, intents = components_and_intents(pairs)
    assert set(comps) == {"pipe", "cooler"}
    assert set(intents) == {"material", "corrosion_protection", "cleaning"}


def test_components_and_intents_preserves_order_deduplicates():
    from cooling_rag_mg.requirement_analyzer import components_and_intents
    pairs = [("pipe", "material"), ("pipe", "inspection"), ("pipe", "material")]
    comps, intents = components_and_intents(pairs)
    assert comps == ["pipe"]
    assert intents.count("material") == 1
