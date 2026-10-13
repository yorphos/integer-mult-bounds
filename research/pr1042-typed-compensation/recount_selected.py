"""Execute the current selected supplier's original literal native recounter."""
import argparse
import os
import sys
from pathlib import Path
from support import ROOT, read, sha, dump


def main():
    p=argparse.ArgumentParser();p.add_argument('--local',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('new recount output required')
    pkg=ROOT/'research/gauge44-slots-t16'
    os.environ['WITNESS_SPEC']=str(pkg/'data/SPEC.json')
    os.environ.pop('WITNESS_DISCOVER',None)
    sys.path.insert(0,str(pkg/'code'))
    from invoice_allcold import recount_provider
    local=a.local.resolve();w=read(local/'CANONICAL-WORD.json.gz');programs=read(local/'LOCAL-PROGRAMS.json.gz');checks=read(local/'LOCAL-CHECKS.json')
    registry=dict(canonical_word_sha256=sha(local/'CANONICAL-WORD.json.gz'),local_programs_sha256=sha(local/'LOCAL-PROGRAMS.json.gz'),local_programs=programs,local_program_checks=checks,
      exact_local_clifford_recipe_sha256=sha(local/'CLIFFORD-RECIPES.json'),residual_adapter_sha256=sha(local/'RESIDUAL-ADAPTERS.json'),v=w['v'],R=w['R'],h=w['h'],ports=w['ports'],centers=w['centers'],
      widths=[len(w['frames'][w['final'][r]])-len(w['frames'][w['start'][r]]) for r in range(2*w['v'],2*w['v']+w['R'])])
    dump(a.out,recount_provider(local,registry))

if __name__=='__main__':main()
