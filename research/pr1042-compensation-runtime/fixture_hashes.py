"""Untimed deterministic input identities for an already completed campaign."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,random


def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('new output required')
    script=Path(__file__).with_name('benchmark.py');spec=importlib.util.spec_from_file_location('timed_benchmark',script);bm=importlib.util.module_from_spec(spec);spec.loader.exec_module(bm)
    result=json.loads((a.results/'RESULT.json').read_text());digest=hashlib.sha256(script.read_bytes()).hexdigest()
    if result['benchmark_source_sha256']!=digest:raise ValueError('frozen source changed')
    records=[]
    for bits in sorted({c['bits'] for c in result['cases']}):
      for pair in range(result['pairs_per_case']):
        seed=20261013+pair;rng=random.Random(seed)
        rows=[[(1 if rng.randrange(2) else -1)*((rng.getrandbits(bits)|(1<<(bits-1)))<<2) for _ in range(1024)] for _ in range(705)]
        identity=bm.digest(rows)
        widths={x.bit_length() for row in rows for x in row}
        if widths!={bits+2} or any(x%4 for row in rows for x in row):raise ValueError('fixed-point grid')
        names=[]
        for direction in ['forward','backward']:
          for arm in ['baseline','candidate']:
            name=f'b{bits}-{direction}-p{pair}-{arm}.json';sample=json.loads((a.results/name).read_text())
            if sample['input_seed']!=seed or sample['input_magnitude_bits']!=bits or sample['complex_coordinates_per_register']!=512:raise ValueError('sample input identity')
            names.append(name)
        records.append({'input_magnitude_bits':bits,'stored_magnitude_bits':bits+2,'seed':seed,'gaussian_coordinates_per_register':512,'registers_including_coefficient_work':705,'input_sha256':identity,'bound_samples':names})
        print(bits,pair,identity,flush=True)
    out={'status':'PASS_REGENERATED_INPUT_IDENTITIES','benchmark_source_sha256':digest,'records':records,'scope':'Input hashes regenerated from the frozen deterministic generator and exact recorded seeds/configurations. Both arms and directions receive the same initial values in each matched pair. No timing was repeated or changed.'}
    a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')

if __name__=='__main__':main()
