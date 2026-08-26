# Worked Examples — Multi-Level Chess Position Explainer

These are sample outputs illustrating what the system is designed to produce for two
kinds of position: an ordinary one (the 3–4 sentence rule) and a forced checkmate
(the length exception). Both input positions are legal; the evaluations shown are
rounded illustrations, not claims of engine-exact numbers.

---

## Example 1 — Normal position (side is a clean piece up)

**Input given to the model**

- **Position:** `r2q1rk1/ppp2ppp/8/3p4/1b1P4/2N1PN2/PP3PPP/R2Q1RK1 w - - 0 1`
  (White: Kg1, Qd1, Ra1, Rf1, Nc3, Nf3, pawns a2 b2 d4 e3 f2 g2 h2. Black: Kg8, Qd8,
  Ra8, Rf8, Bb4, pawns a7 b7 c7 d5 f7 g7 h7.)
- **Evaluation:** `+3.0` (White's point of view, in pawns)
- **Piece-by-piece:** White is a full minor piece ahead — two knights against Black's
  single bishop, pawns level. White's king is safely castled; rooks and queen are
  ready to be activated. Black's b4-bishop achieves nothing and the d5-pawn is
  isolated on a half-open file. Black has no threat and no compensation.

**Output**

### Beginner (under 1000)
White is clearly winning, because White has an extra piece — two knights against just
one bishop — and everything else is equal. Nothing dangerous is happening right now:
the white king is tucked safely behind its pawns and Black has no threat. The simplest
plan is to bring the rooks and queen into play and trade pieces whenever you can,
because when you are a piece up, swapping pieces makes the win easier. Just keep your
own pieces protected and don't give the extra piece back.

### Intermediate (1000–2000)
White is up a clean minor piece with a safe king and Black has no compensation, so
this is close to winning (about +3). The position is quiet: Black's b4-bishop is doing
little and the isolated d5-pawn on the half-open file is a long-term target. White
should finish developing (rooks to c1/e1, reroute the queen) and steer toward
exchanges, since simplification favours the side with extra material. Watch only that
the bishop doesn't create a cheap trick against c3; otherwise trade down toward a won
endgame.

### Master (2000+)
White is a clean piece up (~+3) with no structural or dynamic compensation for Black:
the king is secure, the b4-bishop bites on nothing, and the isolated d5-pawn is a
static weakness on the half-open d-file. The conversion is trivial in principle —
defuse any b4/c3 friction (a2-a3 to question the bishop, or Ne2/Qd3 rerouting), then
trade queens and a pair of rooks to kill counterplay. With no imbalance working for
Black, mass exchanges convert most cleanly; the extra knight decides while d5 is
rounded up or simply ignored. There is no reason to keep pieces on — minimise Black's
activity and enter a won minor-piece or rook endgame.

---

## Example 2 — Forced checkmate (length exception applies)

**Input given to the model**

- **Position:** `5r1k/6pp/7N/8/8/1Q6/8/6K1 w - - 0 1`
  (White: Kg1, Qb3, Nh6. Black: Kh8, Rf8, pawns g7 h7.)
- **Evaluation:** `M2` (forced mate for White in 2)
- **Piece-by-piece:** The knight on h6 covers f7 and g8; the queen on b3 rakes the
  long light diagonal to g8. Black's king on h8 is boxed in by its own rook on f8 and
  the g7/h7 pawns, with no flight squares — the classic smothered-mate picture:
  `Qg8+` forces `...Rxg8`, then `Nf7` is mate.

**Output** *(longer than 3–4 sentences — permitted only because this is a forced mate)*

### Beginner (under 1000)
White has a forced checkmate in two moves, so the game is essentially over. Black's
king on h8 is trapped in the corner by its own rook and pawns and has no safe square
to escape to. White plays the queen to g8 with check, and Black is forced to take it
with the rook, since nothing else stops the check. Then the knight jumps to f7 and
it's checkmate: the king can't move, can't capture the knight, and nothing can block.
So the finish is queen to g8, rook takes queen, knight to f7 — mate.

### Intermediate (1000–2000)
This is a textbook smothered mate, forced in two, with Black's king self-blocked on h8
by the f8-rook and the g7/h7 pawns. 1.Qg8+ is a decoy sacrifice — the rook must
recapture (1...Rxg8) — and 2.Nf7 is mate, the king smothered by its own men. There is
no defence, because every escape square is occupied and the knight can't be taken.
It's the classic pattern worth memorising: a knight landing on f7 with a queen
deflection to clear g8.

### Master (2000+)
Standard Philidor's-legacy smothered mate, forced: with the king immured on h8
(Rf8, pawns g7/h7) and Nh6 already covering f7 and g8, 1.Qg8+!! Rxg8 2.Nf7# is clean
and unavoidable. The queen sacrifice is a pure deflection/obstruction — it removes the
g8 flight and lures the rook to a square that preserves the smother. Nothing
interposes and f7 is untouchable, so the mate is immune to any in-between move. Trivial
to execute; the only way to spoil it is to miss the queen sac.
