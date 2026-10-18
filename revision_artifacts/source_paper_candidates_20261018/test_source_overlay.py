"""Regression fixtures for reviewed grid bindings; not an OCR accuracy study."""
import copy,json
from pathlib import Path
import pytest
from build_source_overlay import cell
W=Path(__file__).resolve().parent
def overlay():return json.loads((W/'source_corrections_candidate.json').read_text('utf8'))
@pytest.mark.parametrize('dash',['-','–','—',''])
def test_blank_bound_is_not_a_sign(dash):
    assert cell(dash)['value'] is None
    assert cell('100°C3)')['value']==100
    assert cell('-37°C')['value']==-37
def test_grid_keeps_alarm_and_preheat_rows_separate():
    rows=overlay()['parameters'];alarm,preheat=rows[3:5]
    assert alarm['interface']=='3111, TE3190'
    assert alarm['min'] is None and alarm['max']==100
    assert 'alarm' in alarm['conditions'][0]
    assert preheat['interface']=='3121 (3102), TE3145'
    assert (preheat['min'],preheat['max'])==(60,80)
    assert 'before start' in preheat['conditions'][0]
def test_nominal_is_not_a_lower_limit():
    jacket=overlay()['parameters'][2]
    assert jacket['nominal']==90 and jacket['min'] is None and jacket['max'] is None
    assert 'SaCoS' in jacket['conditions'][0]
def test_variants_do_not_cross_models_or_pressure_type():
    loss,rise=overlay()['parameters'][6:8]
    assert loss['variants'][0]['models']==['6L','8L']
    assert loss['variants'][0]['value']==1.1
    assert rise['variants'][0]['models']==['6L']
    assert rise['variants'][0]['value']==3.6
    assert 'nominal flow rate' in loss['conditions'][0]
    assert 'nominal speed' in rise['conditions'][0]
def test_inactive_and_unknown_are_not_promoted():
    o=overlay();assert not o['active'] and not o['main_KB_mutation']
    assert o['quarantine_retained']==['E-HT-COMP-036']
    assert all(not r['enabled'] and r['conditions'] and r['raw_cells'] and r['project_applicability']=='unknown' for r in o['parameters'])
    assert o['sources'][1]['sha256'] is None and not o['sources'][1]['parameters']
