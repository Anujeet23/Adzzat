"""Beam search over a token transition log-probability table. Expands every
active beam to all vocab_size candidates and keeps the global top
beam_width -- but normalizes each candidate's score by its current length
at every intermediate step, not only when ranking the final output, and
breaks score ties using whatever order the candidates happened to be
generated in. See /app/TASK_CONTRACT.md.
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
        candidates.sort(key=lambda c: -(c[1] / len(c[0])))
        beams = candidates[:beam_width]

    beams.sort(key=lambda c: -(c[1] / len(c[0])))
    return [(seq, score) for seq, score, _ in beams]
