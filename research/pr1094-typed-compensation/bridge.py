"""Source-bound PR1094 hosting of the unchanged admitted R480 replacement."""
import copy
import sys
from pathlib import Path
from fractions import Fraction as Q
from decimal import Decimal,localcontext

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CORE=ROOT/'research/pr1042-typed-compensation'
PACKAGE=ROOT/'research/complex-t16-rare-pattern-exchanges'
sys.path.insert(0,str(CORE))
from support import read,sha,dump,require,load_source,validate_sources,environment
from bindings import bind_baseline
from rebind_plan import refreshed
from prepare_hosted import provider


def inventory(root):
    root=Path(root)
    return {p.relative_to(root).as_posix():sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def validate():
    require(not sys.flags.optimize,'Retained checkers require assertions')
    pins=read(HERE/'SOURCES.json')
    for rel,digest in pins['source_sha256'].items():
        path=(ROOT/rel).resolve();require(path.is_relative_to(ROOT) and sha(path)==digest,'Pinned source: '+rel)
    core=validate_sources()
    manifest=read(PACKAGE/'MANIFEST.json')
    actual=inventory(PACKAGE);actual.pop('MANIFEST.json')
    require(actual==manifest,'Complete current public package manifest')
    return dict(extension_sources=pins,core_sources=core)


def bind_provider(work):
    work=Path(work).resolve();r=read(work/'RESULT.json')
    require(r['status']=='PASS_CURRENT_PR1042_TYPED_COMPENSATION_COMPLETE_SUPPLIER','Completed admitted provider')
    require(r['source_pins']==validate_sources(),'Exact admitted core dependency pins')
    require(set(r['artifacts'])==set(inventory(work))-{'RESULT.json'},'Complete admitted provider artifact inventory')
    require(r['own_source_sha256']=={p.relative_to(CORE).as_posix():sha(p) for p in CORE.rglob('*.py') if '__pycache__' not in p.parts},'Exact admitted core source')
    expected_stages=['alternative-native','independent-native','prepare-hosted','strict-hosted','independent-hosted']
    require([s['name'] for s in r['stages']] in [expected_stages,['selected-baseline']+expected_stages],'Complete provider stages')
    for stage in r['stages']:
        require(stage['exit_code']==0 and sha(work/(stage['name']+'.log'))==stage['log_sha256'],'Admitted provider stage log')
        script=(ROOT/stage['source']).resolve();require(script.is_relative_to(ROOT) or script.is_relative_to(work),'Admitted stage source containment')
        require(sha(script)==stage['source_sha256'],'Admitted provider stage source')
    for rel,digest in r['artifacts'].items():
        path=(work/rel).resolve();require(path.is_relative_to(work) and sha(path)==digest,'Admitted provider artifact: '+rel)
    baseline=Path(r['baseline']).resolve();bound=bind_baseline(baseline)
    require(bound==read(work/'BASELINE-BINDING.json'),'Exact provider ancestry')
    expected=read(PACKAGE/'data/SPEC.json')['providers']
    require(expected==read(ROOT/'research/gauge44-slots-t16/data/SPEC.json')['providers'],'Complete current provider contract identical to PR1042')
    return dict(status='PASS_REUSED_EXACT_ADMITTED_R480_PROVIDER',result_sha256=sha(work/'RESULT.json'),baseline_result_sha256=bound['result_sha256'],local=str(work/'alternative/local'),baseline=str(baseline))


def bind_current_source(root):
    root=Path(root);source=read(PACKAGE/'SOURCE.json')
    expected=dict(source['files']);expected['MANIFEST.json']=source['manifest_sha256']
    for name in ('OWNERS.json.gz','PLAN.json','SPEC.json'):expected['data/'+name]=sha(PACKAGE/'data'/name)
    require(inventory(root)==expected,'Exact original PR1094 source with only its three owner-data overlays')
    return expected


def bind_current_baseline(work,baseline1042):
    work=Path(work);strict=work/'strict';source=bind_current_source(work/'source')
    stages=read(strict/'STAGES.json')
    names=['restore-parent','bind8','lift16','bind','emit','audit','invoice','assembly','admission-controls','bit-supplier-controls','independent-t16']
    require([s['name'] for s in stages]==names,'Complete current original strict stages')
    for s in stages:require(s['exit_code']==0 and sha(strict/(s['name']+'.log'))==s['log_sha256'],'Current strict stage binding')
    r=read(strict/'REPLAY.json');asm=read(strict/'ASSEMBLY.json');spec=read(PACKAGE/'data/SPEC.json')
    require(r['status']=='PASS_GAUGE44_T16_STRICT_GLOBAL_REPLAY' and r['stages']==stages,'Original current strict success and stage binding')
    require(r['spec_sha256']==sha(work/'source/data/SPEC.json'),'Current original SPEC binding')
    require(asm['kappa']==r['kappa']==spec['expected']['kappa'],'Exact current selected exponent')
    require(asm['complex_profile']==read(PACKAGE/'PROFILE.json'),'Exact current selected profile')
    require(r['controls']==dict(admission=69,bit_supplier=12,independent_t16=6,controller_mutations=15),'All original controls')
    require(r['roles']==69120 and r['complete_invocations']==144 and r['prefix_bits']==397 and r['charged_prefix_bits']==512,'Current whole-owner inventory')
    require(asm['bit_supplier']==read(Path(baseline1042)/'t16/ASSEMBLY.json')['bit_supplier'],'Retained complete bit supplier')
    require(len(asm['outer'])==47 and all(Q(v)>0 for v in asm['outer'].values()),'Current original outer inequalities')
    return dict(status='PASS_CURRENT_PR1094_ORIGINAL_HOSTING',source_files=source,replay_sha256=sha(strict/'REPLAY.json'),assembly_sha256=sha(strict/'ASSEMBLY.json'),stages=stages)


def prepare(current_baseline,baseline_local,candidate_local,out):
    current_baseline=Path(current_baseline);source=current_baseline/'source';bind_current_source(source)
    module=load_source(CORE/'prepare_hosted.py','pr1094_pinned_provider_preparation')
    # Only this input directory is parameterized. The pinned implementation,
    # allowlists, recounter and original executable source are unchanged.
    module.PKG=source
    result=module.prepare(Path(baseline_local).resolve(),Path(candidate_local).resolve(),out)
    bind_current_source(source)
    return result


def bind_preparation(work,current_baseline):
    work=Path(work);source=Path(current_baseline)/'source';expected=bind_current_source(source)
    r=read(work/'REBIND.json')
    require(r['status']=='PASS_PR1042_PROVIDER_ONLY_DATA_REBIND','Pinned core preparation completed')
    require(r['source_files']==expected,'Current source inventory bound')
    require(set(r['changed_files'])=={'data/PLAN.json','data/T8/PLAN.json','data/SPEC.json','data/SPEC-T8.json'},'Exact four provider-data files')
    got=inventory(work/'package');require(set(got)==set(expected),'Complete prepared filename inventory')
    for rel,digest in expected.items():require(got[rel]==(r['changed_files'][rel]['after'] if rel in r['changed_files'] else digest),'Unchanged current source/data: '+rel)
    before,after=read(work/'before.json'),read(work/'after.json')
    require(sha(work/'before.json')==r['original_recount_sha256'] and sha(work/'after.json')==r['candidate_recount_sha256'],'Literal recount bindings')
    baseline,candidate=Path(r['baseline_local']),Path(r['candidate_local'])
    for rel in ['data/T8/PLAN.json','data/PLAN.json']:
        rebuilt=refreshed(read(source/rel),baseline,candidate)
        if rel=='data/PLAN.json':rebuilt['source_plan_sha256']=sha(work/'package/data/T8/PLAN.json')
        require(rebuilt==read(work/'package'/rel),'Recomputed exact current PLAN')
    for rel,plan in [('data/SPEC-T8.json','data/T8/PLAN.json'),('data/SPEC.json','data/PLAN.json')]:
        rebuilt=copy.deepcopy(read(source/rel));rebuilt['data']['plan_sha256']=sha(work/'package'/plan)
        rebuilt['providers']['gauge44']=provider(rebuilt['providers']['gauge44'],before,after)
        require(rebuilt==read(work/'package'/rel),'Recomputed exact current SPEC')
    return dict(status='PASS_PR1094_UNCHANGED_CHECKER_PROVIDER_ONLY_REBIND',changed_files=r['changed_files'],source_files=expected,rebind_sha256=sha(work/'REBIND.json'))


def compare(baseline,candidate):
    a=read(Path(baseline)/'global/audit/PREFIX-AND-INVOICE.json');b=read(Path(candidate)/'global/audit/PREFIX-AND-INVOICE.json')
    fields=['selected_local_paid_profile','provider_counts','complete_invocation_sweeps','bridge_sweeps','charged_prefix_bits','row_prefix_extra','helpers','centres','live','physical','physical_stock_identity','wrapper_elementary_factors_charged','factors_per_wrapper','compiler']
    for k in fields:require(a[k]==b[k],'Unchanged complete invoice term: '+k)
    for k in ('previous_pervertex_allowance','sha256','policy'):require(a['retained_prior_overcharge'][k]==b['retained_prior_overcharge'][k],'Entire prior allowance retained')
    delta=read(CORE/'COMPILE-RECEIPT.json')['invoice_delta']
    for k in ['conservative_pervertex_used','hosted_rebased_pervertex','unhosted_pervertex']:require(a[k]-b[k]==delta['global_pervertex_delta']>0,'Complete current invoice improvement: '+k)
    require(a['local_primitive_bound']-b['local_primitive_bound']==delta['local_primitive_bound_delta'],'Local paid compiler delta')
    require(a['selected_real_component_primitives']-b['selected_real_component_primitives']==delta['selected_real_primitive_delta'],'Current complete dispatch scalar delta')
    require(b['global_prefix_bits']==399<b['charged_prefix_bits']==512,'Current charged precision reserve')
    require(set(a['strict_checks'])==set(b['strict_checks']) and len(b['strict_checks'])==9 and all(b['strict_checks'].values()),'All strict finite invoice checks')
    aa=read(Path(baseline)/'ASSEMBLY.json');bb=read(Path(candidate)/'ASSEMBLY.json')
    for k in ('kappa','complex_profile','bit_supplier'):require(aa[k]==bb[k],'Current retained assembly: '+k)
    require(len(bb['outer'])==47 and all(Q(v)>0 for v in bb['outer'].values()),'All current outer inequalities')
    saved=a['conservative_pervertex_used']-b['conservative_pervertex_used'];fraction=Q(saved,a['conservative_pervertex_used'])
    with localcontext() as ctx:ctx.prec=40;percent=str(Decimal(100)*fraction.numerator/fraction.denominator)
    return dict(status='PASS_CHEAPER_CURRENT_PR1094_COMPLETE_INVOICE',before=a['conservative_pervertex_used'],after=b['conservative_pervertex_used'],saved=saved,fraction_saved=str(fraction),percent_saved=percent,kappa=bb['kappa'],prefix_before=a['global_prefix_bits'],prefix_after=b['global_prefix_bits'],charged_prefix_bits=512,baseline_invoice_sha256=sha(Path(baseline)/'global/audit/PREFIX-AND-INVOICE.json'),candidate_invoice_sha256=sha(Path(candidate)/'global/audit/PREFIX-AND-INVOICE.json'))
