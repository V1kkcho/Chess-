# Supplementary material — Multi-Level Chess Position Explainer
Bachelor Semester Project S2 (Academic Year 2025/26), University of Luxembourg

Maps directly onto the project TODOs:

1. **Piece-by-piece via the chessplainer library** (github.com/fspinna/chessplainer):
   `4_pipeline/chessplainer_pbp.py` wraps its EngineWrapper/ChessExplainer (SHAP values =
   each piece's contribution to White's win probability, computed with Stockfish);
   `4_pipeline/generate_piece_by_piece.py` runs it on all 25 positions. Outputs:
   `5_results/piece_by_piece_texts.csv` (textual lines) and
   `5_results/piece_by_piece_full.csv` (full per-piece attribution tables).
   Install: `pip install git+https://github.com/fspinna/chessplainer` + a Stockfish binary.

2. **Automated LLM querying (script included, no API keys inside):**
   `4_pipeline/chess_batch_explainer.py` loops the dataset, builds each query
   (Concept Library + system prompt from folders 1-2, plus <POSITION>, <EVALUATION>,
   <PIECE_BY_PIECE> from chessplainer) and calls the model. The key is read from the
   ANTHROPIC_API_KEY environment variable only. `--dry-run` previews the exact inputs.

3. **25 queries, one per position** — the dataset in `3_dataset/` has 25 critical
   positions; the script issues exactly one query per row.

4. **Results CSV, 4 columns:** `5_results/results.csv` = id, explanation_beginner,
   explanation_intermediate, explanation_advanced. 25 records.
   (`chess_explanations_extended.csv` adds metadata/evaluations/attributions for reference.)

5. **Evaluation:** `6_evaluation/evaluation.csv` — per record, 9 per-explanation scores
   (groundedness, clarity, faithfulness for each tier) + 1 global coherence score,
   Likert 1-5 integers. `evaluation_rubric.md` defines the anchors and method
   (annotation against machine-verified facts and the chessplainer attributions);
   `evaluation_notes.csv` lists the reason for every score below 5.

**Verification included** (`4_pipeline/`): `verify_dataset.py` replays every critical
move (fen_before + move reproduces fen_after, 25/25); `crosscheck_evals.py` compares
the dataset evaluations with fresh Stockfish 16 analysis (8/8 agreement on the side of
advantage); `validate_submission.py` checks both deliverable CSVs against this spec.
