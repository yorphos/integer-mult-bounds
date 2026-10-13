"""Actual-file negative controls for complete baseline and strict-data binding."""
import argparse,copy,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
from support import HERE,read,sha,dump,require
from bindings import bind_baseline,bind_preparation


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline1042',type=Path,required=True);p.add_argument('--preparation',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    require(not a.out.exists(),'New controls output required')
    baseline,prep=a.baseline1042.resolve(),a.preparation.resolve()
    positive_base=bind_baseline(baseline);positive_prep=bind_preparation(prep);rejected={}
    originals={}
    def remember(path):
        if path not in originals:originals[path]=path.read_bytes() if path.exists() else None
    def restore():
        for path,raw in originals.items():
            if raw is None:
                if path.exists():path.unlink()
            else:path.write_bytes(raw)
    def check(name,mutation,verify):
        try:
            mutation()
            try:verify()
            except (ValueError,AssertionError) as exc:rejected[name]=str(exc)
            else:raise RuntimeError('Accepted corruption: '+name)
        finally:restore()
    result=baseline/'RESULT.json';remember(result)
    def baseline_change(fn):
        v=read(result);fn(v);dump(result,v)
    check('baseline_missing_artifact',lambda:baseline_change(lambda r:r['artifacts'].pop(next(iter(r['artifacts'])))),lambda:bind_baseline(baseline))
    check('baseline_failed_stage',lambda:baseline_change(lambda r:r['stages'][0].update(exit_code=1)),lambda:bind_baseline(baseline))
    check('baseline_wrong_stage_source',lambda:baseline_change(lambda r:r['stages'][0].update(script_sha256='0'*64)),lambda:bind_baseline(baseline))
    check('baseline_wrong_ancestry_mode',lambda:baseline_change(lambda r:r.update(reused_completed_baseline=not r['reused_completed_baseline'])),lambda:bind_baseline(baseline))
    rebind=prep/'REBIND.json';remember(rebind)
    def prepared_json(relative,fn):
        path=prep/'package'/relative;remember(path);v=read(path);fn(v);dump(path,v)
        receipt=read(rebind);receipt['changed_files'][relative]['after']=sha(path);dump(rebind,receipt)
    check('plan_geometry_with_updated_digest',lambda:prepared_json('data/PLAN.json',lambda r:r.update(live=r['live']+1)),lambda:bind_preparation(prep))
    check('plan_call_binding_with_updated_digest',lambda:prepared_json('data/PLAN.json',lambda r:r['provider_calls'][0].update(local_program_sha256='0'*64)),lambda:bind_preparation(prep))
    check('spec_profile_with_updated_digest',lambda:prepared_json('data/SPEC.json',lambda r:r['expected'].update(rank_mass=r['expected']['rank_mass']+1)),lambda:bind_preparation(prep))
    check('spec_primitive_undercount_with_updated_digest',lambda:prepared_json('data/SPEC.json',lambda r:r['providers']['gauge44']['complete_contract'].update(local_primitive_bound=1)),lambda:bind_preparation(prep))
    check('spec_prefix_undercharge_with_updated_digest',lambda:prepared_json('data/SPEC.json',lambda r:r['providers']['gauge44']['complete_contract']['local']['backward'].update(prefix_bits=1)),lambda:bind_preparation(prep))
    path=prep/'package/code/invoice_allcold.py';remember(path)
    check('changed_original_invoice_code',lambda:path.write_bytes(path.read_bytes()+b'\n# mutation\n'),lambda:bind_preparation(prep))
    extra=prep/'package/code/unlisted_module.py';remember(extra)
    check('extra_unbound_importable_file',lambda:extra.write_text('VALUE=1\n'),lambda:bind_preparation(prep))
    require(positive_base==bind_baseline(baseline),'Positive baseline restored')
    require(positive_prep==bind_preparation(prep),'Positive prepared package restored')
    for path,raw in originals.items():require((path.read_bytes() if path.exists() else None)==raw,'Actual fixture not restored')
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/'must-not-exist';r=subprocess.run([sys.executable,'-O','-B',str(HERE/'verify.py'),'--work',str(target)],capture_output=True,text=True)
        require(r.returncode!=0 and 'Retained checkers require assertions' in r.stderr and not target.exists(),'Optimized driver must fail before output creation')
    dump(a.out,dict(status='PASS_PR1042_ACTUAL_FILE_BINDING_CONTROLS',rejected_controls=rejected,optimized_driver_rejected=True,positive_before_after=True,fixtures_preserved=True))
    print('PASS_PR1042_ACTUAL_FILE_BINDING_CONTROLS',len(rejected))

if __name__=='__main__':main()
