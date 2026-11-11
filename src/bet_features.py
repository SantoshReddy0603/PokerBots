def raise_size_features(pot_before, to_call_before, addition):
    """Total new chips / pot after matching the outstanding bet, before raising.

    Both prediction and public-history replay pass the raiser's incremental
    contribution (raise-to minus their prior street total), including the call.
    The small/large boundary is exactly 3/5; equality belongs to large.
    """
    denominator = max(1, pot_before + to_call_before)
    ratio = addition / denominator
    bucket = "fold_small" if 5 * addition < 3 * denominator else "fold_large"
    return ratio, bucket
