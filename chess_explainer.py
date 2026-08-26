#!/usr/bin/env python3
"""
Multi-Level Chess Position Explainer
====================================

Wires three runtime inputs -- a board position, an engine evaluation, and a
piece-by-piece description -- into the system prompt and the Chess Concept Library
("the constants"), then asks Claude to write three explanations of the position,
one each for a beginner, an intermediate, and an advanced player.

USAGE
-----
Set your key once:                export ANTHROPIC_API_KEY="sk-ant-..."
Run the built-in demo:            python chess_explainer.py --demo
Run the forced-mate demo:         python chess_explainer.py --demo-mate
Explain your own position:        python chess_explainer.py \
                                      --position "<FEN or board>" \
                                      --evaluation "+3.1" \
                                      --pieces "path/to/piece_by_piece.txt"
Inspect the assembled prompt       python chess_explainer.py --demo --dry-run
  without calling the API:

Any of --position/--evaluation/--pieces may be either a literal string or a path
to a text file containing the value; the script auto-detects existing files.

FILES EXPECTED ALONGSIDE THIS SCRIPT (paths overridable via flags)
------------------------------------------------------------------
  chess_explainer_system_prompt.md   the instructions (this repo)
  chess_concepts_alphazero.csv       the constants: concept_name,description
"""

import argparse
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PROMPT = HERE / "chess_explainer_system_prompt.md"
DEFAULT_CONCEPTS = HERE / "chess_concepts_alphazero.csv"
DEFAULT_MODEL = os.environ.get("CHESS_EXPLAINER_MODEL", "claude-sonnet-5")

# ---------------------------------------------------------------------------
# Built-in demonstration inputs (illustrative; evaluations are rounded, not
# claimed to be engine-exact). Both positions are legal.
# ---------------------------------------------------------------------------

DEMO_NORMAL = {
    "position": (
        "FEN: r2q1rk1/ppp2ppp/8/3p4/1b1P4/2N1PN2/PP3PPP/R2Q1RK1 w - - 0 1\n"
        "(White: Kg1, Qd1, Ra1, Rf1, Nc3, Nf3, pawns a2 b2 d4 e3 f2 g2 h2. "
        "Black: Kg8, Qd8, Ra8, Rf8, Bb4, pawns a7 b7 c7 d5 f7 g7 h7.)"
    ),
    "evaluation": "+3.0 (from White's point of view, in pawns)",
    "pieces": (
        "White is a full minor piece ahead: two knights against Black's single "
        "bishop, with pawns level (seven each). The white king is safely castled on "
        "g1 behind an intact f2-g2-h2 shelter; both white rooks and the queen sit on "
        "their starting files, ready to be activated. Black's bishop on b4 pins "
        "nothing important and its d5-pawn is isolated on a half-open file. Black has "
        "no immediate threat and no compensation for the missing piece."
    ),
}

DEMO_MATE = {
    "position": (
        "FEN: 5r1k/6pp/7N/8/8/1Q6/8/6K1 w - - 0 1\n"
        "(White: Kg1, Qb3, Nh6. Black: Kh8, Rf8, pawns g7 h7.)"
    ),
    "evaluation": "M2 (forced mate for White in 2)",
    "pieces": (
        "White's knight on h6 covers f7 and g8; the queen on b3 rakes the long light "
        "diagonal straight to g8. Black's king on h8 is boxed in by its own rook on "
        "f8 and the pawns on g7 and h7 -- it has no flight squares. This is the "
        "classic smothered-mate picture: Qg8+ forces the rook to capture on g8, after "
        "which Nf7 is mate. Black has no way to prevent the pattern."
    ),
}


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def _read(path: Path, what: str) -> str:
    if not path.exists():
        sys.exit(f"error: {what} not found at {path}")
    return path.read_text(encoding="utf-8")


def _resolve_value(value: str) -> str:
    """A CLI value is used literally, unless it names an existing file."""
    if value is None:
        return None
    p = Path(value)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8").strip()
    return value


def build_system_message(prompt_path: Path, concepts_path: Path) -> str:
    """Constants first, then the instructions -- the model's full standing context."""
    instructions = _read(prompt_path, "system prompt")
    constants = _read(concepts_path, "concept library (constants)")
    return (
        "=== CHESS CONCEPT LIBRARY (constants and terms) ===\n"
        "Format: concept_name, description. Use these as your controlled vocabulary.\n\n"
        f"{constants.strip()}\n\n"
        "=== END OF CONCEPT LIBRARY ===\n\n"
        f"{instructions.strip()}"
    )


def build_user_message(position: str, evaluation: str, pieces: str) -> str:
    for name, val in (("position", position), ("evaluation", evaluation), ("pieces", pieces)):
        if not val or not val.strip():
            sys.exit(f"error: the '{name}' input is empty")
    return (
        "<POSITION>\n" + position.strip() + "\n</POSITION>\n\n"
        "<EVALUATION>\n" + evaluation.strip() + "\n</EVALUATION>\n\n"
        "<PIECE_BY_PIECE>\n" + pieces.strip() + "\n</PIECE_BY_PIECE>"
    )


# ---------------------------------------------------------------------------
# Model call
# ---------------------------------------------------------------------------

def call_claude(system_message: str, user_message: str, model: str) -> str:
    try:
        import anthropic
    except ImportError:
        sys.exit("error: the 'anthropic' package is not installed. Run: pip install anthropic")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("error: ANTHROPIC_API_KEY is not set in the environment.")

    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=1200,
        system=system_message,
        messages=[{"role": "user", "content": user_message}],
    )
    return "".join(block.text for block in resp.content if block.type == "text").strip()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description="Generate three rank-tailored explanations of a chess position.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--position", help="FEN/board string, or a path to a text file.")
    ap.add_argument("--evaluation", help="Engine score string, or a path to a text file.")
    ap.add_argument("--pieces", help="Piece-by-piece text, or a path to a text file.")
    ap.add_argument("--demo", action="store_true", help="Use the built-in 'up a piece' example.")
    ap.add_argument("--demo-mate", action="store_true", help="Use the built-in forced-mate example.")
    ap.add_argument("--prompt", default=str(DEFAULT_PROMPT), help="Path to the system prompt .md.")
    ap.add_argument("--concepts", default=str(DEFAULT_CONCEPTS), help="Path to the concept library .csv.")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Model name (default: {DEFAULT_MODEL}).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print the assembled system+user messages and exit (no API call).")
    args = ap.parse_args()

    if args.demo or args.demo_mate:
        src = DEMO_MATE if args.demo_mate else DEMO_NORMAL
        position, evaluation, pieces = src["position"], src["evaluation"], src["pieces"]
    else:
        if not (args.position and args.evaluation and args.pieces):
            ap.error("provide --position, --evaluation and --pieces (or use --demo / --demo-mate).")
        position = _resolve_value(args.position)
        evaluation = _resolve_value(args.evaluation)
        pieces = _resolve_value(args.pieces)

    system_message = build_system_message(Path(args.prompt), Path(args.concepts))
    user_message = build_user_message(position, evaluation, pieces)

    if args.dry_run:
        print("================= SYSTEM MESSAGE =================\n")
        print(system_message)
        print("\n\n================== USER MESSAGE ==================\n")
        print(user_message)
        return

    print(call_claude(system_message, user_message, args.model))


if __name__ == "__main__":
    main()
