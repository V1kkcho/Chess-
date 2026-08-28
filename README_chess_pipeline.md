# Chess explanations — batch pipeline

This turns the 25 critical positions in `chess_database.xlsx` into one CSV with, for
each position, the engine evaluation and **three explanations** tailored to Beginner
(<1400), Intermediate (1400–2200) and Advanced (2200+) players.

## The deliverable

**`chess_explanations.csv`** — 25 rows, one per critical position. Columns:

| column | meaning |
|---|---|
| `id`, `white`, `black`, `event`, `date` | game identification |
| `side_to_move`, `critical_move`, `fen` | the position (FEN = `fen_before`) and the move played |
| `eval_before_cp` | the position's evaluation (dataset value, White-POV centipawns) |
| `eval_verbal` | plain-language reading of that number |
| `eval_after_cp`, `eval_change_cp` | evaluation after the critical move, and the swing |
| `piece_by_piece` | automatically-computed per-piece placement values |
| `beginner_u1400`, `intermediate_1400_2200`, `advanced_2200plus` | the three explanations |

## How it was made (grounding & consistency)

Every explanation was written against **machine-verified facts**, not guesswork:

- **Position ↔ evaluation consistency.** `verify_dataset.py` replayed
  `fen_before` + `board move` with python-chess for all 25 rows and it reproduces
  `fen_after` exactly; `crosscheck_evals.py` compared the dataset's evaluations with
  fresh Stockfish 16 analysis (8/8 agreement on the side of advantage; e.g. row 1:
  dataset 129 vs SF 126, row 13: −96 vs −117). Each explanation's verdict matches the
  sign and size of `eval_before_cp` — checked automatically in `validate_csv.py`.
- **Correct facts per game.** Material balance, side to move, captures/checks and mate
  spikes were extracted from the actual boards, so no position is misread.
- **Automated piece-by-piece.** `pst_eval.py` computes each piece's positional
  placement value (White-POV, in pawns) from the real board, so the piece-by-piece is
  correct and specific to every position; the validator confirms every listed piece
  actually stands on its named square.
- **Forced mates.** No `fen_before` is itself a mate — the two mate spikes (rows 7 and
  13) appear only *after* the critical move — so each position is described by its true
  `eval_before`. Row 13 ("Black better but sharp") even warns the side to move off the
  very capture (gxf3) that led to the forced mate.
- **Quality gates.** `validate_csv.py` enforces 7 checks: completeness, the 3–4 sentence
  cap, per-tier evaluation/side consistency, cross-tier agreement, FEN validity,
  piece-by-piece square occupancy, and strict CSV parseability. All pass.

## Files

- **`chess_explanations.csv`** — the output described above.
- **`build_final_csv.py`** — rebuilds `chess_explanations.csv` exactly (explanations
  embedded). Run: `python build_final_csv.py`. Needs `pst_eval.py` + the xlsx.
- **`pst_eval.py`** — the automated piece-by-piece module (self-testing: `python pst_eval.py`).
- **`verify_dataset.py`**, **`crosscheck_evals.py`**, **`validate_csv.py`** — the
  verification & validation suite used to guarantee consistency.
- **`chess_batch_explainer.py`** — regenerates the explanations by calling Claude. It is
  the whole-dataset version of `chess_explainer.py`: that script explains ONE position;
  this loops over every row, builds the piece-by-piece automatically, sends
  position + evaluation + piece-by-piece to the model with the Concept Library + system
  prompt, and writes the combined CSV.

## Re-running with the live model

```
export ANTHROPIC_API_KEY="sk-ant-..."
# put together in one folder: chess_batch_explainer.py, pst_eval.py,
#   chess_database.xlsx, chess_explainer_system_prompt.md, chess_concepts_alphazero.csv
python chess_batch_explainer.py --out chess_explanations.csv
# preview the exact model inputs for one row (no API call):
python chess_batch_explainer.py --row 7 --dry-run
```
