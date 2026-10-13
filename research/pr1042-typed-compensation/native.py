"""Install an equivalent compensation panel through the unchanged native compiler.

The scalar event alphabet, compiler, frame/wrapper checker and exact Clifford
lowerer are all retained unchanged. Only canonical.compensation is replaced.
"""
import argparse
import copy
from fractions import Fraction as Q
from pathlib import Path
import sys

from support import (HERE, ROOT, PR635, PR558, PR552, read, sha, payload_sha, identity,
                     require, dump, gzip_json, fresh_directory, run_stage)

SELECTED_CANONICAL = '4ddb29fb9bc6f27e0c0fbfcf19a2a93a3496ad900d0f6d89059d0305c9576c0c'
FILES = ('CANONICAL-WORD.json.gz', 'LOCAL-PROGRAMS.json.gz', 'LOCAL-CHECKS.json',
         'INDEPENDENT-LOCAL-REPLAY.json', 'RESIDUAL-ADAPTERS.json', 'WRAPPER-CHECKS.json',
         'CLIFFORD-RECIPES.json', 'CLIFFORD-REVIEW.json')


def panel_operator(panel, n, backward=False):
    rows = [{i: Q(1)} for i in range(n)]
    for gate in panel:
        require(len(gate) == 6 and gate[0] == 'add' and gate[-1] == 0, 'Typed frame-zero ADD panel')
        _, t, s, a, b, _ = gate
        require(type(t) is int and type(s) is int and 0 <= t < n and 0 <= s < n and t != s, 'Panel register type/range/alias')
        require(type(a) is int and type(b) is int and a and b > 0 and b & (b-1) == 0, 'Nonzero dyadic coefficient')
        if backward:
            t, s, a = s, t, -a
        for j, value in list(rows[s].items()):
            total = rows[t].get(j, Q(0)) + Q(a, b)*value
            if total:
                rows[t][j] = total
            else:
                rows[t].pop(j, None)
    return rows


def verify_substitution(original, candidate):
    require(set(original) == set(candidate), 'Canonical field inventory')
    require(all(original[k] == candidate[k] for k in original if k != 'compensation'), 'Only compensation may change')
    n = 2*original['v'] + original['R']
    touched = sorted({r for e in candidate['compensation'] for r in e[1:3]})
    wrapped = {r for r in range(2*original['v'], n) if original['start'][r] != 0 or original['final'][r] != 1}
    require(all(original['start'][r] == 0 and r not in wrapped for r in touched), 'Panel common frame and pre-wrapper exclusion')
    for backward in (False, True):
        require(panel_operator(original['compensation'], n, backward) == panel_operator(candidate['compensation'], n, backward), 'Exact arbitrary-dirty panel identity')
    return dict(columns_each_orientation=n, orientations=2, touched_registers=touched,
                wrapped_helpers_excluded=True, changed_fields=['compensation'])


def execute_native(local, directory):
    stages = []
    for name, script, arguments in (
        ('ledgers', PR635/'code/hpe_emit_local.py', [local]),
        ('local-replay', PR635/'code/hpe_audit_local.py', [local]),
        ('wrappers', PR635/'code/hpe_adapters_local.py', [local/'CANONICAL-WORD.json.gz', local/'RESIDUAL-ADAPTERS.json', local/'WRAPPER-CHECKS.json']),
        ('phases', PR558/'code/phases_full.py', [local, PR552/'complex-global/vendor531/vendor/clifford']),
    ):
        run_stage(directory, stages, name, script, *arguments, portable=True)
    return stages


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-local', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not sys.flags.optimize, 'Assertions are required by retained source checkers')
    baseline = args.baseline_local.resolve()
    require(payload_sha(baseline/'CANONICAL-WORD.json.gz') == SELECTED_CANONICAL, 'Exact selected PR1042 canonical source')
    for name in FILES:
        require((baseline/name).is_file(), 'Missing completed baseline native artifact: ' + name)
    source_hashes = {name: sha(baseline/name) for name in FILES}
    original = read(baseline/'CANONICAL-WORD.json.gz')
    from compiler import compile_compensation
    panel, recipe = compile_compensation(original)
    require(recipe == read(HERE/'COMPILE-RECEIPT.json')['construction'], 'Frozen source-bound compiler receipt')
    candidate = copy.deepcopy(original)
    candidate['compensation'] = panel
    identity_check = verify_substitution(original, candidate)
    out = fresh_directory(args.out)
    local = out/'local'
    local.mkdir()
    gzip_json(local/'CANONICAL-WORD.json.gz', candidate)
    dump(out/'RECIPE.json', recipe)
    dump(out/'SUBSTITUTION.json', identity_check)
    stages = execute_native(local, out)
    baseline_programs = read(baseline/'LOCAL-PROGRAMS.json.gz')
    new_programs = read(local/'LOCAL-PROGRAMS.json.gz')
    old_checks, new_checks = read(baseline/'LOCAL-CHECKS.json'), read(local/'LOCAL-CHECKS.json')
    for orientation in ('forward', 'backward'):
        require([e for e in baseline_programs[orientation] if e[0] != 'scalar'] == [e for e in new_programs[orientation] if e[0] != 'scalar'], 'Exact non-scalar event preservation')
        require(old_checks[orientation]['paid_profile'] == new_checks[orientation]['paid_profile'], 'Paid child preservation')
        for field in ('scalar_macros', 'real_component_primitive_bound'):
            require(new_checks[orientation][field] < old_checks[orientation][field], 'Strict complete-orientation gain: ' + field)
    require(read(baseline/'CLIFFORD-RECIPES.json') == read(local/'CLIFFORD-RECIPES.json'), 'Exact phase recipes unchanged')
    require(read(baseline/'RESIDUAL-ADAPTERS.json') == read(local/'RESIDUAL-ADAPTERS.json'), 'Residual wrapper recipes unchanged')
    from cost import recount_events, invoice_delta
    before = {o:recount_events(events) for o,events in baseline_programs.items()}
    after = {o:recount_events(events) for o,events in new_programs.items()}
    complete_compile = dict(construction=recipe,before=before,after=after,invoice_delta=invoice_delta(before,after))
    require(identity(complete_compile) == identity(read(HERE/'COMPILE-RECEIPT.json')), 'Complete recomputed compilation receipt')
    require(source_hashes == {name: sha(baseline/name) for name in FILES}, 'Baseline artifacts changed')
    result = dict(status='PASS_PR1042_TYPED_COMPENSATION_UNCHANGED_NATIVE_CHAIN',
                  baseline_artifacts=source_hashes, candidate_artifacts={name: sha(local/name) for name in FILES},
                  substitution=identity_check, recipe_sha256=sha(out/'RECIPE.json'),
                  complete_compile_receipt_sha256=sha(HERE/'COMPILE-RECEIPT.json'), stages=stages,
                  programs={name: dict(baseline=old_checks[name], candidate=new_checks[name]) for name in old_checks},
                  native_replay=read(local/'INDEPENDENT-LOCAL-REPLAY.json'),
                  scope='Actual unchanged native scalar/frame/wrapper/phase admission. Global owner/controller/invoice admission is a separate driver stage.')
    dump(out/'RESULT.json', result)
    print(result['status'])


if __name__ == '__main__':
    main()
