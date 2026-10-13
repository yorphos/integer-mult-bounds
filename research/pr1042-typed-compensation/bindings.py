"""Bind the completed selected baseline, strict alternative and exact savings."""
import copy
from decimal import Decimal,localcontext
from fractions import Fraction as Q
from pathlib import Path
from support import ROOT,HERE,read,sha,require,load_source,source_context,validate_sources

BASE_STAGES=['leaver-manifest','slots-manifest','t16-manifest','base','cells','chain','independent-leaver','leaver-global','slots','t16']


def bind_baseline(work):
    work=Path(work).resolve();r=read(work/'RESULT.json')
    require(r['status']=='PASS_COMPLETE_PR1042_COMPOSITION','Complete selected baseline status')
    require(r['kappa']==read(ROOT/'research/gauge44-slots-t16/data/SPEC.json')['expected']['kappa'],'Selected kappa')
    names=[x['name'] for x in r['stages']]
    require(names in [BASE_STAGES,['baseline799-cold']+BASE_STAGES],'Complete baseline stage inventory')
    for stage in r['stages']:
        require(stage['exit_code']==0,'Baseline stage failed')
        p=(ROOT/stage['script']).resolve();require(p.is_relative_to(ROOT),'Baseline script containment')
        require(sha(p)==stage['script_sha256'],'Baseline stage source changed')
        require(sha(work/(stage['name']+'.log'))==stage['log_sha256'],'Baseline stage log changed')
    expected_artifacts=set(read(ROOT/'research/community-frontier1042-audit/RESULT.json')['artifacts'])
    if names[0]=='baseline799-cold':expected_artifacts.add('baseline799-cold.log')
    require(set(r['artifacts'])==expected_artifacts,'Exact selected baseline artifact inventory')
    require(r['reused_completed_baseline']==(names[0]!='baseline799-cold'),'Declared ancestry replay mode')
    for relative,digest in r['artifacts'].items():
        p=(work/relative).resolve();require(not Path(relative).is_absolute() and p.is_relative_to(work),'Baseline artifact containment')
        require(sha(p)==digest,'Baseline artifact changed: '+relative)
    require(sha(work/'BASELINE-BINDING.json')==r['baseline_binding_sha256'],'Baseline ancestry receipt')
    require(sha(work/'t16/ASSEMBLY.json')==r['selected_assembly_sha256'],'Baseline assembly binding')
    ids=load_source(ROOT/'research/gauge44-slots-t16/code/generated_identity.py','pr1042_baseline_identities')
    expected=read(ROOT/'research/gauge44-slots-t16/data/SPEC.json')['providers']['gauge44']['artifact_semantic_sha256']
    require(ids.artifact_identities(work/'slots/local')==expected,'Baseline is the exact selected native word')
    baseline799=Path(r['baseline']).resolve()
    coverage=load_source(ROOT/'scripts/verify_replay_coverage.py','pr1042_original_coverage')
    with source_context(ROOT/'scripts'):
        ancestry=coverage.check_selected(baseline799,baseline799/'ancestor')
    require(ancestry==read(work/'BASELINE-BINDING.json'),'Retained complete bit/PR799 ancestry')
    return dict(status='PASS_SOURCE_BOUND_COMPLETED_PR1042_BASELINE',result_sha256=sha(work/'RESULT.json'),artifact_count=len(r['artifacts']),stage_names=names,
      native_semantic_identities=expected,ancestry=ancestry)


def compare_invoices(baseline,hosted):
    a=read(Path(baseline)/'t16/global/audit/PREFIX-AND-INVOICE.json')
    b=read(Path(hosted)/'global/audit/PREFIX-AND-INVOICE.json')
    fields=['selected_local_paid_profile','provider_counts','complete_invocation_sweeps','bridge_sweeps','charged_prefix_bits','row_prefix_extra','helpers','centres','live','physical','physical_stock_identity','wrapper_elementary_factors_charged','factors_per_wrapper','compiler']
    for k in fields:require(a[k]==b[k],'Unchanged invoice field: '+k)
    prior_a,prior_b=a['retained_prior_overcharge'],b['retained_prior_overcharge']
    require(prior_a['previous_pervertex_allowance']==prior_b['previous_pervertex_allowance'] and prior_a['sha256']==prior_b['sha256'],'Entire prior allowance retained')
    delta=read(HERE/'COMPILE-RECEIPT.json')['invoice_delta']
    for k in ['conservative_pervertex_used','hosted_rebased_pervertex','unhosted_pervertex']:
        require(a[k]-b[k]==delta['global_pervertex_delta']>0,'Complete actual invoice decrease: '+k)
    require(a['local_primitive_bound']-b['local_primitive_bound']==delta['local_primitive_bound_delta'],'Local primitive delta')
    require(a['selected_real_component_primitives']-b['selected_real_component_primitives']==delta['selected_real_primitive_delta'],'Actual dispatch scalar delta')
    require(b['global_prefix_bits']<b['charged_prefix_bits']==512,'Strict charged precision reserve')
    require(set(a['strict_checks'])==set(b['strict_checks']) and len(b['strict_checks'])==9 and all(b['strict_checks'].values()),'Every strict finite invoice inequality')
    asm=read(Path(hosted)/'ASSEMBLY.json');oldasm=read(Path(baseline)/'t16/ASSEMBLY.json')
    require(asm['kappa']==oldasm['kappa'],'Selected conditional kappa preserved')
    require(asm['complex_profile']==oldasm['complex_profile'] and asm['bit_supplier']==oldasm['bit_supplier'],'Paid profile and complete inherited bit supplier unchanged')
    require(len(asm['outer'])==47 and all(Q(v)>0 for v in asm['outer'].values()),'All strict outer inequalities')
    saved=a['conservative_pervertex_used']-b['conservative_pervertex_used'];fraction=Q(saved,a['conservative_pervertex_used'])
    with localcontext() as ctx:
        ctx.prec=40;percent=str(100*Decimal(fraction.numerator)/Decimal(fraction.denominator))
    return dict(status='PASS_STRICTLY_CHEAPER_CURRENT_PR1042_COMPLETE_INVOICE',before=a['conservative_pervertex_used'],after=b['conservative_pervertex_used'],saved=saved,fraction_saved=str(fraction),percent_saved=percent,
      prefix_before=a['global_prefix_bits'],prefix_after=b['global_prefix_bits'],charged_prefix_bits=b['charged_prefix_bits'],kappa=asm['kappa'],
      unchanged_fields=fields,baseline_invoice_sha256=sha(Path(baseline)/'t16/global/audit/PREFIX-AND-INVOICE.json'),candidate_invoice_sha256=sha(Path(hosted)/'global/audit/PREFIX-AND-INVOICE.json'))


def bind_preparation(work):
    work=Path(work);r=read(work/'REBIND.json');pkg=ROOT/'research/gauge44-slots-t16'
    require(r['status']=='PASS_PR1042_PROVIDER_ONLY_DATA_REBIND','Provider-only preparation receipt')
    require(set(r['changed_files'])=={'data/PLAN.json','data/T8/PLAN.json','data/SPEC.json','data/SPEC-T8.json'},'Exact data update inventory')
    current={p.relative_to(pkg).as_posix():sha(p) for p in pkg.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    require(current==r['source_files'],'Complete original T16 package source preserved')
    prepared_names={p.relative_to(work/'package').as_posix() for p in (work/'package').rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    require(prepared_names==set(current),'Exact prepared package file inventory')
    for relative,digest in current.items():
        expected=r['changed_files'][relative]['after'] if relative in r['changed_files'] else digest
        require(sha(work/'package'/relative)==expected,'Prepared code/data changed: '+relative)
    from prepare_hosted import provider
    from rebind_plan import refreshed
    baseline,candidate=Path(r['baseline_local']),Path(r['candidate_local'])
    before,after=read(work/'before.json'),read(work/'after.json')
    require(sha(work/'before.json')==r['original_recount_sha256'] and sha(work/'after.json')==r['candidate_recount_sha256'],'Literal recount receipt bindings')
    for rel in ['data/T8/PLAN.json','data/PLAN.json']:
        rebuilt=refreshed(read(pkg/rel),baseline,candidate)
        if rel=='data/PLAN.json':rebuilt['source_plan_sha256']=sha(work/'package/data/T8/PLAN.json')
        require(rebuilt==read(work/'package'/rel),'Recomputed provider-only PLAN')
    for rel,plan in [('data/SPEC-T8.json','data/T8/PLAN.json'),('data/SPEC.json','data/PLAN.json')]:
        rebuilt=copy.deepcopy(read(pkg/rel));rebuilt['data']['plan_sha256']=sha(work/'package'/plan)
        rebuilt['providers']['gauge44']=provider(rebuilt['providers']['gauge44'],before,after)
        require(rebuilt==read(work/'package'/rel),'Recomputed strict provider-only SPEC')
    return dict(status='PASS_UNCHANGED_SELECTED_CHECKER_AND_EXACT_DATA_REBIND',changed_files=r['changed_files'],rebind_sha256=sha(work/'REBIND.json'))
