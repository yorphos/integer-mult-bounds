"""Exact retained binary-Horner costs and positive-prefix invoice.

The charged primitive convention and compiler reserve are the selected
PR1042/PR1018/PR1005 lineage, retained without a coefficient discount.
Prepared with substantial OpenAI Codex assistance. Apache-2.0.
"""
from collections import Counter
from fractions import Fraction as Q
from functools import lru_cache

COMPILER = 64 * 74**3
ADAPTER_PRICE_PER_MACRO = 16 * COMPILER


def require(ok, message):
    if not ok:
        raise ValueError(message)


@lru_cache(None)
def quarter_add_real_cost(a):
    """Cost of target += (a/4)*source, including both work clears."""
    require(type(a) is int, "quarter-grid integer")
    if not a:
        return 0
    q = Q(a, 4)
    n, d = abs(q.numerator), q.denominator
    return 2 * (3 + n.bit_length()-1 + n.bit_count() + d.bit_length()-1)


@lru_cache(None)
def quarter_invoice_cost(a):
    return 0 if not a else ADAPTER_PRICE_PER_MACRO + quarter_add_real_cost(a)


def primitive_count(op):
    tag = op[0]
    if tag in ("clear", "copy"):
        return 1
    q = Q(op[3], op[4]) if tag == "add" else Q(op[2], op[3])
    a, d = abs(q.numerator), q.denominator
    require(a and d & (d-1) == 0, "nonzero dyadic coefficient")
    if tag == "scale":
        require(a & (a-1) == 0, "scale is a signed power of two")
        return abs(a.bit_length()-d.bit_length()) + int(q < 0)
    require(tag == "add", "scalar opcode")
    return 3 + a.bit_length()-1 + a.bit_count() + d.bit_length()-1


def recount_events(events, logical_registers=704, centres=8):
    """Literal macro cost and every positive Horner-work prefix.

    This recount does not replace the independent all-column/frame replay.
    It preserves the selected convention of clearing private work per macro.
    """
    env = {("L", i): Q(1) for i in range(logical_registers)}
    env.update({("C", i): Q(1) for i in range(centres)})
    peak = Q(1)
    macros = real = coefficient_work = 0
    paid = Counter()
    for event in events:
        tag = event[0]
        if tag == "climb":
            paid[event[5]] += 1
        elif tag == "center":
            paid[event[4]] += 1
        elif tag == "scalar":
            op = event[1]
            target = tuple(op[1])
            require(target in env, "known scalar target")
            macros += 1
            count = primitive_count(op)
            if op[0] == "clear":
                env[target] = Q(0)
            elif op[0] == "copy":
                source = tuple(op[2])
                require(source in env and source != target, "copy source/alias")
                env[target] = env[source]
            elif op[0] == "scale":
                env[target] *= abs(Q(op[2], op[3]))
            elif op[0] == "add":
                source = tuple(op[2])
                require(source in env and source != target, "add source/alias")
                q = Q(op[3], op[4])
                a, d = abs(q.numerator), q.denominator
                accumulator = 0
                for j, bit in enumerate(bin(a)[2:]):
                    if j:
                        accumulator *= 2
                        peak = max(peak, accumulator*env[source])
                    if bit == "1":
                        accumulator += 1
                        peak = max(peak, accumulator*env[source])
                value = Q(accumulator)
                for _ in range(d.bit_length()-1):
                    value /= 2
                    peak = max(peak, value*env[source])
                require(value == abs(q), "retained Horner coefficient")
                env[target] += abs(q)*env[source]
                coefficient_work += count
            real += 2*count
            peak = max(peak, env[target])
        else:
            require(tag in ("adapter", "phase", "residual_adapter"), "event opcode")
    cleared = all(env[("C", i)] == 0 for i in range(centres))
    require(cleared, "private centers erased")
    return {"events": len(events), "scalar_macros": macros,
            "real_component_primitive_bound": real,
            "coefficient_work_primitive_count": coefficient_work,
            "prefix_l1_upper": str(peak),
            "prefix_bits_upper": peak.numerator.bit_length()-peak.denominator.bit_length()+1,
            "paid_profile": dict(sorted(paid.items())), "private_work_erased": cleared}


def invoice_delta(before, after, calls=144):
    """Exact sensitivity of the unchanged selected finite invoice formula."""
    require(set(before) == set(after) == {"forward", "backward"}, "both orientations")
    dm = max(x["scalar_macros"] for x in before.values()) - max(x["scalar_macros"] for x in after.values())
    primitive_delta = max(x["real_component_primitive_bound"] for x in before.values()) - max(x["real_component_primitive_bound"] for x in after.values())
    require(calls == 144, "T16 calls")
    forward_calls, backward_calls = 5*16, 4*16
    selected_delta = sum(n*(before[o]["real_component_primitive_bound"]-after[o]["real_component_primitive_bound"])
                         for o,n in (("forward",forward_calls),("backward",backward_calls)))
    adapter_delta = 16*dm
    return {"compiler": COMPILER, "local_adapter_delta": adapter_delta,
            "local_primitive_bound_delta": adapter_delta*COMPILER+primitive_delta,
            "selected_real_primitive_delta": selected_delta,
            "global_pervertex_delta": calls*adapter_delta*COMPILER+selected_delta,
            "scope": "Exact delta in retained T16 formula with all other invoice terms fixed; fresh hosted invoice is required separately."}
