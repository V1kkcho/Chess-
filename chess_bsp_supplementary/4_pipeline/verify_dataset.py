"""Full-dataset verification: FEN validity, move replay consistency, and fact extraction."""
import chess, pandas as pd

MAT = {chess.PAWN:1,chess.KNIGHT:3,chess.BISHOP:3,chess.ROOK:5,chess.QUEEN:9,chess.KING:0}
MATE_THRESH = 9000   # |eval| above this = mate spike (non-mate values in data max at 1052)

def verbal(cp):
    if abs(cp) >= MATE_THRESH:
        return ("White" if cp>0 else "Black")+" has a forced mate"
    a=abs(cp)/100.0; side = "White" if cp>0 else "Black"
    if a < 0.3: return "roughly equal"
    if a < 0.9: return f"slight edge for {side}"
    if a < 1.5: return f"clear advantage for {side}"
    if a < 3.0: return f"large advantage for {side}"
    return f"{side} is winning"

def material(b):
    w=sum(MAT[p.piece_type] for p in b.piece_map().values() if p.color)
    bl=sum(MAT[p.piece_type] for p in b.piece_map().values() if not p.color)
    return w, bl

def hanging(b, color):
    out=[]
    for sq,pc in b.piece_map().items():
        if pc.color!=color or pc.piece_type==chess.KING: continue
        if b.is_attacked_by(not color, sq) and not b.is_attacked_by(color, sq):
            out.append(chess.square_name(sq))
    return out

def run():
    df = pd.read_excel('chess_database.xlsx', sheet_name='critical_positions')
    assert len(df)==25, f"expected 25 rows, got {len(df)}"
    problems=[]
    print(f"{'id':>3} {'stm':>5} {'mat W-B':>8} {'eval_b':>7} {'eval_a':>7}  {'move':>6} {'cap':>3} {'chk':>3} {'mate_spike':>10} {'replay_ok':>9}")
    for _, r in df.iterrows():
        rid=int(r['id'])
        b = chess.Board(r['fen_before'])            # raises if invalid FEN
        assert b.is_valid(), f"id {rid}: illegal position"
        w,bl = material(b)
        stm = 'W' if b.turn else 'B'
        try:
            mv = b.parse_san(str(r['board move']))
        except Exception:
            mv=None; problems.append((rid,'move unparseable'))
        cap=chk=False; ok=False
        if mv is not None:
            cap=b.is_capture(mv)
            b2=b.copy(); b2.push(mv); chk=b2.is_check()
            exp=chess.Board(r['fen_after'])
            ok = (b2.board_fen()==exp.board_fen() and b2.turn==exp.turn)
            if not ok: problems.append((rid,'fen_after mismatch'))
        eb, ea = int(r['evaluation_before']), int(r['evaluaition_after'])
        spike = 'yes('+('W' if ea>0 else 'B')+')' if abs(ea)>=MATE_THRESH else '-'
        print(f"{rid:>3} {stm:>5} {w:>3}-{bl:<4} {eb:>7} {ea:>7}  {str(r['board move']):>6} {str(cap)[0]:>3} {str(chk)[0]:>3} {spike:>10} {str(ok):>9}")
    # eval_before must never itself be a mate spike (relevant for which positions get mate wording)
    assert (df['evaluation_before'].abs() < MATE_THRESH).all(), "an eval_before is a mate spike"
    print("\nproblems:", problems if problems else "NONE — all 25 rows verified: valid FENs, legal moves, fen_before+move==fen_after")
    return df

if __name__=='__main__':
    run()
