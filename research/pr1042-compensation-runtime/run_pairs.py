"""Alternating fresh-process measurements of exact full compensation panels."""
from pathlib import Path
import argparse,hashlib,json,statistics,subprocess,sys,time


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--candidate',required=True);p.add_argument('--out',required=True);p.add_argument('--pairs',type=int,default=5);p.add_argument('--bits',type=int,nargs='+',default=[128,1024,4096]);a=p.parse_args()
    out=Path(a.out).resolve()
    if out.exists() or not 3<=a.pairs<=15:raise ValueError('fresh output and at least three pairs required')
    out.mkdir();script=Path(__file__).with_name('benchmark.py');source=script.read_bytes();cases=[];started=time.monotonic()
    for bits in a.bits:
      for direction in ['forward','backward']:
        pairs=[]
        for pair in range(a.pairs):
          arms=['baseline','candidate'] if pair%2==0 else ['candidate','baseline'];receipts={}
          for arm in arms:
            name=f'b{bits}-{direction}-p{pair}-{arm}'
            cmd=[sys.executable,'-I','-B',str(script),'--baseline',str(Path(a.baseline).resolve()),'--candidate',str(Path(a.candidate).resolve()),'--arm',arm,'--direction',direction,'--bits',str(bits),'--coordinates','512','--seed',str(20261013+pair),'--warmup','1','--repeats','1','--out',str(out/(name+'.json'))]
            with (out/(name+'.log')).open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            receipts[arm]=json.loads((out/(name+'.json')).read_text())
          if receipts['baseline']['output_sha256']!=receipts['candidate']['output_sha256']:raise ValueError('pair outputs differ')
          b=receipts['baseline']['wall_seconds'][0];c=receipts['candidate']['wall_seconds'][0]
          pairs.append({'pair':pair,'order':arms,'baseline_seconds':b,'candidate_seconds':c,'speedup':b/c,'output_sha256':receipts['baseline']['output_sha256'],
                        'baseline_peak_rss_kib':receipts['baseline']['max_rss_kib'],'candidate_peak_rss_kib':receipts['candidate']['max_rss_kib']})
          print(bits,direction,pair,round(b,6),round(c,6),round(b/c,3),flush=True)
        bm=statistics.median(x['baseline_seconds'] for x in pairs);cm=statistics.median(x['candidate_seconds'] for x in pairs)
        cases.append({'bits':bits,'direction':direction,'complex_coordinates':512,'pairs':pairs,'baseline_median_seconds':bm,'candidate_median_seconds':cm,'ratio_of_medians':bm/cm,
                      'paired_speedup_median':statistics.median(x['speedup'] for x in pairs),'paired_speedup_range':[min(x['speedup'] for x in pairs),max(x['speedup'] for x in pairs)]})
        (out/'PARTIAL.json').write_text(json.dumps(cases,indent=2)+'\n')
    if script.read_bytes()!=source:raise ValueError('benchmark source changed')
    r={'status':'PASS_FRESH_PROCESS_COMPENSATION_RUNTIME_PAIRS','cases':cases,'pairs_per_case':a.pairs,'processes':len(cases)*a.pairs*2,'calls_timed':len(cases)*a.pairs*2,'warmups':len(cases)*a.pairs*2,
       'benchmark_source_sha256':hashlib.sha256(source).hexdigest(),'total_experiment_seconds':time.monotonic()-started,'scope':'Exact execution of full compensation panels on 512-coordinate complex blocks. Not full supplier or multiplication runtime.'}
    (out/'RESULT.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'],flush=True)

if __name__=='__main__':main()
