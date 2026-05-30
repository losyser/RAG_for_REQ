from cooling_rag_mg.json_utils import loads_lenient


def test_plain_json():
    assert loads_lenient('{"a":1}') == {"a": 1}


def test_strips_json_fence():
    raw = '```json\n{"keywords":["x"],"sentences":["y"]}\n```'
    assert loads_lenient(raw) == {"keywords": ["x"], "sentences": ["y"]}


def test_strips_bare_fence():
    assert loads_lenient('```\n{"a":2}\n```') == {"a": 2}


def test_extracts_object_with_surrounding_prose():
    raw = '好的，结果如下：\n{"a":3}\n以上。'
    assert loads_lenient(raw) == {"a": 3}


def test_empty_and_garbage_return_empty_dict():
    assert loads_lenient("") == {}
    assert loads_lenient("not json at all") == {}
    assert loads_lenient(None) == {}
