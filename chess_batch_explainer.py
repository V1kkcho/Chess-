#!/usr/bin/env python3
"""
Batch chess explainer  —  the automated, whole-dataset version.
================================================================

`chess_explainer.py` handles ONE position: it wires a single position + evaluation +
piece-by-piece into the system prompt and asks Claude for the three rank-tailored
explanations. THIS script does the same for every row of the dataset, generating the
piece-by-piece automatically so it is correct for each game:

  for each critical position in the xlsx:
      1. read fen_before + evaluation_before
      2. compute the piece-by-piece placement values          (pst_eval.py)
      3. send position + evaluation + piece-by-piece to Claude, with the
         Chess Concept Library + system prompt as standing context
      4. parse the CSV the model returns (beginner / intermediate / advanced)
  write one combined CSV with every explanation + the evaluation.

USAGE
-----
  export ANTHROPIC_API_KEY="sk-ant-..."
  python chess_batch_explainer.py --out chess_explanations.csv
  # preview the exact model inputs for one row, no API call:
  python chess_batch_explainer.py --row 7 --dry-run

Needs: python-chess, pandas, anthropic, and pst_eval.py + the xlsx +
chess_explainer_system_prompt.md + chess_concepts_alphazero.csv in the same folder.
"""
import argparse, csv, io, os, sys
from pathlib import Path
import pandas as pd
import chess
from pst_eval import piece_by_piece_str

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = os.environ.get("CHESS_EXPLAINER_MODEL", "claude-sonnet-5")


def cp_to_eval_text(cp: int) -> str:
    """Dataset stores White-POV centipawns; the system prompt reads pawns, with mate spikes."""
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


def build_user_message(fen: str, cp: int) -> str:
    return ("<POSITION>\n" + fen + "\n</POSITION>\n\n"
            "<EVALUATION>\n" + cp_to_eval_text(cp) + "\n</EVALUATION>\n\n"
            "<PIECE_BY_PIECE>\n" + piece_by_piece_str(fen) + "\n</PIECE_BY_PIECE>")


def parse_model_csv(text: str) -> dict:
    """The model returns a small CSV (header + one row). Pull the three explanations."""
    text = text.strip().strip("`")
    if text.lower().startswith("csv"):
        text = text[3:].lstrip()
    reader = csv.DictReader(io.StringIO(text))
    row = next(reader, None)
    if not row:
        raise ValueError("model returned no CSV data row")
    norm = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
    def pick(*names):
        for n in names:
            if n in norm and norm[n]:
                return norm[n]
        return ""
    return {
        "beginner":     pick("beginner", "beginner (under 1400)", "beginner_u1400"),
        "intermediate": pick("intermediate", "intermediate (1400\u20132200)", "intermediate (1400-2200)", "intermediate_1400_2200"),
        "advanced":     pick("advanced", "advanced (2200+)", "advanced_2200plus"),
    }


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
    ap = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                 description="Batch-generate rank-tailored chess explanations into a CSV.")
    ap.add_argument("--xlsx", default=str(HERE / "chess_database.xlsx"))
    ap.add_argument("--sheet", default="critical_positions")
    ap.add_argument("--prompt", default=str(HERE / "chess_explainer_system_prompt.md"))
    ap.add_argument("--concepts", default=str(HERE / "chess_concepts_alphazero.csv"))
    ap.add_argument("--out", default=str(HERE / "chess_explanations.csv"))
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--row", type=int, help="only process this id (for testing)")
    ap.add_argument("--dry-run", action="store_true", help="print assembled inputs, don't call the API")
    args = ap.parse_args()

    df = pd.read_excel(args.xlsx, sheet_name=args.sheet)
    if args.row is not None:
        df = df[df["id"] == args.row]

    sys_msg = None if args.dry_run else build_system_message(Path(args.prompt), Path(args.concepts))

    out_rows = []
    for _, r in df.iterrows():
        fen = r["fen_before"]; cp = int(r["evaluation_before"])
        user_msg = build_user_message(fen, cp)
        if args.dry_run:
            print("=" * 70 + f"\nid {int(r['id'])}\n" + "=" * 70)
            print(user_msg + "\n")
            continue
        print(f"[id {int(r['id'])}] querying model...", file=sys.stderr)
        expl = parse_model_csv(call_claude(sys_msg, user_msg, args.model))
        out_rows.append({
            "id": int(r["id"]), "white": r["white"], "black": r["black"],
            "event": r["event"], "date": r["date"],
            "side_to_move": "White" if chess.Board(fen).turn else "Black",
            "critical_move": r["board move"], "fen": fen,
            "eval_before_cp": cp, "eval_after_cp": int(r["evaluaition_after"]),
            "eval_change_cp": int(r["the change"]),
            "piece_by_piece": piece_by_piece_str(fen),
            "beginner_u1400": expl["beginner"],
            "intermediate_1400_2200": expl["intermediate"],
            "advanced_2200plus": expl["advanced"],
        })

    if args.dry_run:
        return
    cols = list(out_rows[0].keys())
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader(); w.writerows(out_rows)
    print(f"wrote {args.out} with {len(out_rows)} rows")


if __name__ == "__main__":
    main()
