"""Pure stdlib, offline. Run beside ITEM_ALIGNMENT.json and REPORT.json."""
import json
from pathlib import Path
from fractions import Fraction
HERE=Path(__file__).resolve().parent
rows=json.loads((HERE/'ITEM_ALIGNMENT.json').read_text(encoding='utf8'))
reported=json.loads((HERE/'REPORT.json').read_text(encoding='utf8'))
selected=[r for r in rows if r['included_in_30_agreement']]
assert len(selected)==30 and len(rows)==31
output={}
for dim in ['support','applicability','verifiability','faithfulness']:
    labels=reported['metrics'][dim]['labels']
    matrix={m:{h:0 for h in labels} for m in labels}
    weights=[Fraction(r['stratum_population'],r['stratum_sample_count']) for r in selected]
    agreements=[r['machine_raw'][dim]==r['human_normalized'][dim] for r in selected]
    for r in selected:matrix[r['machine_raw'][dim]][r['human_normalized'][dim]]+=1
    numerator=sum((w for w,a in zip(weights,agreements) if a),Fraction(0))
    denominator=sum(weights,Fraction(0))
    assert denominator==440
    expected=reported['metrics'][dim]
    assert matrix==expected['confusion_matrix']
    assert sum(agreements)==expected['sample_agree']
    assert str(numerator/denominator)==expected['weighted_agreement_exact']
    output[dim]={'agree':sum(agreements),'n':30,'unweighted':float(Fraction(sum(agreements),30)),'weighted_numerator_exact':str(numerator),'weighted_denominator_exact':str(denominator),'weighted_agreement':float(numerator/denominator),'matrix_rows_machine_columns_human':matrix}
print(json.dumps(output,ensure_ascii=False,indent=2))
