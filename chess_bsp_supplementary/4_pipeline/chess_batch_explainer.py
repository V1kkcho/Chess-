#!/usr/bin/env python3
"""
Batch chess explainer — automated LLM querying for the whole dataset.
=====================================================================

For each of the 25 critical positions this script:
  1. reads fen_before + evaluation_before from the xlsx;
  2. generates the piece-by-piece textual explanation with the **chessplainer**
     library (https://github.com/fspinna/chessplainer): SHAP values of each piece's
     contribution to White's win probability, computed with Stockfish;
  3. queries the LLM (Claude) with the agreed prompt — the Chess Concept Library +
     system prompt as standing context, and <POSITION>/<EVALUATION>/<PIECE_BY_PIECE>
     as the inputs;
  4. parses the CSV the model returns (beginner / intermediate / advanced).
Finally it writes results.csv with 4 columns: id + the three explanations.

The API key is read from the ANTHROPIC_API_KEY environment variable — it is never
stored in this file, so the script is safe to publish in the repository.

USAGE
-----
  export ANTHROPIC_API_KEY="sk-ant-..."          # never commit this!
  python chess_batch_explainer.py                # full 25-query run
  python chess_batch_explainer.py --row 7 --dry-run          # preview inputs, no API
  python chess_batch_explainer.py --pbp-csv piece_by_piece_texts.csv   # reuse SHAP values

Needs: python-chess, pandas, shap, scikit-learn, anthropic, a stockfish binary,
and the chessplainer package (pip install git+https://github.com/fspinna/chessplainer).
"""
import argparse, csv, io, os, sys
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = os.environ.get("CHESS_EXPLAINER_MODEL", "claude-sonnet-5")


def cp_to_eval_text(cp: int) -> str:
    """Dataset stores White-POV centipawns; the system prompt reads pawns, mate = spike."""
    if abs(cp) >= 9000:
        who = "White" if cp > 0 else "Black"
        return f"{cp:+d} (a very large spike \u2014 forced mate for {who})"
    return f"{cp/100:+.2f} (White's point of view, in pawns)"


def build_system_message(prompt_path: Path, concepts_path: Path) -> str:
    instructions = prompt_path.read_text(encoding="utf-8").strip()
    constants = concepts_path.read_text(encoding="utf-8").strip()
    return ("=== CHESS CONCEPT LIBRARY (constants and terms) ===\n"
            "Format: concept_name, description. Use these as your controlled vocabulary.\n\n"
            f"{constants}\n\n=== END OF CONCEPT LIBRARY ===\n\n{instructions}")


def build_user_message(fen: str, cp: int, pbp_text: str) -> str:
    return ("<POSITION>\n" + fen + "\n</POSITION>\n\n"
            "<EVALUATION>\n" + cp_to_eval_text(cp) + "\n</EVALUATION>\n\n"
            "<PIECE_BY_PIECE>\n"
            "SHAP contribution of each piece to White's win probability "
            "(+ favours White, - favours Black), computed with chessplainer:\n"
            + pbp_text + "\n</PIECE_BY_PIECE>")


def parse_model_csv(text: str) -> dict:
    """The model returns a small CSV (header + one row) with the three explanations."""
    text = text.strip().strip("`")
    if text.lower().startswith("csv"):
        text = text[3:].lstrip()
    row = next(csv.DictReader(io.StringIO(text)), None)
    if not row:
        raise ValueError("model returned no CSV data row")
    norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
    def pick(*names):
        for n in names:
            if n in norm and norm[n]:
                return norm[n]
        return ""
    return {"beginner":     pick("beginner", "beginner (under 1400)", "beginner_u1400"),
            "intermediate": pick("intermediate", "intermediate (1400\u20132200)",
                                 "intermediate (1400-2200)", "intermediate_1400_2200"),
            "advanced":     pick("advanced", "advanced (2200+)", "advanced_2200plus")}


def call_claude(system_message: str, user_message: str, model: str) -> str:
    import anthropic
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("error: ANTHROPIC_API_KEY is not set.")
    client = anthropic.Anthropic()
    resp = client.messages.create(model=model, max_tokens=1500,
                                  system=system_message,
                                  messages=[{"role": "user", "content": user_message}])
    return "".join(b.text for b in resp.content if b.type == "text").strip()


def main() -> None:
    ap = argparse.ArgumentParser(description="Query the LLM for all 25 positions; write results.csv (id + 3 explanations).")
    ap.add_argument("--xlsx", default=str(HERE / "chess_database.xlsx"))
    ap.add_argument("--sheet", default="critical_positions")
    ap.add_argument("--prompt", default=str(HERE / "chess_explainer_system_prompt.md"))
    ap.add_argument("--concepts", default=str(HERE / "chess_concepts_alphazero.csv"))
    ap.add_argument("--out", default=str(HERE / "results.csv"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--row", type=int, help="only process this id (testing)")
    ap.add_argument("--pbp-csv", help="reuse precomputed chessplainer values (id,piece_by_piece) instead of computing live")
    ap.add_argument("--dry-run", action="store_true", help="print assembled inputs; no API call")
    args = ap.parse_args()

    df = pd.read_excel(args.xlsx, sheet_name=args.sheet)
    if args.row is not None:
        df = df[df["id"] == args.row]

    # piece-by-piece source: precomputed CSV, or live chessplainer runs
    if args.pbp_csv:
        pbp_lookup = pd.read_csv(args.pbp_csv).set_index("id")["piece_by_piece"].to_dict()
        get_pbp = lambda rid, fen: pbp_lookup[rid]
        engine = None
    else:
        from chessplainer_pbp import make_engine, piece_by_piece
        engine = make_engine()
        get_pbp = lambda rid, fen: piece_by_piece(fen, engine)[0]

    sys_msg = None if args.dry_run else build_system_message(Path(args.prompt), Path(args.concepts))
    out_rows = []
    for _, r in df.iterrows():
        rid = int(r["id"]); fen = r["fen_before"]; cp = int(r["evaluation_before"])
        user_msg = build_user_message(fen, cp, get_pbp(rid, fen))
        if args.dry_run:
            print("=" * 70 + f"\nid {rid}\n" + "=" * 70 + "\n" + user_msg + "\n")
            continue
        print(f"[id {rid}] querying model...", file=sys.stderr)
        expl = parse_model_csv(call_claude(sys_msg, user_msg, args.model))
        out_rows.append([rid, expl["beginner"], expl["intermediate"], expl["advanced"]])

    if engine is not None:
        engine.engine.quit()
    if args.dry_run:
        return
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(["id", "explanation_beginner", "explanation_intermediate", "explanation_advanced"])
        w.writerows(out_rows)
    print(f"wrote {args.out} with {len(out_rows)} rows (4 columns)")


if __name__ == "__main__":
    main()
