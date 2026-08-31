"""Runs chessplainer on all 25 positions; writes the textual piece-by-piece lines
and the full per-piece attribution tables."""
import time, pandas as pd
from chessplainer_pbp import make_engine, piece_by_piece

df = pd.read_excel("chess_database.xlsx", sheet_name="critical_positions")
eng = make_engine()
texts, tables = [], []
t0 = time.time()
for _, r in df.iterrows():
    rid = int(r["id"])
    text, tab = piece_by_piece(r["fen_before"], eng)
    tab.insert(0, "id", rid)
    texts.append({"id": rid, "piece_by_piece": text})
    tables.append(tab)
    print(f"id {rid:>2} done ({time.time()-t0:5.1f}s)  {text[:80]}...")
eng.engine.quit()
pd.DataFrame(texts).to_csv("piece_by_piece_texts.csv", index=False)
pd.concat(tables).to_csv("piece_by_piece_full.csv", index=False)
print("wrote piece_by_piece_texts.csv and piece_by_piece_full.csv")
