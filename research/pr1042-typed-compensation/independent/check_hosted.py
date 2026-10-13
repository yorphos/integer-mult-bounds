#!/usr/bin/env python3
"""Independent PR1042 actual dispatch, ownership and complete invoice audit.
Prepared with substantial OpenAI assistance. Apache-2.0.
"""
import argparse
import copy
import math
from collections import Counter
from fractions import Fraction as Q
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
SELECTED_MEMBERS = {
    't16/global/audit/PREFIX-AND-INVOICE.json': '0b4ef2b9713da47a00ed6a948ceb6074ed0108cae78a32ddd0dc0996c5c3bb75',
    't16/global/hosted/GLOBAL-TEMPLATE.json.gz': '73f47a1e60b1e4ea66dbca9a497c411c8e6adc7984e276a437a10a9a7a13b47a',
    't16/ASSEMBLY.json': '093f35445812ea96fe1bfe6a3af7d769cb7f274e08f4fb30f71a17ed1161e54e',
    'slots/local/CANONICAL-WORD.json.gz': '16bc0ebb04b4be6c0ade74badc6a0c0cdba4215eda86e4ff9f13abf8ecebd219',
    'slots/local/LOCAL-PROGRAMS.json.gz': '241fde27d4e43f5a9cb6b128f9f76c5131a53d09f0371676163f914d0b0fef3a',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    path = Path(path)
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def bits(q):
    q = Q(q)
    n = 0
    while Q(1 << n) < q:
        n += 1
    return n


# Exact causal closure of the two elapsed-time fields in the immutable archive.
# No mathematical value, ownership, profile, source value or extra field is omitted.
BASELINE_BINDINGS = {'slots/local/CANONICAL-WORD.json.gz': {'archive_raw_sha256': '16bc0ebb04b4be6c0ade74badc6a0c0cdba4215eda86e4ff9f13abf8ecebd219',
                                        'archive_content_sha256': '4ddb29fb9bc6f27e0c0fbfcf19a2a93a3496ad900d0f6d89059d0305c9576c0c',
                                        'normalized_content_sha256': '4ddb29fb9bc6f27e0c0fbfcf19a2a93a3496ad900d0f6d89059d0305c9576c0c',
                                        'timing_seconds': False,
                                        'bound_references': []},
 'slots/local/LOCAL-PROGRAMS.json.gz': {'archive_raw_sha256': '241fde27d4e43f5a9cb6b128f9f76c5131a53d09f0371676163f914d0b0fef3a',
                                        'archive_content_sha256': '9f41d53659e9be84e20c661560c5687abbf5cd0660cdecbe01ad5eb29e6b8ee3',
                                        'normalized_content_sha256': '9f41d53659e9be84e20c661560c5687abbf5cd0660cdecbe01ad5eb29e6b8ee3',
                                        'timing_seconds': False,
                                        'bound_references': []},
 'slots/local/CLIFFORD-REVIEW.json': {'archive_raw_sha256': 'cb0e10a8b284f176526c17177e91186ce09aa3e88b4f6acc561051daa072b0d0',
                                      'archive_content_sha256': '4dcd174adad352e2630764f1a82faacc5e6f67da6e8a9d6e805180208ac80430',
                                      'normalized_content_sha256': '070c9cc7757b44005ecbd85a271e42bc5f896da9a8d0274251e147933353f295',
                                      'timing_seconds': True,
                                      'bound_references': [('/canonical_word_sha256',
                                                            'slots/local/CANONICAL-WORD.json.gz',
                                                            'raw')]},
 'slots/local/SCALAR-FRAME-AUDIT.json': {'archive_raw_sha256': '0e2a979aae1b948e1bee6c49c218f3ce7d7df00814b3f53b3d0866497510a28b',
                                         'archive_content_sha256': '110b7719ae0e5e5f7d1b8d8552105e72782c1f8c36a247f5e4a546701ebce388',
                                         'normalized_content_sha256': '1f2c8f8a3aee9cd6ebe3fda473ccafb24b6f2626a218b21503e8ee52650eedcc',
                                         'timing_seconds': True,
                                         'bound_references': []},
 'slots/local/INDEPENDENT-LOCAL-REPLAY.json': {'archive_raw_sha256': '13dd18297162569532983db1a2ab67926b064330cd7edd3587e7b546b2dedf17',
                                               'archive_content_sha256': '510c6ec28beb87ee4c854a6bd492c7de8155b815d306e770245b49a074ac4774',
                                               'normalized_content_sha256': '510c6ec28beb87ee4c854a6bd492c7de8155b815d306e770245b49a074ac4774',
                                               'timing_seconds': False,
                                               'bound_references': [('/canonical_word_sha256',
                                                                     'slots/local/CANONICAL-WORD.json.gz',
                                                                     'raw'),
                                                                    ('/local_programs_sha256',
                                                                     'slots/local/LOCAL-PROGRAMS.json.gz',
                                                                     'raw')]},
 't16/global/PLAN.json': {'archive_raw_sha256': 'f6ac4c2f277b797b932ecb81eba3ec4eaf7a197faf4a8b8a9c349350cff7f52d',
                          'archive_content_sha256': '843101edd7eec689237c02979050e421b7ee9c7e33edf42fca9876396cbdb37d',
                          'normalized_content_sha256': '843101edd7eec689237c02979050e421b7ee9c7e33edf42fca9876396cbdb37d',
                          'timing_seconds': False,
                          'bound_references': [('/provider_registry/gauge44/artifact_sha256/CLIFFORD-REVIEW.json',
                                                'slots/local/CLIFFORD-REVIEW.json',
                                                'raw'),
                                               ('/provider_registry/gauge44/artifact_sha256/CANONICAL-WORD.json.gz',
                                                'slots/local/CANONICAL-WORD.json.gz',
                                                'raw'),
                                               ('/provider_registry/gauge44/artifact_sha256/LOCAL-PROGRAMS.json.gz',
                                                'slots/local/LOCAL-PROGRAMS.json.gz',
                                                'raw'),
                                               ('/provider_registry/gauge44/artifact_sha256/INDEPENDENT-LOCAL-REPLAY.json',
                                                'slots/local/INDEPENDENT-LOCAL-REPLAY.json',
                                                'raw')]},
 't16/global/hosted/GLOBAL-TEMPLATE.json.gz': {'archive_raw_sha256': '73f47a1e60b1e4ea66dbca9a497c411c8e6adc7984e276a437a10a9a7a13b47a',
                                               'archive_content_sha256': '8abaa0b526b17e3816d5250542c56f2a7074f58aa03dd07e606ec93d940a9048',
                                               'normalized_content_sha256': '8abaa0b526b17e3816d5250542c56f2a7074f58aa03dd07e606ec93d940a9048',
                                               'timing_seconds': False,
                                               'bound_references': [('/async_schedule/source_plan_sha256',
                                                                     't16/global/PLAN.json',
                                                                     'raw'),
                                                                    ('/local_providers/gauge44/canonical_word_sha256',
                                                                     'slots/local/CANONICAL-WORD.json.gz',
                                                                     'raw'),
                                                                    ('/local_providers/gauge44/local_programs_sha256',
                                                                     'slots/local/LOCAL-PROGRAMS.json.gz',
                                                                     'raw')]},
 't16/global/audit/ASYNC-AUDIT.json': {'archive_raw_sha256': '4a101df262652b03df72862f999bfd177296b3f52bc3dd9426795dc4cdaafc0f',
                                       'archive_content_sha256': '8b057c0e3d622e88284d714c7143efc60e3c7ae1285aeada04d46a2416249e05',
                                       'normalized_content_sha256': '8b057c0e3d622e88284d714c7143efc60e3c7ae1285aeada04d46a2416249e05',
                                       'timing_seconds': False,
                                       'bound_references': [('/template_sha256',
                                                             't16/global/hosted/GLOBAL-TEMPLATE.json.gz',
                                                             'content'),
                                                            ('/complex_template_sha256',
                                                             't16/global/hosted/GLOBAL-TEMPLATE.json.gz',
                                                             'content')]},
 't16/global/audit/OWNERS-AND-PROFILE.json': {'archive_raw_sha256': '888d63e292eed39215fe9f1440b15018f71507e13132f0e02bf0c636d56908e6',
                                              'archive_content_sha256': '07ab69350480dcd2aba12d8cd87fe84391832027caf2a6c803896a8125342392',
                                              'normalized_content_sha256': '07ab69350480dcd2aba12d8cd87fe84391832027caf2a6c803896a8125342392',
                                              'timing_seconds': False,
                                              'bound_references': [('/template_sha256',
                                                                    't16/global/hosted/GLOBAL-TEMPLATE.json.gz',
                                                                    'content'),
                                                                   ('/controller_audit_sha256',
                                                                    't16/global/audit/ASYNC-AUDIT.json',
                                                                    'raw'),
                                                                   ('/source_artifacts/providers~1gauge44~1CLIFFORD-REVIEW.json',
                                                                    'slots/local/CLIFFORD-REVIEW.json',
                                                                    'raw'),
                                                                   ('/source_artifacts/providers~1gauge44~1CANONICAL-WORD.json.gz',
                                                                    'slots/local/CANONICAL-WORD.json.gz',
                                                                    'raw'),
                                                                   ('/source_artifacts/providers~1gauge44~1LOCAL-PROGRAMS.json.gz',
                                                                    'slots/local/LOCAL-PROGRAMS.json.gz',
                                                                    'raw'),
                                                                   ('/source_artifacts/providers~1gauge44~1INDEPENDENT-LOCAL-REPLAY.json',
                                                                    'slots/local/INDEPENDENT-LOCAL-REPLAY.json',
                                                                    'raw')]},
 't16/global/audit/PREFIX-AND-INVOICE.json': {'archive_raw_sha256': '0b4ef2b9713da47a00ed6a948ceb6074ed0108cae78a32ddd0dc0996c5c3bb75',
                                              'archive_content_sha256': '6be10936750043ed43cc8a7208181b6e06247f0edea9c93e5e8f22d05dc15721',
                                              'normalized_content_sha256': '6be10936750043ed43cc8a7208181b6e06247f0edea9c93e5e8f22d05dc15721',
                                              'timing_seconds': False,
                                              'bound_references': [('/providers/gauge44/artifacts/CLIFFORD-REVIEW.json',
                                                                    'slots/local/CLIFFORD-REVIEW.json',
                                                                    'raw'),
                                                                   ('/providers/gauge44/artifacts/SCALAR-FRAME-AUDIT.json',
                                                                    'slots/local/SCALAR-FRAME-AUDIT.json',
                                                                    'raw'),
                                                                   ('/template_sha256',
                                                                    't16/global/hosted/GLOBAL-TEMPLATE.json.gz',
                                                                    'content'),
                                                                   ('/owner_audit_sha256',
                                                                    't16/global/audit/OWNERS-AND-PROFILE.json',
                                                                    'raw'),
                                                                   ('/controller_audit_sha256',
                                                                    't16/global/audit/ASYNC-AUDIT.json',
                                                                    'raw'),
                                                                   ('/providers/gauge44/artifacts/CANONICAL-WORD.json.gz',
                                                                    'slots/local/CANONICAL-WORD.json.gz',
                                                                    'raw'),
                                                                   ('/providers/gauge44/artifacts/LOCAL-PROGRAMS.json.gz',
                                                                    'slots/local/LOCAL-PROGRAMS.json.gz',
                                                                    'raw'),
                                                                   ('/providers/gauge44/artifacts/INDEPENDENT-LOCAL-REPLAY.json',
                                                                    'slots/local/INDEPENDENT-LOCAL-REPLAY.json',
                                                                    'raw')]},
 't16/ASSEMBLY.json': {'archive_raw_sha256': '093f35445812ea96fe1bfe6a3af7d769cb7f274e08f4fb30f71a17ed1161e54e',
                       'archive_content_sha256': '198aed27a2f80c8309fcf56110ff8f809919df3f103b1b7bd522f949c4270357',
                       'normalized_content_sha256': '198aed27a2f80c8309fcf56110ff8f809919df3f103b1b7bd522f949c4270357',
                       'timing_seconds': False,
                       'bound_references': [('/input_sha256/fresh_invoice',
                                             't16/global/audit/PREFIX-AND-INVOICE.json',
                                             'raw'),
                                            ('/input_sha256/owner_audit',
                                             't16/global/audit/OWNERS-AND-PROFILE.json',
                                             'raw'),
                                            ('/template_sha256',
                                             't16/global/hosted/GLOBAL-TEMPLATE.json.gz',
                                             'content')]}}


def content_sha(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def pointer_parent(value, pointer):
    keys=[k.replace('~1','/').replace('~0','~') for k in pointer.split('/')[1:]]
    for key in keys[:-1]:
        value=value[key]
    return value,keys[-1]


def bind_selected_baseline(root):
    root=Path(root)
    # Pin complete proof content, while checking every actual raw-container reference.
    original={name:read(root/name) for name in BASELINE_BINDINGS}
    raw={name:sha(root/name) for name in BASELINE_BINDINGS}
    semantic={name:content_sha(value) for name,value in original.items()}
    observed_seconds={}
    for name,rule in BASELINE_BINDINGS.items():
        value=copy.deepcopy(original[name])
        if rule['timing_seconds']:
            elapsed=value.pop('seconds')
            require(type(elapsed) in (int,float) and math.isfinite(elapsed) and elapsed>=0,
                    'finite nonnegative baseline seconds: '+name)
            observed_seconds[name]=elapsed
        for pointer,dependency,kind in rule['bound_references']:
            parent,key=pointer_parent(value,pointer)
            actual=raw[dependency] if kind=='raw' else semantic[dependency]
            require(parent[key]==actual,'actual baseline dependency: '+name+pointer)
            parent[key]=BASELINE_BINDINGS[dependency]['archive_'+kind+'_sha256']
        require(content_sha(value)==rule['normalized_content_sha256'],
                'exact selected baseline content apart from bound elapsed times: '+name)
    for name in ('CANONICAL-WORD.json.gz','LOCAL-PROGRAMS.json.gz','CLIFFORD-REVIEW.json','SCALAR-FRAME-AUDIT.json','INDEPENDENT-LOCAL-REPLAY.json'):
        require(read(root/'slots/local'/name)==read(root/'t16/global/base/providers/gauge44'/name),
                'fresh baseline hosted provider artifact: '+name)
    return {'status':'PASS_EXACT_SELECTED_BASELINE_WITH_BOUND_ELAPSED_TIMES',
            'original_archive_member_sha256':{n:r['archive_raw_sha256'] for n,r in BASELINE_BINDINGS.items()},
            'observed_artifact_sha256':raw,'observed_seconds':observed_seconds,
            'normalized_content_sha256':{n:r['normalized_content_sha256'] for n,r in BASELINE_BINDINGS.items()},
            'bound_reference_count':sum(len(r['bound_references']) for r in BASELINE_BINDINGS.values()),
            'excluded_fields':['slots/local/CLIFFORD-REVIEW.json#/seconds','slots/local/SCALAR-FRAME-AUDIT.json#/seconds']}


def check(baseline_replay, candidate_local, hosted_work):
    if hasattr(sys, 'set_int_max_str_digits'):
        sys.set_int_max_str_digits(0)
    baseline_replay, candidate_local, hosted_work = map(Path, (baseline_replay,candidate_local,hosted_work))
    baseline_binding=bind_selected_baseline(baseline_replay)
    spec = importlib.util.spec_from_file_location('independent_pr1042_primitives', HERE/'verify.py')
    scalar = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scalar)
    old_invoice = read(baseline_replay/'t16/global/audit/PREFIX-AND-INVOICE.json')
    old_template = read(baseline_replay/'t16/global/hosted/GLOBAL-TEMPLATE.json.gz')
    old_assembly = read(baseline_replay/'t16/ASSEMBLY.json')
    invoice = read(hosted_work/'global/audit/PREFIX-AND-INVOICE.json')
    template = read(hosted_work/'global/hosted/GLOBAL-TEMPLATE.json.gz')
    assembly = read(hosted_work/'ASSEMBLY.json')
    word, programs = scalar.read_local(candidate_local)
    bw, bp = scalar.read_local(baseline_replay/'slots/local')
    scalar.check_boundary(bw,bp,word,programs)
    scalar.check_panel(bw,word)
    hosted_word, hosted_programs = scalar.read_local(hosted_work/'global/base/providers/gauge44')
    require(hosted_word == word and hosted_programs == programs, 'hosted provider equals actual native candidate')
    require(template['local_providers']['gauge44']['local_programs'] == programs,
            'literal hosted template dispatch programs equal candidate')
    replays = {d:scalar.replay(programs[d],word,d) for d in scalar.BASE_PROGRAMS}
    prices = {d:r['complex_real_primitives'] for d,r in replays.items()}
    macros = {d:sum(e[0]=='scalar' for e in events) for d,events in programs.items()}
    hashes = {d:scalar.digest(events) for d,events in programs.items()}
    require(invoice['providers']['gauge44']['program_hashes'] == hashes, 'invoice actual provider bindings')
    for d in programs:
        require(invoice['providers']['gauge44']['local'][d]['prefix_l1'] == replays[d]['positive_prefix_l1_upper'],
                'independently recomputed primitive positive prefix')
    require(len(template['calls']) == len(old_template['calls']) == len(invoice['selected_calls']) == 144,
            '144 actual whole calls, fully billed')
    for key in ('hosting','idle_children','bank_padding','private_namespace','execution_schedule','recipe',
                'live','physical','port_restriction','cover','cover_final_correction','replica_lift'):
        require(template[key] == old_template[key], 'unchanged physical controller field: '+key)
    require({k:v for k,v in template['async_schedule'].items() if k!='source_plan_sha256'} ==
            {k:v for k,v in old_template['async_schedule'].items() if k!='source_plan_sha256'},
            'unchanged complete asynchronous schedule apart from refreshed plan identity')
    require(template['async_schedule']['source_plan_sha256'] == sha(hosted_work/'global/PLAN.json') and
            old_template['async_schedule']['source_plan_sha256'] == sha(baseline_replay/'t16/global/PLAN.json'),
            'both actual asynchronous plan identities')
    pooled = template['hosting']['pooled_slots']
    require(len(pooled) == 69120, 'literal nonempty whole-helper ownership')
    require(len({(r['stage'],r['replica'],r['helper']) for r in pooled}) == 69120,
            'all helper-role identities distinct')
    widths = invoice['providers']['gauge44']['widths']
    require(widths == old_invoice['providers']['gauge44']['widths'] and len(widths) == 480,
            'all actual helper widths preserved')
    require(Counter(widths) == {4:56,5:32,7:30,8:122,9:240}, 'selected R480 width inventory')
    require(widths == [len(word['frames'][word['final'][r]])-len(word['frames'][word['start'][r]])
                       for r in range(224,704)], 'widths independently derived from literal entrance and final frames')
    require(all(r['width'] == widths[r['helper']] for r in pooled), 'every actual helper-role width')
    by_role = {(r['stage'],r['replica'],r['helper']):r for r in pooled}
    counts = Counter(); roles = 0
    for old_call, call, billed in zip(old_template['calls'],template['calls'],invoice['selected_calls']):
        require({k:v for k,v in call.items() if k!='local_program_sha256'} ==
                {k:v for k,v in old_call.items() if k!='local_program_sha256'}, 'unchanged complete call owner routes')
        d = call['orientation']
        require(call['provider_id'] == 'gauge44' and call['local_program_sha256'] == hashes[d],
                'literal candidate whole-call dispatch')
        require(len(call['owners']) == 704 and len({r[0] for r in call['owners']}) == 704,
                'all logical registers have distinct physical owner routes')
        for helper, route in enumerate(call['owners'][224:]):
            require(route[0] == by_role[call['stage'],call['replica'],helper]['family'],
                    'literal helper route matches its full physical owner nomination')
        roles += len(call['owners'])-224
        counts[d] += 1
        for key in ('stage','replica','provider_id','orientation'):
            require(billed[key] == call[key], 'invoice call identity: '+key)
        require(billed['program_sha256'] == hashes[d] and billed['macros'] == macros[d] and
                billed['real_component_primitives'] == prices[d], 'fully charged selected call')
    require(roles == 69120 and counts == {'forward':80,'backward':64}, 'complete nonvacuous orientation census')
    require(invoice['selected_real_component_primitives'] == sum(counts[d]*prices[d] for d in counts),
            'actual global primitive sum')
    require(invoice['selected_scalar_macros'] == sum(counts[d]*macros[d] for d in counts), 'actual global macro sum')
    compiler = 64*74**3
    children = sum(word['local_profile'].values())
    adapters = 16*(max(macros.values())+children+704+8)+64*73
    local_bound = max(prices.values())+adapters*compiler
    require(invoice['compiler'] == compiler and invoice['local_adapters'] == adapters and
            invoice['local_primitive_bound'] == local_bound, 'unchanged full local compiler invoice formula')
    for key in ('selected_local_paid_profile','provider_counts','complete_invocation_sweeps','bridge_sweeps',
                'charged_prefix_bits','row_prefix_extra','helpers','centres','live','physical','physical_stock_identity',
                'wrapper_elementary_factors_charged','factors_per_wrapper'):
        require(invoice[key] == old_invoice[key], 'unchanged full-invoice term: '+key)
    real_saved = old_invoice['selected_real_component_primitives']-invoice['selected_real_component_primitives']
    adapter_saved = old_invoice['local_adapters']-adapters
    saved = real_saved+144*adapter_saved*compiler
    require(real_saved > 0 and adapter_saved > 0, 'strict scalar and adapter improvement')
    for field in ('unhosted_pervertex','hosted_rebased_pervertex','conservative_pervertex_used'):
        require(old_invoice[field]-invoice[field] == saved > 0, 'complete retained-invoice decrease: '+field)
    retained = invoice['retained_prior_overcharge']
    for key in ('previous_pervertex_allowance','sha256','policy'):
        require(retained[key] == old_invoice['retained_prior_overcharge'][key], 'entire historical overcharge retained')
    require(retained['added_complete_new_pervertex'] == invoice['unhosted_pervertex'] and
            invoice['conservative_pervertex_used'] == invoice['unhosted_pervertex']+retained['previous_pervertex_allowance'],
            'full conservative invoice identity')
    prefix = max(bits(r['positive_prefix_l1_upper']) for r in replays.values())+37+144+144+4
    require(prefix == invoice['global_prefix_bits'] < invoice['charged_prefix_bits'] == 512, 'actual global prefix reserve')
    require(invoice['physical'] == 14826 and invoice['physical_stock_identity'] ==
            {'data_and_owner_families':14336,'local_helpers':480,'private_centres':8,'coefficient_work':2},
            'actual selected physical stock')
    require(invoice['finite']['physical_stock_bits'] == 2642 and
            invoice['finite']['physical_row_coefficient'] == 2*2642+9909+252+2*512 == 16469 < 20161,
            'complete row reserve')
    require(len(invoice['strict_checks']) == 9 and all(v is True for v in invoice['strict_checks'].values()),
            'all nine strict invoice constraints')
    require(len(assembly['outer']) == 47 and all(Q(v)>0 for v in assembly['outer'].values()), 'all 47 outer constraints')
    require(assembly['complex_profile'] == old_assembly['complex_profile'] and assembly['kappa'] == old_assembly['kappa'],
            'unchanged selected recurrence and exact exponent')
    paths = ['global/audit/PREFIX-AND-INVOICE.json','global/hosted/GLOBAL-TEMPLATE.json.gz','ASSEMBLY.json',
             'global/base/providers/gauge44/CANONICAL-WORD.json.gz','global/base/providers/gauge44/LOCAL-PROGRAMS.json.gz']
    return {'status':'PASS_INDEPENDENT_COMPLETE_PR1042_HOSTED_INVOICE', 'complete_calls':144,
            'orientation_counts':dict(counts),'actual_helper_roles':roles,'actual_physical_stock':14826,
            'retained_independent_physical_upper_bound':14850,'paid_children_per_call':children,
            'real_primitives_per_orientation':prices,'scalar_macros_per_orientation':macros,
            'selected_real_primitives_saved':real_saved,'complete_conservative_invoice_saved':saved,
            'conservative_invoice_fraction_saved':str(Q(saved,old_invoice['conservative_pervertex_used'])),
            'actual_prefix_bits':prefix,'charged_prefix_bits':512,'row_charge':16469,
            'strict_invoice_checks':9,'positive_outer_constraints':47,'kappa':assembly['kappa'],
            'baseline_binding':baseline_binding,'immutable_selected_members':SELECTED_MEMBERS,'actual_artifact_sha256':{n:sha(hosted_work/n) for n in paths},
            'candidate_local_artifacts_sha256':{n:sha(candidate_local/n) for n in ('CANONICAL-WORD.json.gz','LOCAL-PROGRAMS.json.gz')},
            'scope':'Independent literal PR1042 dispatch, ownership and complete retained invoice. No new exponent or discharge of inherited all-size assumptions.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-replay',type=Path,required=True)
    parser.add_argument('--candidate-local',type=Path,required=True)
    parser.add_argument('--hosted-work',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    a = parser.parse_args()
    require(not a.out.exists(), 'fresh independent receipt')
    result = check(a.baseline_replay,a.candidate_local,a.hosted_work)
    with a.out.open('x') as stream:
        json.dump(result,stream,indent=2,sort_keys=True);stream.write('\n')
    print(result['status'])


if __name__ == '__main__':
    main()
