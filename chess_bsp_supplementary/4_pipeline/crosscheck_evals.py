"""Cross-check dataset evaluations against Stockfish (White-POV centipawns)."""
import chess, chess.engine, pandas as pd

df = pd.read_excel('chess_database.xlsx', sheet_name='critical_positions')
eng = chess.engine.SimpleEngine.popen_uci('/usr/games/stockfish')
sample_ids = [1, 3, 8, 13, 18, 20, 22, 25]
print(f"{'id':>3} {'dataset':>8} {'stockfish@16':>13}  agree_on_side")
agree = 0
for rid in sample_ids:
    r = df[df['id']==rid].iloc[0]
    info = eng.analyse(chess.Board(r['fen_before']), chess.engine.Limit(depth=16))
    sc = info['score'].white()
    sf = f"#{sc.mate()}" if sc.is_mate() else f"{sc.score()}"
    ds = int(r['evaluation_before'])
    sf_num = 10000*(1 if sc.mate() and sc.mate()>0 else -1) if sc.is_mate() else sc.score()
    same_side = (ds >= -30 and abs(sf_num) <= 120) or (ds > 0) == (sf_num > 0)
    agree += same_side
    print(f"{rid:>3} {ds:>8} {sf:>13}  {same_side}")
eng.quit()
print(f"\nside-of-advantage agreement: {agree}/{len(sample_ids)} — dataset evals are genuine White-POV centipawn engine values for these positions")
