"""Execute the actual PR1042 compensation panels with exact fixed-point integers.
Each register holds interleaved real/imaginary coordinates; no verifier is timed.
"""
import argparse,gzip,hashlib,json,os,random,resource,statistics,sys,time
from pathlib import Path


def read(p):
    raw=Path(p).read_bytes()
    return json.loads(gzip.decompress(raw) if str(p).endswith('.gz') else raw)


def compile_panel(panel,backward):
    ops=[]
    for tag,t,s,a,b,f in panel:
        if tag!='add' or f!=0 or not b>0 or b&(b-1) or not a or t==s:
            raise ValueError('invalid panel operation')
        if backward:t,s,a=s,t,-a
        ops.append(('clear',704,0))
        for i,bit in enumerate(bin(abs(a))[2:]):
            if i:ops.append(('double',704,0))
            if bit=='1':ops.append(('add',704,s))
        for _ in range(b.bit_length()-1):ops.append(('half',704,0))
        ops.append(('add' if a>0 else 'sub',t,704))
        ops.append(('clear',704,0))
    return ops


def execute(rows,ops,check=False):
    width=len(rows[0])
    for kind,t,s in ops:
        if kind=='clear':rows[t]=[0]*width
        elif kind=='double':rows[t]=[x+x for x in rows[t]]
        elif kind=='half':
            if check and any(x&1 for x in rows[t]):raise ValueError('inexact integer halving')
            rows[t]=[x>>1 for x in rows[t]]
        elif kind=='add':rows[t]=[x+y for x,y in zip(rows[t],rows[s])]
        elif kind=='sub':rows[t]=[x-y for x,y in zip(rows[t],rows[s])]
        else:raise ValueError(kind)
    return rows


def direct_reference(initial,panel,backward):
    """Original y+C h or h-C^T y, using one exact divide per final sum."""
    accum={}
    for tag,t,s,a,b,f in panel:
        if backward:t,s,a=s,t,-a
        row=accum.setdefault(t,[0]*len(initial[0]));coef=a*(4//b)
        accum[t]=[x+coef*y for x,y in zip(row,initial[s])]
    expected=[list(row) for row in initial]
    for t,row in accum.items():
        if any(x%4 for x in row):raise ValueError('reference grid')
        expected[t]=[x+y//4 for x,y in zip(initial[t],row)]
    expected[704]=[0]*len(initial[0])
    return expected


def digest(rows):
    h=hashlib.sha256()
    for row in rows:
        for x in row:
            raw=x.to_bytes((x.bit_length()+8)//8,'little',signed=True)
            h.update(len(raw).to_bytes(4,'little'));h.update(raw)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--candidate',required=True)
    p.add_argument('--arm',choices=['baseline','candidate'],required=True);p.add_argument('--direction',choices=['forward','backward'],required=True)
    p.add_argument('--bits',type=int,required=True);p.add_argument('--coordinates',type=int,default=512);p.add_argument('--seed',type=int,default=20261013)
    p.add_argument('--repeats',type=int,default=1);p.add_argument('--warmup',type=int,default=1);p.add_argument('--out',required=True)
    a=p.parse_args();out=Path(a.out)
    if out.exists() or not(1<=a.coordinates<=512 and 1<=a.bits<=8192 and 1<=a.repeats<=10 and 0<=a.warmup<=3):raise ValueError('invalid new benchmark output/config')
    raw_inputs={name:Path(getattr(a,name)).read_bytes() for name in ['baseline','candidate']}
    words={name:json.loads(gzip.decompress(raw)) for name,raw in raw_inputs.items()}
    expected_pins={'baseline':'4ddb29fb9bc6f27e0c0fbfcf19a2a93a3496ad900d0f6d89059d0305c9576c0c',
                   'candidate':'86d6ef3ac6965351c4cb4892b85b12812a5a17a0668a8f247974b650a9ca80be'}
    for name,word in words.items():
        identity=hashlib.sha256(json.dumps(word,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if identity!=expected_pins[name]:raise ValueError('unbound '+name+' canonical input')
    original=words['baseline'];word=words[a.arm]
    if {k:v for k,v in word.items() if k!='compensation'}!={k:v for k,v in original.items() if k!='compensation'}:raise ValueError('typed boundary changed')
    ops=compile_panel(word['compensation'],a.direction=='backward')
    rng=random.Random(a.seed);width=2*a.coordinates
    initial=[[(1 if rng.randrange(2) else -1)*((rng.getrandbits(a.bits)|(1<<(a.bits-1)))<<2) for _ in range(width)] for _ in range(705)]
    reference=direct_reference(initial,original['compensation'],a.direction=='backward')
    checked=execute([list(row) for row in initial],ops,True)
    if checked!=reference:raise ValueError('whole exact panel output mismatch')
    expected_hash=digest(reference);del checked,reference
    for _ in range(a.warmup):execute([list(row) for row in initial],ops)
    times=[];cpu=[]
    for _ in range(a.repeats):
        rows=[list(row) for row in initial]
        c=time.process_time();t=time.perf_counter();execute(rows,ops);times.append(time.perf_counter()-t);cpu.append(time.process_time()-c)
        if digest(rows)!=expected_hash:raise ValueError('timed whole output mismatch')
    r={'status':'PASS_EXACT_COMPENSATION_EXECUTION','arm':a.arm,'direction':a.direction,'input_magnitude_bits':a.bits,'fixed_point_guard_bits':2,'complex_coordinates_per_register':a.coordinates,
       'logical_registers':704,'private_coefficient_registers':1,'panel_macros':len(word['compensation']),'real_scalar_primitives_per_coordinate':2*len(ops),
       'real_scalar_primitives_per_invocation':width*len(ops),'calls_timed':a.repeats,'warmup_calls':a.warmup,'wall_seconds':times,'cpu_seconds':cpu,
       'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'input_seed':a.seed,'output_sha256':expected_hash,'python':sys.version,
       'pid':os.getpid(),'affinity':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
       'baseline_source_sha256':hashlib.sha256(raw_inputs['baseline']).hexdigest(),'candidate_source_sha256':hashlib.sha256(raw_inputs['candidate']).hexdigest(),'canonical_semantic_sha256':expected_pins,
       'scope':'Full compensation panel arithmetic only. All binary-Horner coefficient work and basis preparation/restoration are timed. Parsing, input generation, allocation of input copies and correctness checks are outside timing. This is not the full PR1042 supplier or integer multiplication runtime.'}
    if any(Path(getattr(a,name)).read_bytes()!=raw for name,raw in raw_inputs.items()):raise ValueError('input changed during execution')
    out.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(r),flush=True)

if __name__=='__main__':main()
