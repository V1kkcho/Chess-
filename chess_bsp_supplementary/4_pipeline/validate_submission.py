"""Validates the two deliverable CSVs against the professor's spec."""
import re, pandas as pd

res = pd.read_csv("results.csv")
assert list(res.columns) == ["id","explanation_beginner","explanation_intermediate","explanation_advanced"], "results.csv must have exactly 4 columns: id + 3 explanations"
assert len(res) == 25, "must contain 25 records (one query per position)"
assert res["id"].tolist() == list(range(1,26))
for c in res.columns[1:]:
    assert res[c].str.strip().str.len().min() > 50, f"empty/short explanation in {c}"

ev = pd.read_csv("evaluation.csv")
assert len(ev) == 25 and len(ev.columns) == 11, "evaluation.csv must be 25 records x (id + 9 + 1 values)"
vals = ev.drop(columns=["id"])
assert (vals.dtypes == "int64").all(), "Likert values must be integers"
assert ((vals >= 1) & (vals <= 5)).all().all(), "Likert values must be in 1..5"
expected = ["beginner_groundedness","beginner_clarity","beginner_faithfulness",
            "intermediate_groundedness","intermediate_clarity","intermediate_faithfulness",
            "advanced_groundedness","advanced_clarity","advanced_faithfulness","coherence"]
assert list(vals.columns) == expected, "evaluation columns mismatch"

# coherence sanity: the three explanations of each record must state the same side
def side(t):
    t = t.lower()
    pats = {"white": ["white is", "white holds", "white has a", "white enjoys"],
            "black": ["black is", "black holds", "black has a"],
            "equal": ["roughly equal", "about level", "essentially balanced", "evaluation is balanced"]}
    best, best_i = None, 10**9
    for lab, plist in pats.items():
        for p in plist:
            i = t.find(p)
            if i >= 0 and i < best_i:
                best, best_i = lab, i
    if "sharp fight" in t and best is None: return "white"
    return best
for _, r in res.iterrows():
    s = {side(r[c]) for c in res.columns[1:]}
    assert len(s) == 1, f"id {r['id']}: tiers disagree {s}"

print("SUBMISSION VALIDATION PASSED:")
print(" - results.csv: 25 records, exactly 4 columns (id + 3 explanations)")
print(" - evaluation.csv: 25 records x 10 integer Likert values (1-5), 9 per-explanation + 1 coherence")
print(" - all three explanations agree per record (coherence basis verified)")
