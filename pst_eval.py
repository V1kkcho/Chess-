"""
Automated piece-by-piece value generator.

For any position (FEN) it returns, for every piece on the board, a positional
placement value in pawns from White's point of view (+ favours White, - favours
Black), using the classic Michniewski "simplified evaluation" piece-square tables.
Material is deliberately NOT included, so the numbers are small positional
contributions (e.g. +0.35), matching the agreed piece-by-piece format
("Piece -> value"). The king uses a middlegame or endgame table depending on how
much material remains.

These values are a transparent, reproducible positional attribution computed from
the actual board; the position's overall evaluation comes from the dataset.
Self-test: `python pst_eval.py` runs orientation assertions.
"""
import chess

PAWN=[0,0,0,0,0,0,0,0, 50,50,50,50,50,50,50,50, 10,10,20,30,30,20,10,10,
 5,5,10,25,25,10,5,5, 0,0,0,20,20,0,0,0, 5,-5,-10,0,0,-10,-5,5,
 5,10,10,-20,-20,10,10,5, 0,0,0,0,0,0,0,0]
KNIGHT=[-50,-40,-30,-30,-30,-30,-40,-50, -40,-20,0,0,0,0,-20,-40, -30,0,10,15,15,10,0,-30,
 -30,5,15,20,20,15,5,-30, -30,0,15,20,20,15,0,-30, -30,5,10,15,15,10,5,-30,
 -40,-20,0,5,5,0,-20,-40, -50,-40,-30,-30,-30,-30,-40,-50]
BISHOP=[-20,-10,-10,-10,-10,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,10,10,5,0,-10,
 -10,5,5,10,10,5,5,-10, -10,0,10,10,10,10,0,-10, -10,10,10,10,10,10,10,-10,
 -10,5,0,0,0,0,5,-10, -20,-10,-10,-10,-10,-10,-10,-20]
ROOK=[0,0,0,0,0,0,0,0, 5,10,10,10,10,10,10,5, -5,0,0,0,0,0,0,-5,
 -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5, -5,0,0,0,0,0,0,-5,
 -5,0,0,0,0,0,0,-5, 0,0,0,5,5,0,0,0]
QUEEN=[-20,-10,-10,-5,-5,-10,-10,-20, -10,0,0,0,0,0,0,-10, -10,0,5,5,5,5,0,-10,
 -5,0,5,5,5,5,0,-5, 0,0,5,5,5,5,0,-5, -10,5,5,5,5,5,0,-10,
 -10,0,5,0,0,0,0,-10, -20,-10,-10,-5,-5,-10,-10,-20]
KING_MG=[-30,-40,-40,-50,-50,-40,-40,-30]*4 + [-20,-30,-30,-40,-40,-30,-30,-20,
 -10,-20,-20,-20,-20,-20,-20,-10, 20,20,0,0,0,0,20,20, 20,30,10,0,0,10,30,20]
KING_EG=[-50,-40,-30,-20,-20,-30,-40,-50, -30,-20,-10,0,0,-10,-20,-30, -30,-10,20,30,30,20,-10,-30,
 -30,-10,30,40,40,30,-10,-30, -30,-10,30,40,40,30,-10,-30, -30,-10,20,30,30,20,-10,-30,
 -30,-30,0,0,0,0,-30,-30, -50,-30,-30,-30,-30,-30,-30,-50]
TABLES={chess.PAWN:PAWN,chess.KNIGHT:KNIGHT,chess.BISHOP:BISHOP,chess.ROOK:ROOK,chess.QUEEN:QUEEN}

def _idx_white(sq): return (7 - chess.square_rank(sq)) * 8 + chess.square_file(sq)
def _idx_black(sq): return chess.square_rank(sq) * 8 + chess.square_file(sq)

def is_endgame(board):
    npm = sum(len(board.pieces(pt, c)) for pt in (chess.KNIGHT,chess.BISHOP,chess.ROOK,chess.QUEEN)
              for c in (True, False))
    return npm <= 6

def piece_values(fen):
    """List of (label, value_white_pov_pawns) for every piece, most significant first."""
    board = chess.Board(fen)
    king_tbl = KING_EG if is_endgame(board) else KING_MG
    out=[]
    for sq, pc in board.piece_map().items():
        tbl = king_tbl if pc.piece_type==chess.KING else TABLES[pc.piece_type]
        raw = tbl[_idx_white(sq)] if pc.color==chess.WHITE else -tbl[_idx_black(sq)]
        label = ('' if pc.piece_type==chess.PAWN else pc.symbol().upper()) + chess.square_name(sq)
        out.append((label, round(raw/100.0, 2)))
    return sorted(out, key=lambda x: -abs(x[1]))

def piece_by_piece_str(fen, top=8):
    """Compact 'Piece -> +0.xx' list of the most significant pieces (White-POV)."""
    vals = piece_values(fen)[:top]
    return "; ".join(f"{lab} \u2192 {v:+.2f}" for lab, v in vals)

if __name__ == "__main__":
    assert KNIGHT[_idx_white(chess.parse_square('e4'))] > 0, "central white knight must be +"
    assert KNIGHT[_idx_white(chess.parse_square('a1'))] < 0, "corner white knight must be -"
    assert PAWN[_idx_white(chess.parse_square('e7'))] == 50, "white pawn on 7th must be +50"
    assert KING_MG[_idx_white(chess.parse_square('g1'))] == 30, "castled king g1 (mg) must be +30"
    assert KING_EG[_idx_white(chess.parse_square('e4'))] == 40, "central king (eg) must be +40"
    b = chess.Board(None); b.set_piece_at(chess.parse_square('e5'), chess.Piece(chess.KNIGHT, chess.BLACK))
    assert piece_values(b.fen())[0][1] < 0, "black central knight must be negative White-POV"
    print("PST orientation checks passed")
    print("demo:", piece_by_piece_str("r2q1rk1/ppp2ppp/8/3p4/1b1P4/2N1PN2/PP3PPP/R2Q1RK1 w - - 0 1"))
