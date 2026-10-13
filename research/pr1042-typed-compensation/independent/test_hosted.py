#!/usr/bin/env python3
"""Actual-file mutations of a completed PR1042 hosted replay.
Prepared with substantial OpenAI assistance. Apache-2.0.
"""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile

spec=importlib.util.spec_from_file_location('independent_pr1042_hosted',Path(__file__).with_name('check_hosted.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


def write_replacement(path, value):
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    if path.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
    temporary=path.with_name(path.name+'.mutant-tmp')
    with temporary.open('xb') as f:f.write(raw)
    os.replace(temporary,path)  # Never modify the inode shared with the real evidence.


def inventory(root):
    return {p.relative_to(root).as_posix():audit.sha(p) for p in root.rglob('*') if p.is_file()}


def baseline_controls(root):
    """Coherently rehash corruptions so merely checking digest edges cannot pass."""
    root=Path(root)
    baseline_before={n:audit.sha(root/n) for n in audit.BASELINE_BINDINGS}
    required=set(audit.BASELINE_BINDINGS)|set(audit.SELECTED_MEMBERS)
    for name in ('CANONICAL-WORD.json.gz','LOCAL-PROGRAMS.json.gz','CLIFFORD-REVIEW.json','SCALAR-FRAME-AUDIT.json','INDEPENDENT-LOCAL-REPLAY.json'):
        required.add('t16/global/base/providers/gauge44/'+name)
    review='slots/local/CLIFFORD-REVIEW.json';scalar='slots/local/SCALAR-FRAME-AUDIT.json'
    plan='t16/global/PLAN.json';tpl='t16/global/hosted/GLOBAL-TEMPLATE.json.gz'
    inv='t16/global/audit/PREFIX-AND-INVOICE.json';asm='t16/ASSEMBLY.json'
    cases=[
      ('changed_native_exact_columns','slots/local/INDEPENDENT-LOCAL-REPLAY.json',lambda d:d['local']['forward'].__setitem__('all_exact_columns',703),True),
      ('changed_native_payload','slots/local/CANONICAL-WORD.json.gz',lambda d:d.__setitem__('R',d['R']+1),True),
      ('changed_review_mathematics',review,lambda d:d.__setitem__('frames',d['frames']+1),True),
      ('changed_review_source',scalar,lambda d:d.__setitem__('input_content_sha256','0'*64),True),
      ('negative_seconds',review,lambda d:d.__setitem__('seconds',-1),True),
      ('nonfinite_seconds',scalar,lambda d:d.__setitem__('seconds',float('inf')),True),
      ('boolean_seconds',scalar,lambda d:d.__setitem__('seconds',True),True),
      ('extra_timing_field',review,lambda d:d.__setitem__('elapsed_seconds',0),True),
      ('unbound_plan_reference',plan,lambda d:d['provider_registry']['gauge44']['artifact_sha256'].__setitem__('CLIFFORD-REVIEW.json','0'*64),False),
      ('unbound_template_reference',tpl,lambda d:d['async_schedule'].__setitem__('source_plan_sha256','0'*64),False),
      ('coherently_rehashed_owner_corruption',tpl,lambda d:d['calls'][0]['owners'][224].__setitem__(0,d['calls'][0]['owners'][224][0]-1),True),
      ('coherently_rehashed_profile_corruption',asm,lambda d:d['complex_profile'].__setitem__(next(iter(d['complex_profile'])),0),True),
      ('coherently_rehashed_numeric_corruption',inv,lambda d:d.__setitem__('conservative_pervertex_used',d['conservative_pervertex_used']-1),True),
    ]
    results=[]
    for name,relative,mutate,rehash in cases+[('valid_elapsed_time_refresh',review,lambda d:d.__setitem__('seconds',0.25),True),('valid_native_recompression','slots/local/CANONICAL-WORD.json.gz',lambda d:None,True),('valid_program_recompression','slots/local/LOCAL-PROGRAMS.json.gz',lambda d:None,True)]:
        with tempfile.TemporaryDirectory(prefix='pr1042-baseline-control-',dir=root.resolve().parent) as temp:
            work=Path(temp)/'work'
            for member in required:
                dest=work/member;dest.parent.mkdir(parents=True,exist_ok=True);os.link(root/member,dest)
            path=work/relative;value=audit.read(path);mutate(value);write_replacement(path,value)
            if name in ('valid_native_recompression','valid_program_recompression'):
                audit.require(audit.sha(path)!=audit.sha(root/relative),'nonvacuous recompression control')
            if rehash:
                for member,rule in audit.BASELINE_BINDINGS.items():
                    value=audit.read(work/member)
                    for pointer,dependency,kind in rule['bound_references']:
                        parent,key=audit.pointer_parent(value,pointer)
                        parent[key]=audit.sha(work/dependency) if kind=='raw' else audit.content_sha(audit.read(work/dependency))
                    if rule['bound_references']:write_replacement(work/member,value)
                for review_name in ('CANONICAL-WORD.json.gz','LOCAL-PROGRAMS.json.gz','CLIFFORD-REVIEW.json','SCALAR-FRAME-AUDIT.json','INDEPENDENT-LOCAL-REPLAY.json'):
                    write_replacement(work/'t16/global/base/providers/gauge44'/review_name,audit.read(work/'slots/local'/review_name))
            try:audit.bind_selected_baseline(work)
            except ValueError as error:
                if name.startswith('valid_'):raise
                results.append({'name':name,'reason':str(error)})
            else:audit.require(name.startswith('valid_'),'baseline mutation accepted: '+name)
        print('ACCEPT' if name.startswith('valid_') else 'REJECT',name,flush=True)
    audit.require({n:audit.sha(root/n) for n in audit.BASELINE_BINDINGS}==baseline_before,'original baseline evidence unchanged')
    return {'controls_rejected':results,'valid_elapsed_time_refresh_accepted':True,'valid_native_recompression_accepted':True,'valid_program_recompression_accepted':True,'original_baseline_unchanged':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-replay',type=Path,required=True)
    parser.add_argument('--candidate-local',type=Path,required=True)
    parser.add_argument('--hosted-work',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();audit.require(not a.out.exists(),'fresh mutation receipt')
    before=inventory(a.hosted_work)
    original=audit.check(a.baseline_replay,a.candidate_local,a.hosted_work)
    baseline_mutations=baseline_controls(a.baseline_replay)
    inv='global/audit/PREFIX-AND-INVOICE.json';tpl='global/hosted/GLOBAL-TEMPLATE.json.gz';asm='ASSEMBLY.json'
    program='global/base/providers/gauge44/LOCAL-PROGRAMS.json.gz'
    mutations=[
      ('omitted_call',tpl,lambda d:d['calls'].pop()),
      ('wrong_physical_helper_route',tpl,lambda d:d['calls'][0]['owners'][224].__setitem__(0,d['calls'][0]['owners'][224][0]-1)),
      ('omitted_owner_role',tpl,lambda d:d['hosting']['pooled_slots'].pop()),
      ('wrong_plan_binding',tpl,lambda d:d['async_schedule'].__setitem__('source_plan_sha256','0'*64)),
      ('false_total_primitive_bill',inv,lambda d:d.__setitem__('selected_real_component_primitives',d['selected_real_component_primitives']-1)),
      ('unbilled_selected_primitive',inv,lambda d:d['selected_calls'][0].__setitem__('real_component_primitives',d['selected_calls'][0]['real_component_primitives']-1)),
      ('understated_helper_width',inv,lambda d:d['providers']['gauge44']['widths'].__setitem__(0,8)),
      ('understated_positive_prefix',inv,lambda d:d['providers']['gauge44']['local']['backward'].__setitem__('prefix_l1','1')),
      ('exhausted_precision_reserve',inv,lambda d:d.__setitem__('global_prefix_bits',512)),
      ('dropped_retained_overcharge',inv,lambda d:d['retained_prior_overcharge'].__setitem__('previous_pervertex_allowance',d['retained_prior_overcharge']['previous_pervertex_allowance']-1)),
      ('nonpositive_outer_margin',asm,lambda d:d['outer'].__setitem__(next(iter(d['outer'])),'0')),
      ('changed_claimed_exponent',asm,lambda d:d.__setitem__('kappa','1/2')),
      ('changed_hosted_scalar',program,lambda d:next(e for e in d['forward'] if e[0]=='scalar')[1].__setitem__(-1,7)),
    ]
    rejected=[]
    for name,relative,mutate in mutations:
        with tempfile.TemporaryDirectory(prefix='pr1042-hosted-control-',dir=a.hosted_work.resolve().parent) as temp:
            work=Path(temp)/'work'
            shutil.copytree(a.hosted_work,work,copy_function=os.link)
            path=work/relative;value=audit.read(path);mutate(value);write_replacement(path,value)
            try:audit.check(a.baseline_replay,a.candidate_local,work)
            except ValueError as error:rejected.append({'name':name,'reason':str(error)})
            else:raise ValueError('mutation accepted: '+name)
        print('REJECT',name,flush=True)
    try:audit.check(a.baseline_replay,a.baseline_replay/'slots/local',a.baseline_replay/'t16')
    except ValueError as error:
        audit.require('Strict' in str(error) or 'strict' in str(error),'baseline rejected specifically for no improvement')
        rejected.append({'name':'unchanged_baseline_claimed_as_improvement','reason':str(error)})
    else:raise ValueError('baseline incorrectly passed as improvement')
    audit.require(inventory(a.hosted_work)==before,'actual successful hosted evidence unchanged')
    r={'status':'PASS_INDEPENDENT_PR1042_ACTUAL_HOSTED_MUTATIONS','controls_rejected':rejected,
       'baseline_controls':baseline_mutations,'successful_receipt_status':original['status'],'original_evidence_unchanged':True,
       'source_sha256':{p.name:audit.sha(p) for p in [Path(__file__),Path(__file__).with_name('check_hosted.py'),Path(__file__).with_name('verify.py')]},
       'hosted_input_sha256':before}
    with a.out.open('x') as f:json.dump(r,f,sort_keys=True,indent=2);f.write('\n')
    print(r['status'])


if __name__=='__main__':main()
