"""Tests on explicitly supplied, freshly regenerated PR1042 native inputs."""
import argparse
from collections import Counter
import copy
from fractions import Fraction as Q
import gzip
import itertools
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import compiler as C
import cost

BASELINE = None


def load(path):
    b = path.read_bytes()
    return json.loads(gzip.decompress(b) if path.suffix == ".gz" else b)


def panel_operator(panel, backward=False):
    """Independent direct Fraction matrix, every arbitrary target/helper input."""
    rows = {r:{r:Q(1)} for r in range(112,704)}
    for op in panel:
        tag,t,s,a,b,frame = op
        if tag != "add" or frame != 0 or t == s:
            raise ValueError("panel syntax")
        q = Q(a,b)
        if backward:
            t,s,q = s,t,-q
        for col,value in tuple(rows[s].items()):
            new = rows[t].get(col,Q(0))+q*value
            if new:
                rows[t][col] = new
            else:
                rows[t].pop(col,None)
    return rows


class CompilerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.word = load(BASELINE / "CANONICAL-WORD.json.gz")
        cls.programs = load(BASELINE / "LOCAL-PROGRAMS.json.gz")
        cls.checks = load(BASELINE / "LOCAL-CHECKS.json")
        cls.panel, cls.receipt = C.compile_compensation(cls.word)
        cls.before, cls.after, cls.candidates = {}, {}, {}
        for orientation,events in cls.programs.items():
            cls.candidates[orientation] = C.replace_events(events,cls.word,cls.panel,orientation)
            cls.before[orientation] = cost.recount_events(events)
            cls.after[orientation] = cost.recount_events(cls.candidates[orientation])

    def test_complete_forward_and_transpose_panel_maps(self):
        for backward in (False, True):
            self.assertEqual(panel_operator(self.panel, backward), panel_operator(self.word["compensation"], backward))

    def test_baseline_cost_matches_unchanged_native_recount(self):
        for orientation,row in self.before.items():
            reference = self.checks[orientation]
            for key in ("events","scalar_macros","real_component_primitive_bound"):
                self.assertEqual(row[key], reference[key])
            self.assertEqual(row["paid_profile"], {int(r):n for r,n in reference["paid_profile"].items()})

    def test_actual_improvements_and_prefix_budget(self):
        self.assertEqual(self.receipt["original"]["macros"],7208)
        self.assertEqual(self.receipt["replacement"]["macros"],2596)
        for orientation,real,bits in (("forward",143006,52),("backward",143054,70)):
            row = self.after[orientation]
            self.assertEqual(row["scalar_macros"],15081)
            self.assertEqual(row["real_component_primitive_bound"],real)
            self.assertEqual(row["prefix_bits_upper"],bits)
            self.assertLess(Q(row["prefix_l1_upper"]),2**192)
            self.assertEqual(row["paid_profile"],self.before[orientation]["paid_profile"])
        self.assertEqual(max(x["prefix_bits_upper"] for x in self.after.values())+37+144+144+4,399)

    def test_both_orientation_invoice_is_fully_charged(self):
        result = cost.invoice_delta(self.before,self.after)
        self.assertEqual(result["local_adapter_delta"],73792)
        self.assertEqual(result["local_primitive_bound_delta"],1913746577872)
        self.assertEqual(result["selected_real_primitive_delta"],8029440)
        self.assertEqual(result["global_pervertex_delta"],275579507213568)

    def test_every_preparation_and_restoration_is_paid(self):
        blocks = self.receipt["block_bills"]
        self.assertEqual(sum(b["macros"] for b in blocks.values()),len(self.panel))
        self.assertEqual(blocks["target_prepare"],blocks["target_restore"])
        self.assertEqual(blocks["helper_prepare"],blocks["helper_restore"])
        self.assertGreater(blocks["target_prepare"]["macros"],0)
        self.assertGreater(blocks["helper_prepare"]["macros"],0)
        self.assertEqual(sum(b["weighted_invoice"] for b in blocks.values()), self.receipt["replacement"]["weighted_invoice"])

    def test_boundary_and_all_non_scalar_events_unchanged(self):
        start = 1+len(self.word["precondition"])
        end = start+len(self.word["compensation"])
        for orientation,events in self.programs.items():
            candidate = self.candidates[orientation]
            self.assertEqual(candidate[:start],events[:start])
            self.assertEqual(candidate[start+len(self.panel):],events[end:])
            self.assertEqual([e for e in candidate if e[0] != "scalar"],[e for e in events if e[0] != "scalar"])

    def test_missing_basis_operations_break_arbitrary_dirty_map(self):
        expected = panel_operator(self.word["compensation"])
        blocks = self.receipt["block_bills"]
        tp,hp,body = (blocks[k]["macros"] for k in ("target_prepare","helper_prepare","residual"))
        positions = (0,tp,tp+hp+body,len(self.panel)-1)
        for pos in positions:
            mutant = self.panel[:pos]+self.panel[pos+1:]
            self.assertNotEqual(panel_operator(mutant),expected)

    def test_helper_pre_wrapper_and_frame_corruption_rejected(self):
        helper = self.receipt["helpers"][0]
        for field,value in (("start",1),("final",0)):
            word = copy.deepcopy(self.word)
            word[field][helper] = value
            with self.assertRaisesRegex(ValueError,"helper"):
                C.compile_compensation(word)
        word = copy.deepcopy(self.word)
        word["compensation"][0][-1] = 1
        with self.assertRaisesRegex(ValueError,"syntax/frame"):
            C.compile_compensation(word)

    def test_original_event_binding_rejected(self):
        events = copy.deepcopy(self.programs["forward"])
        pos = 1+len(self.word["precondition"])
        events[pos][1][3] *= -1
        with self.assertRaisesRegex(ValueError,"binding"):
            C.replace_events(events,self.word,self.panel,"forward")

    def test_zero_self_and_nondyadic_inputs_rejected(self):
        for q in (Q(0), Q(1,3)):
            with self.assertRaises(ValueError):
                cost.primitive_count(["add",["L",0],["L",1],q.numerator,q.denominator])
        with self.assertRaises(ValueError):
            cost.primitive_count(["scale",["L",0],3,1])

    def test_deterministic_rebuild_without_mutating_source(self):
        original = C.digest(self.word)
        panel,receipt = C.compile_compensation(self.word)
        self.assertEqual(panel,self.panel)
        self.assertEqual(receipt,self.receipt)
        self.assertEqual(C.digest(self.word),original)

    def test_literal_quarter_cost_matches_general_primitive_count(self):
        for a in range(-128,129):
            if a:
                q = Q(a,4)
                self.assertEqual(cost.quarter_add_real_cost(a),2*cost.primitive_count(["add",["L",0],["L",1],q.numerator,q.denominator]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline-local",type=Path,required=True)
    args,remaining = ap.parse_known_args()
    BASELINE = args.baseline_local.resolve()
    unittest.main(argv=[sys.argv[0],*remaining],verbosity=2)
