"""Refresh only the native provider records of the unchanged T16 owner plan."""
import argparse
import copy
from pathlib import Path

from native import FILES, verify_substitution
from support import ROOT, read, sha, require, dump, load_source


def refreshed(plan, baseline, candidate):
    identity_module = load_source(ROOT/'research/gauge44-slots-t16/code/generated_identity.py', 'u8_generated_identity')
    old_word = read(baseline/'CANONICAL-WORD.json.gz')
    new_word = read(candidate/'CANONICAL-WORD.json.gz')
    verify_substitution(old_word, new_word)
    old_checks = read(baseline/'LOCAL-CHECKS.json')
    new_checks = read(candidate/'LOCAL-CHECKS.json')
    require(set(plan['provider_registry']) == {'gauge44'}, 'Single selected PR1042 provider')
    old = plan['provider_registry']['gauge44']
    require(old['artifact_semantic_sha256'] == identity_module.artifact_identities(baseline), 'Plan must bind the original native PR1042 provider')
    require(old['orientation_program_sha256'] == {k: v['sha256'] for k,v in old_checks.items()}, 'Original plan program bindings')
    widths = [len(new_word['frames'][new_word['final'][r]])-len(new_word['frames'][new_word['start'][r]]) for r in range(224,704)]
    require(old['ports'] == new_word['ports'] and old['centers'] == new_word['centers'] and old['widths'] == widths, 'Unchanged ports/centers/whole-helper widths')
    require(old['actual_paid_profile'] == new_word['local_profile'], 'Unchanged paid profile')
    for orientation in ('forward', 'backward'):
        require(old_checks[orientation]['paid_profile'] == new_checks[orientation]['paid_profile'], 'Same native paid children')
        require(new_checks[orientation]['scalar_macros'] < old_checks[orientation]['scalar_macros'], 'Strict complete macro gain')
        require(new_checks[orientation]['real_component_primitive_bound'] < old_checks[orientation]['real_component_primitive_bound'], 'Strict complete primitive gain')
    new = copy.deepcopy(plan)
    registry = new['provider_registry']['gauge44']
    registry['artifact_sha256'] = {name: sha(candidate/name) for name in identity_module.FILES}
    registry['artifact_semantic_sha256'] = identity_module.artifact_identities(candidate)
    registry['orientation_program_sha256'] = {k: v['sha256'] for k,v in new_checks.items()}
    for before, after in zip(plan['provider_calls'], new['provider_calls']):
        require(before['provider'] == 'gauge44' and before['local_program_sha256'] == old_checks[before['orientation']]['sha256'], 'All original call bindings')
        after['local_program_sha256'] = new_checks[before['orientation']]['sha256']
    # Remove exactly the permitted fields, then require literal equality.
    a, b = copy.deepcopy(plan), copy.deepcopy(new)
    for value in (a,b):
        reg = value['provider_registry']['gauge44']
        for key in ('artifact_sha256', 'artifact_semantic_sha256', 'orientation_program_sha256'):
            del reg[key]
        for call in value['provider_calls']:
            del call['local_program_sha256']
    require(a == b, 'No owner, order, width, frame, profile or dispatch change')
    return new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--baseline-local', type=Path, required=True)
    parser.add_argument('--candidate-local', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'Refuse to replace a rebind receipt')
    backup = args.plan.with_name('PLAN-BEFORE-COMPENSATION.json')
    require(not backup.exists(), 'Refuse to replace the original plan snapshot')
    original_bytes = args.plan.read_bytes()
    plan = read(args.plan)
    candidate = refreshed(plan, args.baseline_local.resolve(), args.candidate_local.resolve())
    backup.write_bytes(original_bytes)
    dump(args.plan, candidate)
    dump(args.out, dict(status='PASS_EXACT_PR1042_PROVIDER_REBIND_UNCHANGED_OWNER_GEOMETRY',
        original_plan_sha256=sha(backup), candidate_plan_sha256=sha(args.plan),
        baseline_native={n:sha(args.baseline_local/n) for n in FILES},
        candidate_native={n:sha(args.candidate_local/n) for n in FILES},
        allowed_changes=['provider_registry.gauge44.artifact_sha256',
                         'provider_registry.gauge44.artifact_semantic_sha256',
                         'provider_registry.gauge44.orientation_program_sha256',
                         'provider_calls[*].local_program_sha256']))
    print('PASS_EXACT_PR1042_PROVIDER_REBIND_UNCHANGED_OWNER_GEOMETRY')


if __name__ == '__main__':
    main()
