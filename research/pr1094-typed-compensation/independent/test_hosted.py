#!/usr/bin/env python3
"""Actual-file controls for the current PR1094 compensation integration.
Prepared with substantial OpenAI assistance. Apache-2.0.
"""
import argparse,gzip,hashlib,importlib.util,json,os,shutil,tempfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('current_hosted_audit',Path(__file__).with_name('check_hosted.py'))
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
core=audit.load_legacy()

def inventory(root):return {p.relative_to(root).as_posix():audit.sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

def replace(path,value):
    raw=(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
    if path.suffix=='.gz':raw=gzip.compress(raw,mtime=0)
    temporary=path.with_name(path.name+'.mutant-new')
    with temporary.open('xb') as f:f.write(raw)
    os.replace(temporary,path)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline1042','baseline1094','candidate-local','hosted-work','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();audit.require(not a.out.exists(),'fresh current mutation receipt')
    baseline_before=inventory(a.baseline1094);candidate_before=inventory(a.hosted_work)
    original=audit.check(a.baseline1042,a.baseline1094,a.candidate_local,a.hosted_work)
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
        with tempfile.TemporaryDirectory(prefix='pr1094-candidate-control-',dir=a.hosted_work.resolve().parent) as temp:
            work=Path(temp)/'work';shutil.copytree(a.hosted_work,work,copy_function=os.link)
            value=core.read(work/relative);mutate(value);replace(work/relative,value)
            try:audit.check(a.baseline1042,a.baseline1094,a.candidate_local,work)
            except ValueError as e:rejected.append({'name':name,'reason':str(e)})
            else:raise ValueError('actual current candidate mutation accepted: '+name)
        print('REJECT',name,flush=True)
    try:audit.check(a.baseline1042,a.baseline1094,a.baseline1042/'slots/local',a.baseline1094/'strict')
    except ValueError as e:
        audit.require('strict' in str(e).lower(),'no-improvement control rejects on exact price')
        rejected.append({'name':'unchanged_current_baseline_claimed_as_improvement','reason':str(e)})
    else:raise ValueError('unchanged current baseline admitted as improvement')
    baseline_mutations=[
      ('changed_selected_owner_data','source/data/OWNERS.json.gz',lambda d:d[0].__setitem__('family',d[0]['family']-1)),
      ('changed_selected_specification','source/data/SPEC.json',lambda d:d['expected'].__setitem__('kappa','1/2')),
      ('changed_actual_baseline_owner','strict/'+tpl,lambda d:d['hosting']['pooled_slots'][0].__setitem__('family',d['hosting']['pooled_slots'][0]['family']-1)),
      ('changed_actual_baseline_profile','strict/'+asm,lambda d:d['complex_profile'].__setitem__(next(iter(d['complex_profile'])),0)),
    ]
    for name,relative,mutate in baseline_mutations:
        with tempfile.TemporaryDirectory(prefix='pr1094-baseline-control-',dir=a.baseline1094.resolve().parent) as temp:
            work=Path(temp)/'work';shutil.copytree(a.baseline1094,work,copy_function=os.link)
            value=core.read(work/relative);mutate(value);replace(work/relative,value)
            try:audit.bind_baseline(a.baseline1042,work,audit.load_legacy())
            except ValueError as e:rejected.append({'name':name,'reason':str(e)})
            else:raise ValueError('current baseline mutation accepted: '+name)
        print('REJECT',name,flush=True)
    audit.require(inventory(a.baseline1094)==baseline_before and inventory(a.hosted_work)==candidate_before,'both actual successful current fixtures unchanged')
    result={'status':'PASS_INDEPENDENT_PR1094_ACTUAL_HOSTED_MUTATIONS','successful_receipt_status':original['status'],'controls_rejected':rejected,'actual_baseline_and_candidate_unchanged':True,'baseline_input_sha256':baseline_before,'candidate_input_sha256':candidate_before,'source_sha256':{p.name:audit.sha(p) for p in (Path(__file__),Path(__file__).with_name('check_hosted.py'))},'unchanged_accounting_source_sha256':audit.LEGACY_SHA}
    with a.out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(result['status'])

if __name__=='__main__':main()
