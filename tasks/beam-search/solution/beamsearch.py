"""Reference implementation.

Two things naive beam search implementations routinely get wrong, both
handled here: (1) pruning at each intermediate step uses the raw
cumulative log-probability, not the length-normalized score -- normalizing
mid-search compares sequences of different lengths on an inconsistent
basis and biases the search itself; length normalization is applied only
once, when ranking the finished candidates. (2) pruning keeps the true top
`beam_width` candidates across ALL beams' expansions combined, never just
the best continuation of each individual beam.
"""


def beam_search(transition_logprobs, start_token, end_token, vocab_size, beam_width, max_length):
    beams = [([], 0.0, False)]

    for _ in range(max_length):
        if all(done for _, _, done in beams):
            break
        candidates = []
        for seq, score, done in beams:
            if done:
                candidates.append((seq, score, True))
                continue
            prev = seq[-1] if seq else start_token
            logprobs = transition_logprobs[prev]
            for tok in range(vocab_size):
                new_seq = seq + [tok]
                new_score = score + logprobs[tok]
                candidates.append((new_seq, new_score, tok == end_token))
        candidates.sort(key=lambda c: (-c[1], tuple(c[0])))
        beams = candidates[:beam_width]

    beams.sort(key=lambda c: (-(c[1] / len(c[0])), tuple(c[0])))
    return [(seq, score) for seq, score, _ in beams]
