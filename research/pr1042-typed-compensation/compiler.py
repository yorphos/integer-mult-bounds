"""Typed restored target-forest/helper-pair compensation compiler.

Target forest: Oscar Fennell PR759, Sricharan Vagvala PR749, dd-hemant
PR816 and selected-X4 PR932. Restored helper basis: David Awad PR807 and
the later two-sided constructions. This compiler optimizes the selected
retained macro-adapter invoice, then emits its complete paid macro program.
No scalar lowering discount or new recursive child is assumed.
Prepared with substantial OpenAI Codex assistance. Apache-2.0.
"""
from collections import Counter, deque
from fractions import Fraction as Q
import hashlib
import json
from cost import (ADAPTER_PRICE_PER_MACRO, quarter_add_real_cost,
                  quarter_invoice_cost, require)


def canonical(x):
    return json.dumps(x, sort_keys=True, separators=(",", ":"))


def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def extract_matrix(word):
    require((word["v"], word["R"], word["h"]) == (112,480,9), "selected PR1042 provider shape")
    require(word["frames"][0] == [] and len(word["frames"][1]) == 9, "bottom/full frame identifiers")
    require(all(word["start"][r] == 0 for r in range(112,224)), "arbitrary target bottom entries")
    rows = [{} for _ in range(112)]
    for op in word["compensation"]:
        require(len(op) == 6 and op[0] == "add" and op[-1] == 0, "original compensation syntax/frame")
        _,target,helper,a,b,_ = op
        require(all(type(x) is int for x in (target,helper,a,b)), "integer canonical fields")
        require(112 <= target < 224 and 224 <= helper < 704, "compensation roles")
        require(word["start"][helper] == 0 and word["final"][helper] == 1,
                "frame-zero helper is bottom-start and FULL-ended, without pre-wrapper")
        q = Q(a,b)*4
        require(q.denominator == 1 and q, "nonzero quarter-grid input")
        require(helper not in rows[target-112], "duplicate matrix entry")
        rows[target-112][helper] = q.numerator
    helpers = sorted(set().union(*(set(row) for row in rows)))
    require(len(word["compensation"]) == 7208 and len(helpers) == 240, "selected panel inventory")
    return rows, helpers


def row_cost(row):
    return sum(quarter_invoice_cost(q) for q in row.values())


def subtract(a,b,sign):
    return {h:q for h in a.keys()|b.keys() if (q := a.get(h,0)-sign*b.get(h,0))}


def target_forest(rows):
    """Exact MST for the signed single-parent target-forest invoice class."""
    n = len(rows)
    edges = [(row_cost(row), -1, j, 0) for j,row in enumerate(rows)]
    twice_basis = 2*quarter_invoice_cost(4)
    for i in range(n):
        for j in range(i+1,n):
            for sign in (-1,1):
                edges.append((row_cost(subtract(rows[j], rows[i],sign))+twice_basis,i,j,sign))
    edges.sort()
    roots = list(range(n+1))
    def find(i):
        i += 1
        while roots[i] != i:
            roots[i] = roots[roots[i]]
            i = roots[i]
        return i
    chosen = []
    for weight,i,j,sign in edges:
        a,b = find(i),find(j)
        if a == b:
            continue
        roots[a] = b
        chosen.append((weight,i,j,sign))
        if len(chosen) == n:
            break
    require(len(chosen) == n, "complete rooted spanning tree")
    adjacency = {i:[] for i in range(-1,n)}
    for weight,i,j,sign in chosen:
        adjacency[i].append((j,sign)); adjacency[j].append((i,sign))
    parent, depth = {}, {-1:0}
    todo = deque([-1])
    while todo:
        i = todo.popleft()
        for j,sign in sorted(adjacency[i]):
            if j in depth:
                continue
            parent[j] = (i,sign)
            depth[j] = depth[i]+1
            todo.append(j)
    residual = [dict(row) if parent[j][0] == -1 else subtract(row,rows[parent[j][0]],parent[j][1])
                for j,row in enumerate(rows)]
    prep = [["add",112+j,112+parent[j][0],-parent[j][1],1,0]
            for j in sorted(range(n),key=lambda j:(-depth[j],j)) if parent[j][0] != -1]
    cost = sum(row_cost(row) for row in residual)+len(prep)*twice_basis
    require(cost == sum(x[0] for x in chosen), "MST price and emitted forest agree")
    return residual, prep, {"edge_inventory":len(edges),"edge_inventory_sha256":digest(edges),
                            "chosen_edges":[list(x) for x in chosen], "weighted_cost":cost,
                            "scope":"Exact MST optimum within signed-unit single-parent target forests, before helper-pair pass."}


def helper_pairs(residual):
    helpers = sorted(set().union(*(set(row) for row in residual)))
    columns = {h:{j:row[h] for j,row in enumerate(residual) if h in row} for h in helpers}
    costs = {h:row_cost(column) for h,column in columns.items()}
    candidates = []
    for dst in helpers:
        for src in helpers:
            if dst == src:
                continue
            for sign in (-1,1):
                gain = costs[src]-row_cost(subtract(columns[src],columns[dst],sign))-2*quarter_invoice_cost(4)
                candidates.append((gain,dst,src,sign))
    candidates.sort(key=lambda p:(-p[0],p[1:]))
    chosen, used = [], set()
    for gain,dst,src,sign in candidates:
        if gain > 0 and dst not in used and src not in used:
            chosen.append((gain,dst,src,sign)); used.update((dst,src))
    prep = []
    for gain,dst,src,sign in chosen:
        prep.append(["add",dst,src,sign,1,0])
        for row in residual:
            q = row.get(src,0)-sign*row.get(dst,0)
            if q:
                row[src] = q
            else:
                row.pop(src,None)
    return prep, {"candidate_inventory":len(candidates),"candidate_inventory_sha256":digest(candidates),
                  "chosen_pairs":[list(x) for x in chosen], "claimed_weighted_gain":sum(x[0] for x in chosen),
                  "scope":"Deterministic positive-gain disjoint greedy pairs; no matching or joint optimum claim."}


def inverse(ops):
    return [op[:3]+[-op[3]]+op[4:] for op in reversed(ops)]


def compile_compensation(word):
    rows, helpers = extract_matrix(word)
    residual, target_prep, forest = target_forest(rows)
    helper_prep, pairs = helper_pairs(residual)
    body = []
    for j,row in enumerate(residual):
        for h,a in sorted(row.items()):
            q = Q(a,4)
            body.append(["add",112+j,h,q.numerator,q.denominator,0])
    blocks = {"target_prepare":target_prep,"helper_prepare":helper_prep,"residual":body,
              "helper_restore":inverse(helper_prep),"target_restore":inverse(target_prep)}
    panel = sum(blocks.values(),[])
    for op in panel:
        for register in op[1:3]:
            require(word["start"][register] == 0, "replacement incident role starts at frame zero")
            if register >= 224:
                require(word["final"][register] == 1, "replacement helper needs no cold-end pre-wrapper")
    def bill(ops):
        values = [int(Q(op[3],op[4])*4) for op in ops]
        return {"macros":len(ops),"real_primitives":sum(quarter_add_real_cost(a) for a in values),
                "weighted_invoice":sum(quarter_invoice_cost(a) for a in values)}
    after, before = bill(panel), bill(word["compensation"])
    require(after["weighted_invoice"] == forest["weighted_cost"]-pairs["claimed_weighted_gain"], "complete prepared/restored invoice")
    require(after["macros"] < before["macros"] and after["real_primitives"] < before["real_primitives"], "strict actual panel improvement")
    receipt = {"status":"PASS_TYPED_RESTORED_COMPENSATION_COMPILATION", "canonical_word_sha256":digest(word),
               "original_panel_sha256":digest(word["compensation"]),"replacement_panel_sha256":digest(panel),
               "original":before,"replacement":after,"block_bills":{k:bill(v) for k,v in blocks.items()},
               "helpers":helpers,"target_forest":forest,"helper_pairs":pairs,
               "adapter_price_per_macro":ADAPTER_PRICE_PER_MACRO,
               "contract":"Arbitrary target/helper input: y+=C*h, helpers restored. Every emitted operation is paid at frame zero before entry_adapters; all other events unchanged."}
    return panel, receipt


def event(op,direction):
    require(direction in ("forward","backward"), "orientation")
    _,t,s,a,b,f = op
    require(f == 0, "compensation frame zero")
    if direction == "backward":
        t,s,a = s,t,-a
    return ["scalar",["add",["L",t],["L",s],a,b],0]


def replace_events(events,word,panel,direction):
    start = 1+len(word["precondition"])
    end = start+len(word["compensation"])
    require(events[0] == ["phase","zero_frame_precondition"] and events[end] == ["phase","entry_adapters"], "typed compensation phase boundaries")
    require(events[start:end] == [event(op,direction) for op in word["compensation"]], "original panel/event binding")
    candidate = events[:start]+[event(op,direction) for op in panel]+events[end:]
    require([e for e in events if e[0] != "scalar"] == [e for e in candidate if e[0] != "scalar"], "all non-scalar events preserved")
    return candidate
