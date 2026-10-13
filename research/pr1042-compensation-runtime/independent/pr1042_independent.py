#!/usr/bin/env python3
"""Independent literal PR1042 replacement and inherited binary-Horner replay.

This module imports no candidate constructor, emitter, auditor or compiler.
Its finite scalar checks do not replace the separately run native/global chain.
Prepared with substantial OpenAI assistance. Apache-2.0.
"""
import argparse
import copy
import gzip
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path

Q = Fraction
BASE_WORD = '4ddb29fb9bc6f27e0c0fbfcf19a2a93a3496ad900d0f6d89059d0305c9576c0c'
BASE_PROGRAMS = {
    'forward': '071ecdacc0bb3ac16046aad4119ed551a945cb0ed6c57002a548a3e2232503d8',
    'backward': 'f36c5831106f5637102c6bedeec76ed2b223c6671ce42fd0eceed9ef24725b23',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read_local(directory):
    directory = Path(directory)
    return tuple(json.loads(gzip.decompress((directory / name).read_bytes())) for name in
                 ('CANONICAL-WORD.json.gz', 'LOCAL-PROGRAMS.json.gz'))


def dyadic(a, b):
    require(type(a) is int and type(b) is int and b != 0, 'integer rational operands')
    q = Q(a, b)
    require(q.denominator & (q.denominator - 1) == 0, 'dyadic coefficient')
    return q


def add_row(dst, src, q):
    result = dict(dst)
    for column, value in src.items():
        value = result.get(column, Q(0)) + q * value
        if value:
            result[column] = value
        else:
            result.pop(column, None)
    return result


def panel_event(op, direction):
    require(isinstance(op, list) and len(op) == 6 and op[0] == 'add', 'panel ADD shape')
    _, target, source, a, b, frame = op
    if direction == 'backward':
        target, source, a = source, target, -a
    return ['scalar', ['add', ['L', target], ['L', source], a, b], frame]


def check_boundary(base_word, base_programs, candidate_word, candidate_programs):
    """Check actual substitution and physical wrapper eligibility, not just identity."""
    require(digest(base_word) == BASE_WORD, 'selected PR1042 canonical binding')
    require(set(base_programs) == set(BASE_PROGRAMS), 'baseline orientations')
    for direction, sha in BASE_PROGRAMS.items():
        require(digest(base_programs[direction]) == sha, 'selected PR1042 program binding: ' + direction)
    require(set(candidate_word) == set(base_word), 'canonical field inventory')
    require(all(candidate_word[k] == base_word[k] for k in base_word if k != 'compensation'),
            'only compensation may change')
    require(set(candidate_programs) == set(BASE_PROGRAMS), 'candidate orientations')
    n, helpers = base_word['v'], base_word['R']
    width = 2 * n + helpers
    require((n, helpers, base_word['h']) == (112, 480, 9), 'selected PR1042 dimensions')
    touched = set()
    for op in candidate_word['compensation']:
        require(isinstance(op, list) and len(op) == 6 and op[0] == 'add', 'panel ADD shape')
        _, target, source, a, b, frame = op
        require(type(target) is int and type(source) is int and n <= target < width
                and n <= source < width and target != source, 'target/helper panel domains')
        require(type(frame) is int and frame == 0, 'panel frame zero')
        require(dyadic(a, b) != 0, 'nonzero panel coefficient')
        for reg in (target, source):
            require(base_word['start'][reg] == 0, 'panel register starts at frame zero')
            require(reg < 2 * n or base_word['final'][reg] == 1,
                    'panel helper is unwrapped: no early cold-HPE access')
            touched.add(reg)
    prefix_length = 1 + len(base_word['precondition'])
    for direction in BASE_PROGRAMS:
        original = base_programs[direction]
        candidate = candidate_programs[direction]
        left = prefix_length
        old_right = left + len(base_word['compensation'])
        new_right = left + len(candidate_word['compensation'])
        require(original[0] == ['phase', 'zero_frame_precondition']
                and original[old_right] == ['phase', 'entry_adapters'], 'original panel boundary')
        require(original[left:old_right] == [panel_event(op, direction) for op in base_word['compensation']],
                'baseline literal panel binding')
        require(candidate[left:new_right] == [panel_event(op, direction) for op in candidate_word['compensation']],
                'candidate literal panel binding')
        require(original[:left] == candidate[:left] and original[old_right:] == candidate[new_right:],
                'all surrounding scalar/non-scalar events preserved')
        require([e for e in original if e[0] != 'scalar'] == [e for e in candidate if e[0] != 'scalar'],
                'non-scalar events preserved')
    return {'touched_targets': len([r for r in touched if r < 2*n]),
            'touched_helpers': len([r for r in touched if r >= 2*n]),
            'every_touched_register_starts_zero': True,
            'every_touched_helper_ends_full_and_is_unwrapped': True,
            'all_noncompensation_fields_and_events_unchanged': True}


def check_panel(base_word, candidate_word):
    """Replay all 592 arbitrary target/helper columns with exact rational rows."""
    n = base_word['v']
    width = 2 * n + base_word['R']
    result = {}
    for direction in BASE_PROGRAMS:
        expected = {r: {r: Q(1)} for r in range(n, width)}
        actual = {r: {r: Q(1)} for r in range(n, width)}
        for word, rows in ((base_word, expected), (candidate_word, actual)):
            for op in word['compensation']:
                _, e, _ = panel_event(op, direction)
                dst, src = e[1][1], e[2][1]
                rows[dst] = add_row(rows[dst], rows[src], dyadic(e[3], e[4]))
        require(actual == expected, 'exact arbitrary-input panel identity: ' + direction)
        result[direction] = {'arbitrary_columns': width - n, 'exact_endpoint_equal': True}
    return result


def primitive_stream(events):
    """Literal, independently specified PR635 binary-Horner program.

    Work W is cleared before and after every ADD. Negative final accumulation
    uses one signed addition. Counts are single-real-coordinate primitives.
    """
    work = ('W', 0)
    for event in events:
        if event[0] != 'scalar':
            continue
        op = event[1]
        tag, dst = op[0], tuple(op[1])
        if tag in ('clear', 'copy'):
            yield (tag, dst) if tag == 'clear' else (tag, dst, tuple(op[2]))
        elif tag == 'scale':
            q = dyadic(op[2], op[3])
            a, b = abs(q.numerator), q.denominator
            require(a and a & (a - 1) == 0, 'power-of-two scale')
            exponent = a.bit_length() - b.bit_length()
            for _ in range(abs(exponent)):
                yield ('scale', dst, Q(2) if exponent > 0 else Q(1, 2))
            if q < 0:
                yield ('scale', dst, Q(-1))
        else:
            require(tag == 'add' and len(op) == 5, 'scalar operation inventory')
            src = tuple(op[2])
            require(src != dst and src != work and dst != work, 'independent coefficient work')
            q = dyadic(op[3], op[4])
            require(q, 'nonzero emitted ADD')
            bits = bin(abs(q.numerator))[2:]
            yield ('clear', work)
            for i, bit in enumerate(bits):
                if i:
                    yield ('scale', work, Q(2))
                if bit == '1':
                    yield ('add', work, src, Q(1))
            for _ in range(q.denominator.bit_length() - 1):
                yield ('scale', work, Q(1, 2))
            yield ('add', dst, work, Q(1 if q > 0 else -1))
            yield ('clear', work)


def replay(events, word, direction):
    """All 704 logical and 9 arbitrary private columns, every primitive prefix."""
    n = word['v']
    width = 2*n + word['R']
    registers = [('L', r) for r in range(width)] + [('C', k) for k in range(len(word['centers']))] + [('W', 0)]
    rows = {reg: {i: Q(1)} for i, reg in enumerate(registers)}
    positive = dict.fromkeys(registers, Q(1))
    exact_max = Q(1)
    positive_max = Q(1)
    fractional_bits = 0
    count = 0
    histogram = Counter()
    stream_hash = hashlib.sha256()
    for primitive in primitive_stream(events):
        count += 1
        tag, dst = primitive[:2]
        require(dst in rows, 'primitive destination domain')
        histogram[tag] += 1
        stream_hash.update((repr(primitive)+'\n').encode())
        if tag == 'clear':
            rows[dst] = {}
            positive[dst] = Q(0)
        elif tag == 'copy':
            src = primitive[2]
            require(src in rows, 'primitive source domain')
            rows[dst] = dict(rows[src])
            positive[dst] = positive[src]
        elif tag == 'scale':
            q = primitive[2]
            rows[dst] = {i: q*x for i, x in rows[dst].items()}
            positive[dst] *= abs(q)
        else:
            src, q = primitive[2:]
            require(src in rows, 'primitive source domain')
            rows[dst] = add_row(rows[dst], rows[src], q)
            positive[dst] += abs(q) * positive[src]
        values = rows[dst].values()
        exact_max = max(exact_max, sum((abs(q) for q in values), Q(0)))
        positive_max = max(positive_max, positive[dst])
        fractional_bits = max(fractional_bits, max((q.denominator.bit_length()-1 for q in rows[dst].values()), default=0))
    for r in range(width):
        expected = {r: Q(1)}
        if direction == 'forward' and n <= r < 2*n:
            expected[r-n] = Q(1)
        elif direction == 'backward' and r < n:
            expected[r+n] = Q(-1)
        require(rows['L', r] == expected, 'complete endpoint logical register ' + str(r))
    require(all(not rows[reg] for reg in registers if reg[0] != 'L'), 'all arbitrary private inputs erased')
    require(positive_max < 2**192, 'inherited local 192-bit positive envelope')
    return {'all_arbitrary_columns': len(registers), 'logical_columns': width, 'private_columns': len(registers)-width,
            'private_input_semantics': 'erased, not restored', 'single_real_primitives': count,
            'complex_real_primitives': 2*count, 'primitive_histogram': dict(sorted(histogram.items())),
            'primitive_stream_sha256': stream_hash.hexdigest(), 'exact_prefix_l1': str(exact_max),
            'positive_prefix_l1_upper': str(positive_max), 'max_exact_fractional_bits': fractional_bits,
            'all_logical_helpers_restored': True, 'private_center_and_coefficient_work_erased': True}


def check_emitter_receipt(events, word, replayed, reported):
    paid = Counter()
    for event in events:
        if event[0] == 'climb':
            paid[event[5]] += 1
        elif event[0] == 'center':
            paid[event[4]] += 1
    require(dict(paid) == {int(k): v for k,v in word['local_profile'].items()}, 'literal paid child profile')
    require(reported['sha256'] == digest(events), 'emitter program digest')
    require(reported['events'] == len(events), 'emitter event count')
    require(reported['scalar_macros'] == sum(e[0] == 'scalar' for e in events), 'emitter scalar macro count')
    require(reported['real_component_primitive_bound'] == replayed['complex_real_primitives'], 'emitter primitive price')
    require(reported['paid_profile'] == word['local_profile'], 'emitter paid profile')
    require(reported['all_columns'] == replayed['logical_columns'], 'emitter column coverage')
    require(reported['private_centers_cleared'] is True and
            reported['private_coefficient_stream_cleared_after_each_macro'] is True, 'emitter private clearance flags')


def run_controls(bw, bp, cw, cp):
    """Controls run for every receipt, rather than trusted test-count metadata."""
    rejected = []
    def reject(name, thunk):
        try:
            thunk()
        except ValueError:
            rejected.append(name)
        else:
            raise ValueError('mutation accepted: '+name)
    for name, field in (('panel_sign', 3), ('panel_nondyadic', 4), ('panel_frame', 5)):
        word = copy.deepcopy(cw)
        word['compensation'][0][field] = {3: -word['compensation'][0][3], 4: 3, 5: 1}[field]
        if field == 3:
            reject(name, lambda: check_panel(bw, word))
        else:
            reject(name, lambda: check_boundary(bw, bp, word, cp))
    for name, role in (('missing_target_prepare', 'target'), ('missing_helper_restore', 'helper')):
        word = copy.deepcopy(cw)
        panel = word['compensation']
        if role == 'target':
            candidates = [i for i,op in enumerate(panel) if op[1] < 224 and op[2] < 224]
        else:
            candidates = [i for i,op in enumerate(panel) if op[1] >= 224 and op[2] >= 224]
        require(candidates, 'basis control fixture exists')
        panel.pop(candidates[0] if role == 'target' else candidates[-1])
        reject(name, lambda: check_panel(bw, word))
    for name, helper in (
            ('identity_pair_before_cold_wrapper', next(r for r in range(224,704) if cw['start'][r] == 0 and cw['final'][r] != 1)),
            ('identity_pair_at_nonzero_entrance', next(r for r in range(224,704) if cw['start'][r] != 0))):
        word = copy.deepcopy(cw)
        word['compensation'][:0] = [['add',helper,112,1,1,0], ['add',helper,112,-1,1,0]]
        check_panel(bw, word)  # prove the adversarial addition really is scalar-invisible
        reject(name, lambda: check_boundary(bw, bp, word, cp))
    for name, field, value in (('source_data_write',1,0), ('register_alias',2,cw['compensation'][0][1]),
                               ('boolean_register',1,True), ('zero_denominator',4,0)):
        word = copy.deepcopy(cw)
        word['compensation'][0][field] = value
        reject(name, lambda: check_boundary(bw,bp,word,cp))
    for name, mutate in (
            ('changed_precondition', lambda w: w['precondition'].pop()),
            ('changed_geometry', lambda w: w['frames'][0].append(1)),
            ('changed_paid_profile', lambda w: w['local_profile'].__setitem__('8',7)),
            ('changed_tail', lambda w: w['tail'].pop())):
        word = copy.deepcopy(cw)
        mutate(word)
        reject(name, lambda: check_boundary(bw,bp,word,cp))
    left = 1+len(cw['precondition'])
    for direction in BASE_PROGRAMS:
        programs = copy.deepcopy(cp)
        programs[direction][left][1][3] *= -1
        reject('literal_panel_binding_'+direction, lambda: check_boundary(bw,bp,cw,programs))
    programs = copy.deepcopy(cp)
    es = programs['forward']
    es.pop(next(i for i,e in enumerate(es) if e[0] == 'climb'))
    reject('removed_non_scalar_child', lambda: check_boundary(bw,bp,cw,programs))
    word = copy.deepcopy(bw)
    word['compensation'][0][3] *= -1
    reject('unbound_baseline', lambda: check_boundary(word,bp,cw,cp))
    return rejected


def verify(baseline_local, candidate_local):
    bw, bp = read_local(baseline_local)
    cw, cp = read_local(candidate_local)
    boundary = check_boundary(bw, bp, cw, cp)
    panel = check_panel(bw, cw)
    controls = run_controls(bw,bp,cw,cp)
    full = {}
    for label, word, programs, directory in (('baseline', bw, bp, baseline_local), ('candidate', cw, cp, candidate_local)):
        full[label] = {direction: replay(programs[direction], word, direction) for direction in BASE_PROGRAMS}
        checks = json.loads((Path(directory)/'LOCAL-CHECKS.json').read_text())
        native = json.loads((Path(directory)/'INDEPENDENT-LOCAL-REPLAY.json').read_text())
        for direction in BASE_PROGRAMS:
            # Check metadata only after recomputing the complete literal stream.
            check_emitter_receipt(programs[direction], word, full[label][direction], checks[direction])
            require(full[label][direction]['positive_prefix_l1_upper'] == native['local'][direction]['prefix_l1_upper'],
                    'independent primitive envelope equals unchanged native bound')
    return {'status': 'PASS_INDEPENDENT_PR1042_TYPED_COMPENSATION', 'baseline_word_sha256': digest(bw),
            'candidate_word_sha256': digest(cw), 'candidate_program_sha256': {d: digest(cp[d]) for d in BASE_PROGRAMS},
            'baseline_artifacts': {'CANONICAL-WORD.json.gz': digest(bw), 'LOCAL-PROGRAMS.json.gz': digest(bp)},
            'candidate_artifacts': {'CANONICAL-WORD.json.gz': digest(cw), 'LOCAL-PROGRAMS.json.gz': digest(cp)},
            'artifact_hash_convention': 'SHA256 of canonical JSON semantic payload, independent of gzip bytes',
            'columns_per_orientation': 713, 'orientations': 2, 'dirty_helpers_restored': 480,
            'private_inputs_erased': 9, 'controls_rejected': controls,
            'boundary': boundary, 'panel': panel, 'full_inherited_binary_horner': full,
            'scope': 'Finite typed substitution and inherited lowering. Native wrappers, physical owner hosting, global invoices, precision and assembly are separately checked by the unchanged production chain.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-local', required=True)
    parser.add_argument('--candidate-local', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    out = Path(args.out)
    require(not out.exists(), 'refuse to overwrite independent receipt')
    result = verify(args.baseline_local, args.candidate_local)
    with out.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write('\n')
    print(result['status'], flush=True)


if __name__ == '__main__':
    main()
