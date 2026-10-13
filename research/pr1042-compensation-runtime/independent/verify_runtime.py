#!/usr/bin/env python3
"""Independent audit of the frozen PR1042 arithmetic benchmark, never timed.
Prepared with substantial OpenAI assistance. Imports no candidate constructor.
"""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from fractions import Fraction as Q
from pathlib import Path


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def add(dst, src, q):
    row = dict(dst)
    for j, x in src.items():
        row[j] = row.get(j, Q(0)) + q*x
        if not row[j]:
            del row[j]
    return row


def expected_map(base, backward):
    rows = [{j: Q(1)} for j in range(705)]
    for tag, t, s, a, b, f in base['compensation']:
        require(tag == 'add' and f == 0 and 112 <= t < 224 and 224 <= s < 704,
                'independent flat-C oracle domains')
        if backward:
            t, s, a = s, t, -a
        rows[t] = add(rows[t], {s: Q(1)}, Q(a, b))
    rows[704] = {}
    return rows


def normalize_primitive(primitive):
    def reg(v):
        return 704 if v[0] == 'W' else v[1]
    tag, t = primitive[:2]
    if tag == 'clear':
        return ('clear', reg(t), 0)
    if tag == 'scale':
        require(primitive[2] in (Q(2), Q(1, 2)), 'scale primitive')
        return ('double' if primitive[2] == 2 else 'half', reg(t), 0)
    require(tag == 'add' and primitive[3] in (Q(1), Q(-1)), 'add primitive')
    return ('add' if primitive[3] == 1 else 'sub', reg(t), reg(primitive[2]))


def inspect_stream(ops, expected):
    rows = [{j: Q(1)} for j in range(705)]
    peak = Q(1)
    depth = 0
    witness = None
    for index, (kind, t, s) in enumerate(ops):
        if kind == 'clear':
            rows[t] = {}
        elif kind in ('double', 'half'):
            q = Q(2) if kind == 'double' else Q(1, 2)
            rows[t] = {j: x*q for j, x in rows[t].items()}
        else:
            rows[t] = add(rows[t], rows[s], Q(1 if kind == 'add' else -1))
        peak = max(peak, sum((abs(x) for x in rows[t].values()), Q(0)))
        for column, x in rows[t].items():
            d = x.denominator.bit_length()-1
            require(x.denominator == 1 << d, 'dyadic dependency')
            if d > depth:
                depth = d
                witness = {'primitive_index': index, 'input_column': column,
                           'register': t, 'coefficient': str(x)}
    require(rows == expected, 'all 705 arbitrary columns equal direct panel map')
    require(not rows[704], 'dirty private work input erased')
    return {'all_arbitrary_columns': 705, 'single_real_primitives': len(ops),
            'exact_prefix_l1': str(peak), 'minimal_common_guard_bits': depth,
            'guard_one_failure_witness': witness,
            'stored_width_extra_over_payload_upper': 2+max(0,(peak.numerator-1).bit_length()-(peak.denominator.bit_length()-1)),
            'coefficient_work_erased': True}


def check_campaign_inventory(result):
    require(result['status']=='PASS_FRESH_PROCESS_COMPENSATION_RUNTIME_PAIRS','complete runtime campaign')
    require(result['pairs_per_case']==5 and result['processes']==result['calls_timed']==result['warmups']==60,
            'exact 60-process campaign inventory')
    require(len(result['cases'])==6,'six complete cases')
    expected={(b,d) for b in (128,1024,4096) for d in ('forward','backward')}
    actual=[(c['bits'],c['direction']) for c in result['cases']]
    require(len(set(actual))==6 and set(actual)==expected,'unique complete case inventory')
    names=set()
    for case in result['cases']:
        numbers=[p['pair'] for p in case['pairs']]
        require(all(type(n) is int for n in numbers) and sorted(numbers)==list(range(5)),
                'exact distinct pair inventory 0..4')
        require(case['complex_coordinates']==512,'full block case')
        for pair in numbers:
            for arm in ('baseline','candidate'):
                names.add(f"b{case['bits']}-{case['direction']}-p{pair}-{arm}.json")
    require(len(names)==60,'60 distinct sample filenames')
    return names


def bind_process_id(seen,pid):
    require(type(pid) is int and pid>0 and pid not in seen,'distinct fresh positive process ID')
    seen.add(pid)


def receipt_inventory_controls(result):
    tests=[('duplicate_pair',lambda r:r['cases'][0]['pairs'].__setitem__(1,copy.deepcopy(r['cases'][0]['pairs'][0]))),
           ('omitted_pair',lambda r:r['cases'][0]['pairs'].pop()),
           ('duplicate_case',lambda r:r['cases'].__setitem__(1,copy.deepcopy(r['cases'][0]))),
           ('omitted_case',lambda r:r['cases'].pop())]
    rejected=[]
    for name,mutate in tests:
        value=copy.deepcopy(result);mutate(value)
        try:check_campaign_inventory(value)
        except ValueError:rejected.append(name)
        else:raise ValueError('receipt inventory mutation accepted: '+name)
    seen=set();bind_process_id(seen,1)
    try:bind_process_id(seen,1)
    except ValueError:rejected.append('reused_process_id')
    else:raise ValueError('reused process ID admitted')
    return rejected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--results', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    a = parser.parse_args()
    require(not a.out.exists(), 'fresh output')
    runtime = a.root/'research/pr1042-compensation-runtime/benchmark.py'
    orchestrator=a.root/'research/pr1042-compensation-runtime/run_pairs.py'
    require(sha(runtime)=='ba53542f3941f2f99f7ee855c41f3ef835e6882d53daa8979c9f67f2e56180f2','frozen timed executor source')
    require(sha(orchestrator)=='152424eec3c66c8f1ed15f9d55bb4901286d3d1bc4ea2a83508c36c30572d8bf','frozen process orchestrator source')
    independent = Path(__file__).with_name('pr1042_independent.py')
    require(sha(independent) == 'ceec766f44e90c455b9eea31e3da1ed03585510458fbe0b4ac68c698725c3bd5', 'sealed independent source pin')
    bm = load('frozen_runtime_audit', runtime)
    iv = load('sealed_independent_audit', independent)
    words = {name: json.loads(gzip.decompress(path.read_bytes()))
             for name, path in [('baseline', a.baseline), ('candidate', a.candidate)]}
    pins = {'baseline': '4ddb29fb9bc6f27e0c0fbfcf19a2a93a3496ad900d0f6d89059d0305c9576c0c',
            'candidate': '86d6ef3ac6965351c4cb4892b85b12812a5a17a0668a8f247974b650a9ca80be'}
    require(all(iv.digest(word) == pins[name] for name, word in words.items()), 'sealed semantic pins')
    require({k:v for k,v in words['baseline'].items() if k != 'compensation'} ==
            {k:v for k,v in words['candidate'].items() if k != 'compensation'}, 'same typed boundary')
    checks = {}; controls = []
    for name, word in words.items():
        checks[name] = {}
        for direction in ('forward', 'backward'):
            backward = direction == 'backward'
            ops = bm.compile_panel(word['compensation'], backward)
            literal = list(map(normalize_primitive, iv.primitive_stream(
                iv.panel_event(op, direction) for op in word['compensation'])))
            require(ops == literal, 'literal unchanged PR635 Horner primitive sequence')
            rec = inspect_stream(ops, expected_map(words['baseline'], backward))
            require(rec['minimal_common_guard_bits'] == 2, 'exact minimal guard')
            rows = [[0, 0] for _ in range(705)]
            rows[rec['guard_one_failure_witness']['input_column']] = [2, -2]
            try:
                bm.execute(rows, ops, True)
            except ValueError as error:
                require(str(error) == 'inexact integer halving', 'guard control reason')
                controls.append(name+'_'+direction+'_guard_one_rejected')
            else:
                raise ValueError('guard one incorrectly sufficient')
            initial = [[4*((j*17+3)%127-63), 4*((j*31+9)%131-65)] for j in range(705)]
            direct = [[sum(x*initial[j][k] for j,x in row.items()) for k in range(2)]
                      for row in expected_map(words['baseline'], backward)]
            require(bm.execute([list(r) for r in initial], ops, True) == direct,
                    'signed exact executor equals independent symbolic endpoint')
            require(bm.direct_reference(initial, words['baseline']['compensation'], backward) == direct,
                    'benchmark oracle equals independent reference')
            mutated = ops[:-1]
            require(bm.execute([list(r) for r in initial], mutated, True) != direct,
                    'missing private work cleanup detected')
            controls.append(name+'_'+direction+'_missing_cleanup_rejected')
            checks[name][direction] = rec
    rows = [[0] for _ in range(705)]
    rows[704] = [-3]
    try:
        bm.execute(rows, [('half',704,0)], True)
    except ValueError:
        controls.append('negative_odd_halving_rejected')
    else:
        raise ValueError('negative odd halving admitted')
    with tempfile.TemporaryDirectory(prefix='pr1042-runtime-pin-control-') as temp:
        temp = Path(temp)
        for name in words:
            mutant = json.loads(json.dumps(words[name]))
            mutant['compensation'][0][3] *= -1
            path = temp/(name+'.json.gz')
            path.write_bytes(gzip.compress(json.dumps(mutant).encode(), mtime=0))
            out = temp/(name+'-should-not-exist.json')
            cmd = [sys.executable, '-I', '-B', str(runtime), '--baseline',
                   str(path if name == 'baseline' else a.baseline), '--candidate',
                   str(path if name == 'candidate' else a.candidate), '--arm', 'baseline',
                   '--direction', 'forward', '--bits', '16', '--coordinates', '1',
                   '--warmup', '0', '--repeats', '1', '--out', str(out)]
            rejected = subprocess.run(cmd, capture_output=True, text=True)
            require(rejected.returncode != 0 and 'unbound '+name+' canonical input' in rejected.stderr
                    and not out.exists(), 'actual CLI rejects mutated '+name+' before execution')
            controls.append('actual_'+name+'_canonical_mutation_rejected')
    result = json.loads((a.results/'RESULT.json').read_text())
    require(result['status'] == 'PASS_FRESH_PROCESS_COMPENSATION_RUNTIME_PAIRS', 'complete runtime campaign')
    require(result['benchmark_source_sha256'] == sha(runtime), 'timed source binding')
    require(result['pairs_per_case'] == 5 and len(result['cases']) == 6 and result['processes'] == 60,
            'full planned campaign')
    expected_samples=check_campaign_inventory(result)
    require({p.name for p in a.results.glob('b*.json')}==expected_samples,'exact actual sample file inventory')
    inventory_controls=receipt_inventory_controls(result)
    sample_hashes={};process_ids=set()
    seen = set(); summaries = []
    for case in result['cases']:
        bits, direction = case['bits'], case['direction']
        require((bits,direction) not in seen, 'unique case')
        seen.add((bits,direction))
        require(len(case['pairs']) == 5, 'all pair samples retained')
        for pair in case['pairs']:
            number = pair['pair']
            require(pair['order'] == (['baseline','candidate'] if number%2 == 0 else ['candidate','baseline']), 'AB/BA ordering')
            receipts = {}
            for name in words:
                path = a.results/f'b{bits}-{direction}-p{number}-{name}.json'
                r = json.loads(path.read_text()); receipts[name] = r
                sample_hashes[path.name]=sha(path)
                bind_process_id(process_ids,r['pid'])
                require(r['status'] == 'PASS_EXACT_COMPENSATION_EXECUTION' and r['arm'] == name and
                        r['direction'] == direction and r['input_magnitude_bits'] == bits and
                        r['complex_coordinates_per_register'] == 512 and r['fixed_point_guard_bits'] == 2 and
                        r['logical_registers'] == 704 and r['private_coefficient_registers'] == 1 and
                        r['input_seed'] == 20261013+number and r['calls_timed'] == 1 and r['warmup_calls'] == 1,
                        'sample protocol binding')
                require(r['canonical_semantic_sha256'] == pins, 'sample canonical pins')
                require(r['baseline_source_sha256'] == sha(a.baseline) and r['candidate_source_sha256'] == sha(a.candidate), 'sample input bytes')
                require(r['real_scalar_primitives_per_invocation'] == checks[name][direction]['single_real_primitives']*1024,
                        'fully executed scalar work count')
                require(len(r['wall_seconds']) == len(r['cpu_seconds']) == 1 and
                        r['wall_seconds'][0] > 0 and r['cpu_seconds'][0] > 0, 'positive individual timings')
                require(pair[name+'_seconds'] == r['wall_seconds'][0], 'raw timing preservation')
                require(type(r['max_rss_kib']) is int and r['max_rss_kib']>0 and
                        pair[name+'_peak_rss_kib']==r['max_rss_kib'],'raw process high-water memory preservation')
            require(receipts['baseline']['output_sha256'] == receipts['candidate']['output_sha256'] == pair['output_sha256'], 'same pair output')
            require(receipts['baseline']['python'] == receipts['candidate']['python'] and
                    receipts['baseline']['affinity'] == receipts['candidate']['affinity'], 'same interpreter and available CPUs')
            require(pair['speedup'] == pair['baseline_seconds']/pair['candidate_seconds'], 'paired ratio')
        import statistics
        b = statistics.median(p['baseline_seconds'] for p in case['pairs'])
        c = statistics.median(p['candidate_seconds'] for p in case['pairs'])
        require(case['baseline_median_seconds'] == b and case['candidate_median_seconds'] == c and
                case['ratio_of_medians'] == b/c and case['paired_speedup_median'] == statistics.median(p['speedup'] for p in case['pairs']), 'summary recomputation')
        require(case['paired_speedup_range']==[min(p['speedup'] for p in case['pairs']),max(p['speedup'] for p in case['pairs'])],'observed paired range')
        summaries.append({'bits':bits, 'direction':direction, 'ratio_of_medians':b/c,
                          'paired_speedup_median':case['paired_speedup_median']})
    require(seen == {(b,d) for b in [128,1024,4096] for d in ['forward','backward']}, 'planned case inventory')
    receipt = {'status':'PASS_INDEPENDENT_PR1042_ARITHMETIC_BENCHMARK_AUDIT', 'primitive_and_grid_checks':checks,
               'controls_rejected':controls, 'receipt_inventory_controls_rejected':inventory_controls,
               'sample_sha256':sample_hashes,'distinct_process_ids':sorted(process_ids),'cases':summaries,
               'timed_source_sha256':sha(runtime), 'orchestrator_sha256':sha(a.root/'research/pr1042-compensation-runtime/run_pairs.py'),
               'sealed_independent_source_sha256':sha(independent), 'campaign_result_sha256':sha(a.results/'RESULT.json'),
               'audit_source_sha256':sha(__file__), 'memory_scope':'ru_maxrss is whole-process high-water including untimed correctness/reference work; it is not isolated kernel peak memory.',
               'scope':'Exact full compensation panel arithmetic in CPython on 512-coordinate complex blocks. Input magnitude width B is distinct from stored B+2 bits and certified intermediate bounds. Does not measure full supplier or integer multiplication runtime.'}
    with a.out.open('x') as f:
        json.dump(receipt, f, indent=2, sort_keys=True); f.write('\n')
    print(receipt['status'])

if __name__ == '__main__':
    main()
