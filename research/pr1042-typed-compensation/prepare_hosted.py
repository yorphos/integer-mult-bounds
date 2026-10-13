"""Refresh only native identities/prices in frozen PR1042 T8/T16 data.

The selected controller, binder, invoice, assembly and independent verifier
source files are copied byte-for-byte and executed in strict mode. Source
manifests are checked before generating a separate alternative package.
"""
import argparse
import copy
from pathlib import Path
import shutil
import subprocess
import sys
from support import HERE,ROOT,read,sha,dump,require,environment,fresh_directory
from rebind_plan import refreshed

PKG=ROOT/'research/gauge44-slots-t16'
PROVIDER_KEYS={'artifact_semantic_sha256','program_hashes','artifacts','complete_contract','semantic_phase_sha256','expected_local'}
LOCAL_KEYS={'events','macros','real_component_primitives','prefix_l1','prefix_bits','coefficient_work_primitive_count'}
CONTRACT_KEYS={'local','local_adapters','local_primitive_bound','program_hashes','semantic_artifact_sha256'}


def compare_except(a,b,keys,label):
    require(set(a)==set(b),label+' key inventory')
    require({k:v for k,v in a.items() if k not in keys}=={k:v for k,v in b.items() if k not in keys},label+' unchanged fields')


def provider(old,before,after):
    before={k:v for k,v in before.items() if k!='artifacts'}
    require(old['complete_contract']==before,'Selected spec binds actual baseline literal recount')
    contract={k:v for k,v in after.items() if k!='artifacts'}
    compare_except(before,contract,CONTRACT_KEYS,'Complete provider contract')
    for o in ['forward','backward']:
        compare_except(before['local'][o],contract['local'][o],LOCAL_KEYS,'Native local contract')
        require(contract['local'][o]['macros']<before['local'][o]['macros'],'Strict macro reduction')
        require(contract['local'][o]['real_component_primitives']<before['local'][o]['real_component_primitives'],'Strict primitive reduction')
    new=copy.deepcopy(old)
    new.update(complete_contract=contract,artifact_semantic_sha256=after['semantic_artifact_sha256'],program_hashes=after['program_hashes'],
      semantic_phase_sha256=after['semantic_artifact_sha256']['CLIFFORD-REVIEW.json'],
      artifacts={k:after['artifacts'][k] for k in old['artifacts']},
      expected_local={o:{k:after['local'][o][k] for k in old['expected_local'][o]} for o in old['expected_local']})
    compare_except(old,new,PROVIDER_KEYS,'Provider expectation')
    return new


def prepare(baseline,candidate,out):
    for package in ('gauge44-leaver8','gauge44-slots','gauge44-slots-t16'):
        subprocess.run([sys.executable,'-B',str(ROOT/'research'/package/'verify_manifest.py')],check=True,env=environment())
    out=fresh_directory(out)
    source_files={p.relative_to(PKG).as_posix():sha(p) for p in PKG.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    for name,local in [('before',baseline),('after',candidate)]:
        subprocess.run([sys.executable,'-B',str(HERE/'recount_selected.py'),'--local',str(local),'--out',str(out/(name+'.json'))],check=True,env=environment())
    before,after=read(out/'before.json'),read(out/'after.json')
    pkg=out/'package';shutil.copytree(PKG,pkg,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    changed={}
    for rel in ['data/T8/PLAN.json','data/PLAN.json']:
        original=read(PKG/rel);new=refreshed(original,baseline,candidate)
        if rel=='data/PLAN.json':
            require(original['source_plan_sha256']==sha(PKG/'data/T8/PLAN.json'),'Original T16 ancestry identity')
            new['source_plan_sha256']=sha(pkg/'data/T8/PLAN.json')
        dump(pkg/rel,new);changed[rel]={'before':sha(PKG/rel),'after':sha(pkg/rel)}
    for rel,plan in [('data/SPEC-T8.json','data/T8/PLAN.json'),('data/SPEC.json','data/PLAN.json')]:
        old=read(PKG/rel);new=copy.deepcopy(old)
        require(set(old['providers'])=={'gauge44'},'Exact provider inventory')
        require(old['data']['plan_sha256']==sha(PKG/plan),'Original spec-plan binding')
        new['data']['plan_sha256']=sha(pkg/plan)
        new['providers']['gauge44']=provider(old['providers']['gauge44'],before,after)
        a,b=copy.deepcopy(old),copy.deepcopy(new)
        for v in (a,b):del v['data']['plan_sha256'];del v['providers']
        require(a==b,'All geometry/profile/precision/assembly expectations unchanged')
        dump(pkg/rel,new);changed[rel]={'before':sha(PKG/rel),'after':sha(pkg/rel)}
    require(source_files=={p.relative_to(PKG).as_posix():sha(p) for p in PKG.rglob('*') if p.is_file() and '__pycache__' not in p.parts},'Selected source changed')
    for rel,digest in source_files.items():
        if rel not in changed:require(sha(pkg/rel)==digest,'Non-data source copy changed: '+rel)
    receipt=dict(status='PASS_PR1042_PROVIDER_ONLY_DATA_REBIND',source_files=source_files,changed_files=changed,
      original_manifest_sha256=sha(PKG/'MANIFEST.json'),baseline_local=str(baseline),candidate_local=str(candidate),
      original_recount_sha256=sha(out/'before.json'),candidate_recount_sha256=sha(out/'after.json'),
      selected_code_unchanged=True,owner_maps_unchanged=True,discovery_enabled=False,
      note='Original MANIFEST remains a provenance copy; the four documented alternative data files have their own exact before/after receipt. The source package manifest passed and remains unchanged.')
    dump(out/'REBIND.json',receipt);return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-local',type=Path,required=True);p.add_argument('--candidate-local',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    prepare(a.baseline_local.resolve(),a.candidate_local.resolve(),a.out)
    print('PASS_PR1042_PROVIDER_ONLY_DATA_REBIND')

if __name__=='__main__':main()
