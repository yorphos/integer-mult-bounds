#!/usr/bin/env python3
"""Independent current PR1094 hosting of the identical typed compensation panel.
Prepared with substantial OpenAI assistance. Apache-2.0.
The pinned PR1042 accounting function is unchanged; a separate exact PR1094
baseline binding is supplied to its isolated module. Original admission sources
and all numerical/ownership predicates are unchanged.
"""
import argparse,hashlib,importlib.util,json,tempfile
from fractions import Fraction as Q
from pathlib import Path

HERE=Path(__file__).resolve().parent
LEGACY=HERE.parents[1]/'pr1042-typed-compensation/independent'
LEGACY_SHA='dab0ee1ca6cd8aee4421dc2f267659add6c43d65457cb9dc3917d37302d127c0'
SCALAR_SHA='ceec766f44e90c455b9eea31e3da1ed03585510458fbe0b4ac68c698725c3bd5'
SOURCE_MANIFEST_SHA='fe55cb2812dc863a4bcd9e6083474f7aa986d2095ef66ae210ba85b251fe86c9'
DATA_PINS={'data/OWNERS.json.gz':'87902c528dfab7d503dcf8a784260e3ab6fb7424c418a1820f7261f25be7b6bc',
           'data/PLAN.json':'7bd786ba8e66408f02aa9ef446eaf20c1bfe981ea2e4dd1e5a929f0aa7767bc0',
           'data/SPEC.json':'8cb51f25a5da4a29d3783853025b73ff1f452429d4fdb30c599e598bcab0e71d'}
KAPPA='836330098538459/500000000000000000'
STAGES=['restore-parent','bind8','lift16','bind','emit','audit','invoice','assembly','admission-controls','bit-supplier-controls','independent-t16']
NATIVE_FILES=('CANONICAL-WORD.json.gz','LOCAL-PROGRAMS.json.gz','LOCAL-CHECKS.json','INDEPENDENT-LOCAL-REPLAY.json','RESIDUAL-ADAPTERS.json','CLIFFORD-RECIPES.json','CLIFFORD-REVIEW.json')

BASELINE_ARTIFACT_NAMES_SHA='feca805117a80ea560aa9ee0f98769f542235a087dd9a2cb807131ce66fbafae'
BASELINE_STAGES={'leaver-manifest': {'script': 'research/gauge44-leaver8/verify_manifest.py',
                     'sha256': '723d726dbbe5b65a49caecae0f1aab664a1413fb639abfd3e826a5a538e14e5b'},
 'slots-manifest': {'script': 'research/gauge44-slots/verify_manifest.py',
                    'sha256': '723d726dbbe5b65a49caecae0f1aab664a1413fb639abfd3e826a5a538e14e5b'},
 't16-manifest': {'script': 'research/gauge44-slots-t16/verify_manifest.py',
                  'sha256': '723d726dbbe5b65a49caecae0f1aab664a1413fb639abfd3e826a5a538e14e5b'},
 'base': {'script': 'research/gauge44-leaver8/construction/reproduce.py',
          'sha256': '047bb9b3536b0b16bb08a21cd9fd80404ca9d022345f1aeab34b21dffc281c92'},
 'cells': {'script': 'research/gauge44-leaver8/construction/leaver/reproduce_leaver.py',
           'sha256': '831bfdf2247b5d864b74c3b2b6a475718053d48570851d48bd1c5471d410ee30'},
 'chain': {'script': 'research/gauge44-leaver8/construction/leaver/reproduce_leaver_chain.py',
           'sha256': '2bc3fc3f32e0f957a0731b79254c553ca48fc6d4d47c4f99d6cd31e1901d85b5'},
 'independent-leaver': {'script': 'research/gauge44-leaver8/independent/audit_local.py',
                        'sha256': '03afcfc9da428b3f6edac81c1fee7f277ab81b64998efae78380b63498dec6cd'},
 'leaver-global': {'script': 'research/gauge44-leaver8/verify_global.py',
                   'sha256': '16bd5e54598592e92e210f99065348c5df261b8350fdc688072ce053d15b088a'},
 'slots': {'script': 'research/gauge44-slots/construction/slots/verify_slots.py',
           'sha256': 'bc1c0e3e3d7c81dc1649f5be82cdd2399e543d46c24879cb975877bf9b7957be'},
 't16': {'script': 'research/gauge44-slots-t16/verify_t16.py',
         'sha256': '050e2dfba59911b8f29fd94422833d421367a0ad01c5e4ae916a75a235ee5e46'}}

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_legacy():
    require(sha(LEGACY/'check_hosted.py')==LEGACY_SHA and sha(LEGACY/'verify.py')==SCALAR_SHA,'unchanged independent accounting and scalar sources')
    spec=importlib.util.spec_from_file_location('isolated_pr1042_accounting',LEGACY/'check_hosted.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def bind_baseline(baseline1042,baseline1094,core):
    baseline1042,baseline1094=map(lambda p:Path(p).resolve(),(baseline1042,baseline1094))
    ancestral=core.bind_selected_baseline(baseline1042)
    result1042=core.read(baseline1042/'RESULT.json')
    require(result1042['status']=='PASS_COMPLETE_PR1042_COMPOSITION' and Q(result1042['kappa'])==Q('0.001672188119205421'),'complete PR1042 ancestry result')
    require(sha(baseline1042/'BASELINE-BINDING.json')==result1042['baseline_binding_sha256'],'complete retained ancestry binding')
    require(sha(baseline1042/'t16/ASSEMBLY.json')==result1042['selected_assembly_sha256'],'PR1042 assembly result binding')
    names=set(result1042['artifacts']);base_stages=result1042['stages']
    if base_stages[0]['name']=='baseline799-cold':
        names.discard('baseline799-cold.log');base_stages=base_stages[1:]
    require(core.content_sha(sorted(names))==BASELINE_ARTIFACT_NAMES_SHA,'exact complete PR1042 ancestry artifact inventory')
    require([s['name'] for s in base_stages]==list(BASELINE_STAGES),'exact complete PR1042 ancestry stage inventory')
    for stage in base_stages:
        expected=BASELINE_STAGES[stage['name']]
        require(stage['exit_code']==0 and stage['script']==expected['script'] and stage['script_sha256']==expected['sha256'] and sha(baseline1042/(stage['name']+'.log'))==stage['log_sha256'],'bound original PR1042 source/stage/log')
    for name,digest in result1042['artifacts'].items():
        path=(baseline1042/name).resolve()
        require(path.is_relative_to(baseline1042) and path.is_file() and sha(path)==digest,'actual retained ancestry artifact: '+name)
    source=baseline1094/'source';strict=baseline1094/'strict'
    require(sha(source/'MANIFEST.json')==SOURCE_MANIFEST_SHA,'immutable original PR1087 source inventory')
    expected=core.read(source/'MANIFEST.json');require(len(expected)==179,'179 unchanged original source files')
    expected.update(DATA_PINS);expected['MANIFEST.json']=SOURCE_MANIFEST_SHA
    actual={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    require(actual==expected,'exact original strict source plus three selected PR1094 data overlays')
    spec=core.read(source/'data/SPEC.json');original_spec=core.read(baseline1042/'t16/global/audit/PREFIX-AND-INVOICE.json')
    provider=spec['providers']['gauge44'];native=baseline1042/'slots/local'
    require(provider['artifact_semantic_sha256']['CANONICAL-WORD.json.gz']=='4ddb29fb9bc6f27e0c0fbfcf19a2a93a3496ad900d0f6d89059d0305c9576c0c' and provider['artifact_semantic_sha256']['LOCAL-PROGRAMS.json.gz']=='9f41d53659e9be84e20c661560c5687abbf5cd0660cdecbe01ad5eb29e6b8ee3','current selected native word and programs identical')
    require(provider['complete_contract']['program_hashes']==original_spec['providers']['gauge44']['program_hashes'],'complete native orientation identities unchanged')
    for name in NATIVE_FILES:
        require(core.read(strict/'global/base/providers/gauge44'/name)==core.read(native/name),'current baseline consumes exact complete native artifact: '+name)
    stages=core.read(strict/'STAGES.json');replay=core.read(strict/'REPLAY.json')
    require([s['name'] for s in stages]==STAGES and replay['stages']==stages,'all original strict PR1094 stages')
    for stage in stages:
        require(stage['exit_code']==0 and sha(strict/(stage['name']+'.log'))==stage['log_sha256'],'successful strict stage and actual log')
    require(replay['status']=='PASS_GAUGE44_T16_STRICT_GLOBAL_REPLAY' and replay['kappa']==KAPPA and replay['spec_sha256']==sha(source/'data/SPEC.json'),'current selected exact strict result and SPEC binding')
    require(replay['controls']==dict(admission=69,bit_supplier=12,independent_t16=6,controller_mutations=15),'all retained current baseline controls')
    template=core.read(strict/'global/hosted/GLOBAL-TEMPLATE.json.gz');invoice=core.read(strict/'global/audit/PREFIX-AND-INVOICE.json');assembly=core.read(strict/'ASSEMBLY.json')
    owners=core.read(source/'data/OWNERS.json.gz')
    require(template['hosting']['pooled_slots']==owners and len(owners)==69120 and template['hosting']['owner_map_sha256']==DATA_PINS['data/OWNERS.json.gz'],'literal complete selected PR1094 owner packing')
    require(assembly['complex_profile']==spec['expected']['global_profile']==replay['complex_profile'] and assembly['kappa']==KAPPA,'exact current selected paid profile and exponent')
    require(assembly['bit_supplier']==core.read(baseline1042/'t16/ASSEMBLY.json')['bit_supplier'],'complete inherited bit supplier unchanged')
    require(len(assembly['outer'])==47 and all(Q(v)>0 for v in assembly['outer'].values()),'47 strictly positive current selected outer bounds')
    require(replay['complete_invocations']==144 and replay['roles']==69120 and replay['prefix_bits']==invoice['global_prefix_bits']==397 and replay['charged_prefix_bits']==512 and replay['physical_row_coefficient']==16469,'exact current selected full inventory and precision')
    template_identity=core.content_sha(template)
    owner=core.read(strict/'global/audit/OWNERS-AND-PROFILE.json');control=core.read(strict/'global/audit/ASYNC-AUDIT.json')
    require(assembly['template_sha256']==owner['template_sha256']==control['template_sha256']==invoice['template_sha256']==template_identity,'actual current baseline template identities')
    require(invoice['owner_audit_sha256']==sha(strict/'global/audit/OWNERS-AND-PROFILE.json') and invoice['controller_audit_sha256']==sha(strict/'global/audit/ASYNC-AUDIT.json'),'actual current owner/controller identities')
    require(template['async_schedule']['source_plan_sha256']==sha(strict/'global/PLAN.json'),'actual current baseline plan identity')
    require(control['mutation_controls_run'] and len(control['mutations_rejected'])==15,'actual current controller controls')
    ac=core.read(strict/'ADMISSION-CONTROLS.json');bc=core.read(strict/'BIT-SUPPLIER-CONTROLS.json');ind=core.read(strict/'INDEPENDENT-T16.json')
    require(len(ac['rejected_controls'])==69 and not ac['discovery_accepted_controls'] and len(bc['rejected_controls'])==12 and len(ind['controls_rejected'])==6,'actual complete current admission controls')
    return {'status':'PASS_INDEPENDENT_SELECTED_PR1094_BASELINE','selected_main':'c0e3631dc24e3c24a861f7d3d79e0608481cccec','source_manifest_sha256':SOURCE_MANIFEST_SHA,'selected_data_sha256':DATA_PINS,'source_files_checked':len(expected),'baseline1042_result_sha256':sha(baseline1042/'RESULT.json'),'native_ancestry_binding':ancestral,'baseline1094_artifacts':{n:sha(strict/n) for n in ('REPLAY.json','STAGES.json','ASSEMBLY.json','global/hosted/GLOBAL-TEMPLATE.json.gz','global/audit/PREFIX-AND-INVOICE.json')},'kappa':KAPPA}


def check(baseline1042,baseline1094,candidate_local,hosted_work):
    core=load_legacy();binding=bind_baseline(baseline1042,baseline1094,core)
    # Only the input path layout is adapted. All dispatch, frame-width, scalar,
    # complete charge, prefix, precision, owner and outer predicates are reused.
    with tempfile.TemporaryDirectory(prefix='pr1094-independent-read-view-') as temp:
        view=Path(temp);(view/'slots').mkdir()
        (view/'slots/local').symlink_to(Path(baseline1042).resolve()/'slots/local',target_is_directory=True)
        (view/'t16').symlink_to(Path(baseline1094).resolve()/'strict',target_is_directory=True)
        def checked_current_baseline(path):
            require(Path(path)==view,'only the separately checked current baseline view')
            return binding
        core.bind_selected_baseline=checked_current_baseline
        result=core.check(view,candidate_local,hosted_work)
    result.pop('immutable_selected_members')
    result['status']='PASS_INDEPENDENT_COMPLETE_PR1094_HOSTED_INVOICE'
    result['unchanged_accounting_source_sha256']=LEGACY_SHA
    result['scope']='Current selected PR1094 packing with identical admitted R480 native interface and strictly cheaper complete compensation invoice. Current local arithmetic applicability follows exact word/program identities; no full multiplication-runtime or unconditional theorem claim.'
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline1042','baseline1094','candidate-local','hosted-work','out'):parser.add_argument('--'+name,type=Path,required=True)
    a=parser.parse_args();require(not a.out.exists(),'fresh independent current receipt')
    result=check(a.baseline1042,a.baseline1094,a.candidate_local,a.hosted_work)
    with a.out.open('x') as f:json.dump(result,f,sort_keys=True,indent=2);f.write('\n')
    print(result['status'])

if __name__=='__main__':main()
