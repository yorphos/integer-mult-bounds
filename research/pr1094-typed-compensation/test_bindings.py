"""Actual-file rejection tests for current composition and provider reuse."""
import argparse,copy,json,subprocess,sys,tempfile
from pathlib import Path
from bridge import HERE,read,sha,dump,require,bind_provider,bind_current_baseline,bind_preparation


def main():
    p=argparse.ArgumentParser();p.add_argument('--provider-work',type=Path,required=True);p.add_argument('--baseline1094',type=Path,required=True);p.add_argument('--preparation',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();require(not a.out.exists(),'New test receipt')
    provider=a.provider_work.resolve();base=a.baseline1094.resolve();prep=a.preparation.resolve()
    positive_provider=bind_provider(provider);baseline1042=Path(positive_provider['baseline']);positive_base=bind_current_baseline(base,baseline1042);positive_prep=bind_preparation(prep,base)
    rejected={};original={}
    def save(path):
        if path not in original:original[path]=path.read_bytes() if path.exists() else None
    def restore():
        for path,data in original.items():
            if data is None:
                if path.exists():path.unlink()
            else:path.write_bytes(data)
    def check(name,mutate,test):
        try:
            mutate()
            try:test()
            except (ValueError,AssertionError) as exc:rejected[name]=str(exc)
            else:raise RuntimeError('Accepted '+name)
        finally:restore()
    def change(path,fn):
        save(path);value=read(path);fn(value);dump(path,value)
    result=provider/'RESULT.json'
    for name,fn in [('missing_provider_artifact',lambda r:r['artifacts'].pop(next(iter(r['artifacts'])))),('failed_provider_stage',lambda r:r['stages'][0].update(exit_code=1)),('unbound_provider_source',lambda r:r['stages'][0].update(source_sha256='0'*64)),('missing_provider_dependency',lambda r:r.update(source_pins={})),('extra_provider_stage',lambda r:r['stages'].insert(0,copy.deepcopy(r['stages'][0])))]:
        check(name,lambda fn=fn:change(result,fn),lambda:bind_provider(provider))
    replay=base/'strict/REPLAY.json'
    check('wrong_current_kappa',lambda:change(replay,lambda r:r.update(kappa='1/2')),lambda:bind_current_baseline(base,baseline1042))
    check('wrong_current_spec_binding',lambda:change(replay,lambda r:r.update(spec_sha256='0'*64)),lambda:bind_current_baseline(base,baseline1042))
    rebind=prep/'REBIND.json';save(rebind)
    def prepared(relative,fn):
        path=prep/'package'/relative;change(path,fn);r=read(rebind);r['changed_files'][relative]['after']=sha(path);dump(rebind,r)
    check('geometry_with_updated_hash',lambda:prepared('data/PLAN.json',lambda r:r.update(live=r['live']+1)),lambda:bind_preparation(prep,base))
    check('price_with_updated_hash',lambda:prepared('data/SPEC.json',lambda r:r['providers']['gauge44']['complete_contract'].update(local_primitive_bound=1)),lambda:bind_preparation(prep,base))
    extra=prep/'package/code/unlisted_module.py';save(extra)
    check('extra_importable_file',lambda:extra.write_text('VALUE=1\n'),lambda:bind_preparation(prep,base))
    require(positive_provider==bind_provider(provider) and positive_base==bind_current_baseline(base,baseline1042) and positive_prep==bind_preparation(prep,base),'All positive fixtures restored')
    require(all((p.read_bytes() if p.exists() else None)==v for p,v in original.items()),'All actual bytes restored')
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/'unused';r=subprocess.run([sys.executable,'-O','-B',str(HERE/'verify.py'),'--work',str(target)],capture_output=True,text=True)
        require(r.returncode!=0 and 'Retained checkers require assertions' in r.stderr and not target.exists(),'Optimized entry rejected before output')
    dump(a.out,dict(status='PASS_PR1094_BINDING_MUTATIONS',controls_rejected=rejected,optimized_driver_rejected=True,positive_before_after=True,fixtures_preserved=True))
    print('PASS_PR1094_BINDING_MUTATIONS',len(rejected))

if __name__=='__main__':main()
