#!/usr/bin/env python3
"""Mutation controls against actual PR1042 baseline/candidate artifacts."""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('independent_pr1042', Path(__file__).with_name('verify.py'))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class LiteralControls(unittest.TestCase):
    def boundary(self, word=None, programs=None):
        return audit.check_boundary(self.bw, self.bp, word or self.cw, programs or self.cp)

    def changed_word(self, change):
        word = copy.deepcopy(self.cw)
        change(word)
        with self.assertRaises(ValueError):
            self.boundary(word=word)

    def changed_program(self, change):
        programs = copy.deepcopy(self.cp)
        change(programs)
        with self.assertRaises(ValueError):
            self.boundary(programs=programs)

    def test_actual_positive_boundary(self):
        self.assertEqual(self.boundary()['touched_helpers'], 240)

    def test_actual_both_orientation_panel_identities(self):
        result = audit.check_panel(self.bw, self.cw)
        self.assertEqual(result['forward']['arbitrary_columns'], 592)
        self.assertEqual(result['backward']['arbitrary_columns'], 592)

    def test_all_receipt_controls_execute(self):
        names = audit.run_controls(self.bw,self.bp,self.cw,self.cp)
        self.assertEqual(len(names),19)
        self.assertEqual(len(set(names)),19)

    def test_missing_target_prepare(self):
        word = copy.deepcopy(self.cw)
        panel = word['compensation']
        panel.pop(next(i for i, op in enumerate(panel) if op[1] < 224 and op[2] < 224))
        with self.assertRaises(ValueError):
            audit.check_panel(self.bw, word)

    def test_missing_helper_restore(self):
        word = copy.deepcopy(self.cw)
        panel = word['compensation']
        panel.pop(max(i for i, op in enumerate(panel) if op[1] >= 224 and op[2] >= 224))
        with self.assertRaises(ValueError):
            audit.check_panel(self.bw, word)

    def test_coefficient_sign(self):
        word = copy.deepcopy(self.cw)
        word['compensation'][0][3] *= -1
        with self.assertRaises(ValueError):
            audit.check_panel(self.bw, word)

    def test_target_only_identity_can_hide_forbidden_cold_wrapper_access(self):
        word = copy.deepcopy(self.cw)
        cold = next(r for r in range(224,704) if word['start'][r] == 0 and word['final'][r] != 1)
        # These inverse gates preserve EVERY scalar input, but are illegal before
        # the cold helper's pre-wrapper. An endpoint-only checker would miss it.
        word['compensation'][:0] = [['add',cold,112,1,1,0], ['add',cold,112,-1,1,0]]
        audit.check_panel(self.bw, word)
        with self.assertRaisesRegex(ValueError, 'unwrapped'):
            self.boundary(word=word)

    def test_identity_can_hide_nonzero_entrance_access(self):
        word = copy.deepcopy(self.cw)
        entering = next(r for r in range(224,704) if word['start'][r] != 0)
        word['compensation'][:0] = [['add',entering,112,1,1,0], ['add',entering,112,-1,1,0]]
        audit.check_panel(self.bw, word)
        with self.assertRaisesRegex(ValueError, 'starts at frame zero'):
            self.boundary(word=word)

    def test_wrong_panel_frame(self):
        self.changed_word(lambda w: w['compensation'][0].__setitem__(-1, 1))

    def test_alias_gate(self):
        self.changed_word(lambda w: w['compensation'][0].__setitem__(2, w['compensation'][0][1]))

    def test_source_data_write(self):
        self.changed_word(lambda w: w['compensation'][0].__setitem__(1, 0))

    def test_nondyadic(self):
        self.changed_word(lambda w: w['compensation'][0].__setitem__(4, 3))

    def test_bool_register(self):
        self.changed_word(lambda w: w['compensation'][0].__setitem__(1, True))

    def test_changed_target_precondition(self):
        self.changed_word(lambda w: w['precondition'][0].__setitem__(2, 7))

    def test_changed_paid_profile(self):
        self.changed_word(lambda w: w['local_profile'].__setitem__('8', 7))

    def test_changed_frame_geometry(self):
        self.changed_word(lambda w: w['frames'][0].append(1))

    def test_changed_start_inventory(self):
        self.changed_word(lambda w: w['start'].__setitem__(224, 1))

    def test_changed_tail(self):
        self.changed_word(lambda w: w['tail'].pop())

    def test_program_disagrees_with_canonical(self):
        left = 1+len(self.cw['precondition'])
        self.changed_program(lambda p: p['forward'][left][1].__setitem__(3, 7))

    def test_inverse_transpose_sign(self):
        left = 1+len(self.cw['precondition'])
        self.changed_program(lambda p: p['backward'][left][1].__setitem__(3, -p['backward'][left][1][3]))

    def test_removed_non_scalar_owner_event(self):
        def mutate(programs):
            es = programs['forward']
            es.pop(next(i for i,e in enumerate(es) if e[0] == 'climb'))
        self.changed_program(mutate)

    def test_changed_scalar_after_panel(self):
        def mutate(programs):
            es = programs['forward']
            left = es.index(['phase','A'])
            next(e for e in es[left:] if e[0]=='scalar')[1][1][1] = 0
        self.changed_program(mutate)

    def test_unbound_baseline(self):
        word = copy.deepcopy(self.bw)
        word['compensation'][0][3] *= -1
        with self.assertRaisesRegex(ValueError, 'selected PR1042 canonical'):
            audit.check_boundary(word,self.bp,self.cw,self.cp)

    def test_primitive_horner_literals(self):
        event = ['scalar',['add',['L',112],['L',224],-5,4],0]
        primitives = list(audit.primitive_stream([event]))
        self.assertEqual(len(primitives), 9)  # 3 + two doubles + two 1-bits + two halves
        self.assertEqual(primitives[0], ('clear',('W',0)))
        self.assertEqual(primitives[-1], ('clear',('W',0)))
        self.assertEqual(primitives[-2][-1], -1)

    def test_reciprocal_negative_scale(self):
        primitives = list(audit.primitive_stream([['scalar',['scale',['L',112],2,-1],0]]))
        self.assertEqual(primitives, [('scale',('L',112),2), ('scale',('L',112),-1)])

    def test_unchanged_native_auditor_rejects_scalar_invisible_wrapper_violation(self):
        script = Path(__file__).resolve().parents[3] / 'research/complex-sw4-frame8/vendor/pr635/research/complex-571-cold14-st2/code/hpe_audit_local.py'
        self.assertEqual(hashlib.sha256(script.read_bytes()).hexdigest(),
                         '6bd9a1e279c9c9e4f3767d9f82e537b559292906feb2ddab02f380fb6523a810')
        word, programs = copy.deepcopy(self.cw), copy.deepcopy(self.cp)
        cold = next(r for r in range(224,704) if word['start'][r] == 0 and word['final'][r] != 1)
        extra = [['add',cold,112,1,1,0], ['add',cold,112,-1,1,0]]
        word['compensation'][:0] = extra
        audit.check_panel(self.bw,word)
        left = 1+len(word['precondition'])
        for direction in audit.BASE_PROGRAMS:
            programs[direction][left:left] = [audit.panel_event(op,direction) for op in extra]
        with tempfile.TemporaryDirectory(prefix='pr1042-native-wrapper-control-') as folder:
            for name,data in (('CANONICAL-WORD.json.gz',word),('LOCAL-PROGRAMS.json.gz',programs)):
                (Path(folder)/name).write_bytes(gzip.compress(json.dumps(data).encode(),mtime=0))
            env = dict(os.environ)
            env.pop('PYTHONOPTIMIZE',None)
            # This historical auditor uses assertions. Its unchanged execution
            # must retain them even when this independent test runs with -O.
            result = subprocess.run([sys.executable,'-I','-B',str(script),folder],
                                    text=True,capture_output=True,env=env)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('common frame / wrapper order',result.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-local', required=True)
    parser.add_argument('--candidate-local', required=True)
    args, remaining = parser.parse_known_args()
    LiteralControls.bw, LiteralControls.bp = audit.read_local(args.baseline_local)
    LiteralControls.cw, LiteralControls.cp = audit.read_local(args.candidate_local)
    unittest.main(argv=[str(Path(__file__))]+remaining)


if __name__ == '__main__':
    main()
