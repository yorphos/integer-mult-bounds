"""Rebuild the selected PR1042 compensation and strict whole-owner supplier."""
import argparse
from pathlib import Path
import sys
from support import HERE,ROOT,read,sha,dump,require,fresh_directory,run_stage,validate_sources
from bindings import bind_baseline,bind_preparation,compare_invoices


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',type=Path,required=True)
    g=p.add_mutually_exclusive_group();g.add_argument('--baseline1042',type=Path,help='Completed current selected replay, fully rebound before reuse');g.add_argument('--baseline799',type=Path,help='Completed retained ancestry; all current PR1042 construction stages still rebuild')
    a=p.parse_args();require(not sys.flags.optimize,'Retained checkers require assertions')
    own={x.relative_to(HERE).as_posix():sha(x) for x in HERE.rglob('*.py') if '__pycache__' not in x.parts};pins=validate_sources();work=fresh_directory(a.work);stages=[]
    def run(name,script,*args):run_stage(work,stages,name,script,*args)
    if a.baseline1042:baseline=a.baseline1042.resolve()
    else:
        baseline=work/'baseline1042';args=['--work',baseline]
        if a.baseline799:args+=['--baseline799',a.baseline799.resolve()]
        run('selected-baseline',ROOT/'scripts/verify_frontier1042.py',*args)
    dump(work/'BASELINE-BINDING.json',bind_baseline(baseline))
    run('alternative-native',HERE/'native.py','--baseline-local',baseline/'slots/local','--out',work/'alternative')
    run('independent-native',HERE/'independent/verify.py','--baseline-local',baseline/'slots/local','--candidate-local',work/'alternative/local','--out',work/'INDEPENDENT-NATIVE.json')
    run('prepare-hosted',HERE/'prepare_hosted.py','--baseline-local',baseline/'slots/local','--candidate-local',work/'alternative/local','--out',work/'preparation')
    run('strict-hosted',work/'preparation/package/verify_t16.py','--main',ROOT,'--local',work/'alternative/local','--work',work/'hosted')
    run('independent-hosted',HERE/'independent/check_hosted.py','--baseline-replay',baseline,'--candidate-local',work/'alternative/local','--hosted-work',work/'hosted','--out',work/'INDEPENDENT-HOSTED.json')
    dump(work/'PREPARATION-BINDING.json',bind_preparation(work/'preparation'))
    comparison=compare_invoices(baseline,work/'hosted');dump(work/'INVOICE-COMPARISON.json',comparison)
    require(read(work/'BASELINE-BINDING.json')==bind_baseline(baseline),'Baseline changed during execution')
    require(pins==validate_sources(),'Pinned selected source changed')
    require(own=={x.relative_to(HERE).as_posix():sha(x) for x in HERE.rglob('*.py') if '__pycache__' not in x.parts},'Integration source changed')
    artifacts={x.relative_to(work).as_posix():sha(x) for x in work.rglob('*') if x.is_file() and '__pycache__' not in x.parts}
    dump(work/'RESULT.json',dict(status='PASS_CURRENT_PR1042_TYPED_COMPENSATION_COMPLETE_SUPPLIER',baseline=str(baseline),reused_completed_baseline1042=bool(a.baseline1042),stages=stages,source_pins=pins,own_source_sha256=own,artifacts=artifacts,improvement=comparison,
      scope='Finite current selected supplier improvement, with unchanged inherited conditional interfaces. Measured component runtime is a separate experiment.'))
    print('PASS_CURRENT_PR1042_TYPED_COMPENSATION_COMPLETE_SUPPLIER',comparison['percent_saved'],flush=True)

if __name__=='__main__':main()
