"""Experimental river ordering; bundle after vector_equity.py.

On the river no draws remain. Use the complete showdown rank for range
percentiles, including kickers, instead of the earlier street's draw heuristic.
The scalar fallback and flop/turn features are unchanged.
"""
_draw_street_strength = vector_strength


def vector_strength(pair, board, made=None):
    if len(board) != 5:
        return _draw_street_strength(pair, board, made)
    if made is None:
        made = batch_rank(np.concatenate((
            pair, np.broadcast_to(board, (len(pair), 5))), axis=1))
    # The affine scale preserves exact rank order and ties in [0, 1].
    # Consumers use weighted percentiles, never an equity interpretation.
    return made / float(9 * 15 ** 5)
