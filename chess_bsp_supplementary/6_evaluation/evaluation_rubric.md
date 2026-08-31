# Evaluation rubric — Likert 1-5 (integers only)

Each of the 25 records receives **10 values**: groundedness, clarity and faithfulness
for each of the three explanations (beginner / intermediate / advanced) = 9 values,
plus **one global coherence** value that considers all three explanations at once.

## Dimensions

**Groundedness** — the explanation reports things that are correct, i.e. true in the
starting position (fen_before) and consistent with its evaluation.
5 = every claim verified true; 4 = correct with one imprecise/over-strong phrase;
3 = one minor factual slip; 2 = a clear factual error; 1 = mostly wrong.

**Clarity** — readable and pitched correctly for the tier.
5 = immediately clear; 4 = clear but dense/long sentences; 3 = requires effort;
2 = confusing in places; 1 = hard to understand.

**Faithfulness** — what is claimed as the explanation is the *actual* explanation:
the pieces/factors the text credits match the chessplainer SHAP attribution (which
pieces actually carry the position) and the engine evaluation.
5 = headlines the attribution's top contributors; 4 = mostly aligned, one top factor
omitted or a secondary factor foregrounded; 3 = partially aligned; 2 = credits the
wrong factors; 1 = story contradicts the attribution.

**Coherence** (one score per record) — the three explanations agree with each other
on who is better, by how much, and why.
5 = full agreement; 4 = same verdict, minor emphasis differences; 3 = same verdict,
inconsistent reasons; 2 = verdicts differ in degree; 1 = contradictory verdicts.

## Method

Scores were assigned by manual annotation against machine-verified evidence rather
than impression: groundedness against the board (python-chess) and the dataset
evaluations (cross-checked with Stockfish 16); faithfulness against the chessplainer
SHAP piece attributions computed for every position; coherence additionally verified
programmatically (all three tiers of every record state the same side and magnitude).
Every score below 5 is listed with its reason in `evaluation_notes.csv`.
