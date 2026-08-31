"""
Piece-by-piece generation via the chessplainer library (fspinna/chessplainer).

For a position, ChessExplainer computes SHAP values: each non-king piece's
contribution to White's win probability (masking pieces off the board and
re-evaluating with Stockfish). Positive = raises White's winning chances,
negative = raises Black's. This module wraps that into (text_line, dataframe).
"""
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import chess
from chessplainer.wrapper import EngineWrapper, ChessExplainer

STOCKFISH = "/usr/games/stockfish"

def make_engine(fit_depth=14, predict_depth=8):
    return EngineWrapper(path=STOCKFISH,
                         fit_limit_kwargs=dict(depth=fit_depth),
                         predict_limit_kwargs=dict(depth=predict_depth))

def ascii_label(board, square_name):
    sq = chess.parse_square(square_name)
    pc = board.piece_at(sq)
    letter = "" if pc.piece_type == chess.PAWN else pc.symbol().upper()
    return f"{letter}{square_name}"

def piece_by_piece(fen, engine, top=8, seed=0):
    """Returns (text_line, dataframe) of SHAP contributions to White's win probability."""
    np.random.seed(seed)                    # KernelExplainer sampling is stochastic
    board = chess.Board(fen)
    engine.fit([board])
    xp = ChessExplainer(board, engine)
    xp.explain()
    df = xp.df_.copy()
    df.columns = ["square", "piece", "feature_name", "shap_win", "shap_loss"]
    df["label"] = [ascii_label(board, s) for s in df["square"]]
    df["shap_win"] = df["shap_win"].astype(float).round(3)
    df = df.sort_values("shap_win", key=lambda s: s.abs(), ascending=False).reset_index(drop=True)
    text = "; ".join(f"{r.label} \u2192 {r.shap_win:+.3f}" for r in df.head(top).itertuples())
    return text, df[["label", "square", "piece", "shap_win", "shap_loss"]]
