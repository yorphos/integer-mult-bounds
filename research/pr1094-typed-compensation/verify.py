"""Admit the exact shared R480 replacement under selected PR1094 owner packing."""
import argparse
from pathlib import Path
import sys
from bridge import HERE,ROOT,CORE,PACKAGE,read,sha,dump,require,validate,bind_provider,bind_current_baseline,prepare,bind_preparation,compare,inventory
from support import fresh_directory,run_stage


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--provider-work',type=Path,help='Completed source-bound admitted PR1042 provider result; native content is identical in PR1094')
    p.add_argument('--baseline1042',type=Path,help='Completed PR1042 baseline, used only when rebuilding the admitted provider')
    a=p.parse_args();require(not sys.flags.optimize,'Retained checkers require assertions');require(not(a.provider_work and a.baseline1042),'Choose either complete provider reuse or a baseline for fresh provider admission')
    pins=validate();own={p.relative_to(HERE).as_posix():sha(p) for p in HERE.rglob('*.py') if '__pycache__' not in p.parts};work=fresh_directory(a.work);stages=[]
    def run(name,script,*args):run_stage(work,stages,name,script,*args)
    provider=a.provider_work.resolve() if a.provider_work else work/'provider'
    if not a.provider_work:
        args=['--work',provider]
        if a.baseline1042:args+=['--baseline1042',a.baseline1042.resolve()]
        run('admitted-provider',CORE/'verify.py',*args)
    bound=bind_provider(provider);dump(work/'PROVIDER-BINDING.json',bound)
    baseline1042=Path(bound['baseline']);local=Path(bound['local']);original_local=baseline1042/'slots/local'
    run('current-original-hosting',PACKAGE/'verify.py','--main',ROOT,'--local',original_local,'--work',work/'current-baseline')
    baseline_binding=bind_current_baseline(work/'current-baseline',baseline1042);dump(work/'BASELINE-BINDING.json',baseline_binding)
    prepare(work/'current-baseline',original_local,local,work/'preparation')
    run('current-candidate-hosting',work/'preparation/package/verify_t16.py','--main',ROOT,'--local',local,'--work',work/'candidate')
    run('independent-current-hosting',HERE/'independent/check_hosted.py','--baseline1042',baseline1042,'--baseline1094',work/'current-baseline','--candidate-local',local,'--hosted-work',work/'candidate','--out',work/'INDEPENDENT-HOSTED.json')
    dump(work/'PREPARATION-BINDING.json',bind_preparation(work/'preparation',work/'current-baseline'))
    comparison=compare(work/'current-baseline/strict',work/'candidate');dump(work/'INVOICE-COMPARISON.json',comparison)
    require(bound==bind_provider(provider),'Admitted provider changed during execution');require(baseline_binding==bind_current_baseline(work/'current-baseline',baseline1042),'Current baseline changed')
    require(pins==validate() and own=={p.relative_to(HERE).as_posix():sha(p) for p in HERE.rglob('*.py') if '__pycache__' not in p.parts},'Pinned source changed during execution')
    dump(work/'RESULT.json',dict(status='PASS_PR1094_TYPED_COMPENSATION_COMPLETE_SUPPLIER',source_pins=pins,own_source_sha256=own,stages=stages,provider_work=str(provider),provider_reused=bool(a.provider_work),artifacts=inventory(work),improvement=comparison,scope='Equivalent cheaper finite supplier at the exact PR1094 packing. All inherited conditional obligations remain. Actual shared-native component runtime is separate.'))
    print('PASS_PR1094_TYPED_COMPENSATION_COMPLETE_SUPPLIER',comparison['percent_saved'],flush=True)

if __name__=='__main__':main()
