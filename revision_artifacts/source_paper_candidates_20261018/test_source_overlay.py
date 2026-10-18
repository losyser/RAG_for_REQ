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
    assert all(not r['enabled'] and r['conditions'] and r['raw_cells'] and r['project_applicability']=='unknown' for r in o['parameters'][:8])
    assert not o['sources'][1]['local_archive_complete']
    assert 'parent-reported' in o['sources'][1]['sha256_verification']


def test_mtu_initial_and_restoration_conditions_are_not_collapsed():
    rows={r['candidate_id']:r for r in overlay()['parameters']}
    initial=rows['MTU02E-P16-initial_fill'];restore=rows['MTU02E-P16-restore_after_loss_or_dilution']
    assert initial['value']==restore['value']==50
    assert initial['conditions'] != restore['conditions']
    assert ' OR ' in restore['conditions'][0]
    assert initial['unit']==restore['unit']=='% by volume'

def test_mtu_bounds_and_scope():
    rows={r['candidate_id']:r for r in overlay()['parameters']}
    low=rows['MTU02E-P16-minimum_antifreeze'];high=rows['MTU02E-P16-maximum_antifreeze']
    assert (low['operator'],low['value'])==('>=',40)
    assert (high['operator'],high['value'])==('<=',55)
    for r in overlay()['parameters'][8:]:
        assert r['model_scope']=='Series 1600 PowerPack'
        assert r['project_applicability']=='unknown' and not r['enabled']
        assert r['conditions'] and r['source_span']

def test_mtu_pure_water_exception_and_missing_source_continuation():
    rows={r['candidate_id']:r for r in overlay()['parameters']}
    assert rows['MTU02E-P16-pure_water']['operator']=='prohibited_without'
    assert 'approved corrosion inhibitor' in rows['MTU02E-P16-pure_water']['conditions'][0]
    assert 'A001070' in rows['MTU02E-P16-full_circuit_and_preservation']['source_span']
    assert 'dilution' in rows['MTU02E-P16-residual_dilution_check']['source_span']
