# Actual shared R480 compensation execution

This standard-library benchmark executes the original and replacement PR1042
R480 compensation panels using CPython arbitrary-precision integers. The selected
PR1094 packing retains all seven native semantic artifact identities and the
complete provider contract, so these are also its exact arithmetic inputs. It times
all actual panel work, including original binary-Horner coefficient work and
all target/helper preparation and restoration. Parsing, fixture generation,
copying the initial register lists and correctness validation are outside timing.
It does not measure the verifier, whole supplier or integer multiplication.

Each call uses 704 logical registers and one dirty coefficient-work register,
with 512 complex coordinates per register (1,024 interleaved integer components).
The selected panel has 7,208 macros and executes 41,164,800 real primitives;
the candidate has 2,596 macros and executes 12,615,680. Both implement the same
exact map in the tested orientation. The forward panel is `y += C h`; its
chronological inverse transpose is `h -= C^T y`. The latter intentionally
updates helpers; restoration of all helpers in the full native word is proved
separately by the full supplier checker.

## Protocol

Five matched fresh-process pairs per case, three input widths (128/1,024/4,096)
and both orientations give 60 processes. AB/BA order alternates, paired fixtures
use the same deterministic seed, and seeds vary between pairs. Each process
checks an exact untimed execution, warms up once and times one complete call.
Every timed output hash must match the original flat-C reference and its pair.
Wall and process CPU times, process IDs, interpreter, available CPU affinity and
whole-process `ru_maxrss` are retained in every raw JSON receipt.

B-bit signed magnitudes are shifted by exactly two guard bits, so initial stored
integers have B+2 bits. The independently checked current primitive streams prove
that two guard bits are sufficient and necessary. Every halving is exact, including
negative values. Certified worst-case intermediate widths are at most B+8 for all
four baseline/candidate orientations; this is a bound, not an observed peak.

This is a shared cloud host, not a claim of dedicated hardware or a portable
hardware speedup. Pairing/alternation and CPU times help interpret scheduling
variation. RSS is the entire process high-water including untimed oracle and
validation work, not isolated kernel memory. Report paired medians and observed
ranges without replacing them by operation-count ratios.

## Recorded results (2026-10-13)

CPython 3.12.14, one complete 512-coordinate panel per measurement, five matched
fresh-process pairs per case. All 30 pairs favored the replacement. The primary
statistic is the median of paired ratios, which can differ from the ratio of
the two separately reported medians. Known competing Arena, PDF and verifier
jobs were paused during the 539-second campaign; other host tenants were not observable.

| Input magnitude bits | Direction | Baseline median (s) | Candidate median (s) | Paired median speedup | Median process RSS change |
|---:|---|---:|---:|---:|---:|
| 128 | forward | 1.123 | 0.322 | 3.463x | +6.02% |
| 128 | backward | 1.150 | 0.335 | 3.478x | +2.29% |
| 1024 | forward | 1.767 | 0.534 | 3.403x | +9.44% |
| 1024 | backward | 1.811 | 0.535 | 3.383x | +3.80% |
| 4096 | forward | 4.820 | 1.393 | 3.446x | +10.89% |
| 4096 | backward | 5.392 | 1.468 | 3.704x | +4.19% |

Paired-median speedups span **3.383x–3.704x**; individual paired ratios span
**3.148x–3.812x**. Whole-process high-water memory is higher by **2.29%–10.89%**
across case medians. At 4,096 bits, forward median RSS is 585,120 → 648,864 KiB
and backward is 749,084 → 780,448 KiB. This includes oracle/validation memory.

`evidence/samples/` retains all 60 unedited raw JSON measurements.
`evidence/samples/RESULT.json` is the original paired result; `SUMMARY.json` also reports
CPU-time medians and memory. `FIXTURE-HASHES.json` independently regenerates
the 15 matched input fixtures. The independent audit binds every raw sample,
all distinct process IDs, source/input bytes, exact arithmetic and statistics.

These results concern the complete changed compensation kernel. The separate
full PR1094 strict supplier admission proves the **4.261381% complete conservative
invoice reduction**; it does not establish a whole-multiplication runtime speedup.

## Reproduce

From the repository root, using a fresh output:

```sh
python -I -B research/pr1042-compensation-runtime/run_pairs.py \
  --baseline research/pr1042-compensation-runtime/inputs/baseline-CANONICAL-WORD.json.gz \
  --candidate research/pr1042-compensation-runtime/inputs/candidate-CANONICAL-WORD.json.gz \
  --pairs 5 --bits 128 1024 4096 --out /tmp/pr1042-runtime-new
python -I -B research/pr1042-compensation-runtime/independent/verify_runtime.py \
  --root . \
  --baseline research/pr1042-compensation-runtime/inputs/baseline-CANONICAL-WORD.json.gz \
  --candidate research/pr1042-compensation-runtime/inputs/candidate-CANONICAL-WORD.json.gz \
  --results /tmp/pr1042-runtime-new --out /tmp/pr1042-runtime-audit-new.json
```

The independent consumer compares every executed primitive with a separately
implemented, hash-pinned lowerer, checks all 705 panel input columns, rejects
11 arithmetic/input mutations and recomputes every sample binding and summary.
The exact canonical semantic hashes are enforced before any timing. No package
installation, network access or C++ compiler is needed for this experiment.

See the companion `research/pr1042-typed-compensation` for full native/global
admission and complete retained invoice savings. The old R504 U8 measurements
are preserved separately and are not used here. Prepared with substantial
OpenAI assistance; Apache-2.0. No independent human review is implied.
