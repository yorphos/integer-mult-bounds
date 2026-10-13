#!/usr/bin/env python3
"""Exact primitive-prefix grid certificate for the admitted PR1042 panels.
Prepared with substantial OpenAI assistance. Apache-2.0.
"""
import argparse
import importlib.util
import json
from fractions import Fraction as Q
from pathlib import Path

spec = importlib.util.spec_from_file_location('independent_pr1042',Path(__file__).with_name('verify.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def inspect(word, direction):
    width = 2*word['v']+word['R']
    registers = [('L',r) for r in range(width)]+[('W',0)]
    rows = {r:{j:Q(1)} for j,r in enumerate(registers)}
    positive = dict.fromkeys(registers,Q(1))
    exact_peak = positive_peak = Q(1)
    depth = 0; witness = None; count = 0
    events = [audit.panel_event(op,direction) for op in word['compensation']]
    for index, primitive in enumerate(audit.primitive_stream(events)):
        count += 1
        tag, dst = primitive[:2]
        if tag == 'clear':
            rows[dst] = {}; positive[dst] = Q(0)
        elif tag == 'scale':
            q = primitive[2]
            rows[dst] = {j:q*x for j,x in rows[dst].items()}
            positive[dst] *= abs(q)
        else:
            audit.require(tag == 'add','panel primitive domain')
            src,q = primitive[2:]
            rows[dst] = audit.add_row(rows[dst],rows[src],q)
            positive[dst] += abs(q)*positive[src]
        exact_peak = max(exact_peak,sum((abs(x) for x in rows[dst].values()),Q(0)))
        positive_peak = max(positive_peak,positive[dst])
        for column,x in rows[dst].items():
            d = x.denominator.bit_length()-1
            audit.require(x.denominator == 1<<d,'dyadic dependency')
            if d > depth:
                depth = d; witness = {'primitive':index,'register':list(dst),'input_column':column,'coefficient':str(x)}
    audit.require(not rows['W',0], 'arbitrary coefficient workspace erased')
    extra = 0
    while Q(1<<extra) < exact_peak:
        extra += 1
    return {'logical_registers':width,'arbitrary_columns':len(registers),'single_real_primitives':count,
            'complex_primitives_per_coordinate':2*count,'primitive_count_for_512_complex_coordinates':1024*count,
            'minimal_common_guard_bits':depth,'guard_depth_witness':witness,
            'exact_row_l1_peak':str(exact_peak),'positive_l1_peak':str(positive_peak),
            'stored_intermediate_width_extra_over_payload_upper':depth+extra,'coefficient_workspace_erased':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-local',type=Path,required=True)
    parser.add_argument('--candidate-local',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();audit.require(not a.out.exists(),'fresh grid receipt')
    bw,bp=audit.read_local(a.baseline_local);cw,cp=audit.read_local(a.candidate_local)
    audit.check_boundary(bw,bp,cw,cp);audit.check_panel(bw,cw)
    r={'status':'PASS_INDEPENDENT_PR1042_PANEL_GRID','baseline_word_sha256':audit.digest(bw),
       'candidate_word_sha256':audit.digest(cw),'panels':{label:{d:inspect(w,d) for d in audit.BASE_PROGRAMS}
       for label,w in [('baseline',bw),('candidate',cw)]},
       'scope':'Exact primitive-prefix grid and worst-case growth, including coefficient work; not a runtime measurement.'}
    with a.out.open('x') as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
    print(r['status'])


if __name__=='__main__':main()
