"""Reference BPE trainer/encoder.

Each word starts split into characters plus a trailing '</w>' end-of-word
symbol. Training repeatedly merges the globally most frequent adjacent
symbol pair (weighted by word frequency), breaking ties by preferring the
lexicographically smallest pair, and recomputes pair counts from scratch
each round to avoid any risk of stale/overlapping-count bugs. Encoding
repeatedly finds the single highest-priority (lowest index in `merges`)
applicable merge anywhere in the current symbol sequence and applies it,
never a single left-to-right pass.
"""

END = "</w>"


def _word_symbols(word):
    return list(word) + [END]


def _pair_counts(word_symbols_freqs):
    counts = {}
    for symbols, freq in word_symbols_freqs:
        for i in range(len(symbols) - 1):
            pair = (symbols[i], symbols[i + 1])
            counts[pair] = counts.get(pair, 0) + freq
    return counts


def _apply_merge(symbols, pair):
    out = []
    i = 0
    a, b = pair
    while i < len(symbols):
        if i < len(symbols) - 1 and symbols[i] == a and symbols[i + 1] == b:
            out.append(a + b)
            i += 2
        else:
            out.append(symbols[i])
            i += 1
    return out


def train_bpe(word_freqs, num_merges):
    word_symbols_freqs = [(_word_symbols(word), freq) for word, freq in word_freqs.items()]
    merges = []
    for _ in range(num_merges):
        counts = _pair_counts(word_symbols_freqs)
        if not counts:
            break
        best_count = max(counts.values())
        if best_count <= 1:
            break
        best_pair = min(p for p, c in counts.items() if c == best_count)
        merges.append(best_pair)
        word_symbols_freqs = [(_apply_merge(symbols, best_pair), freq) for symbols, freq in word_symbols_freqs]
    return merges


def encode(word, merges):
    symbols = _word_symbols(word)
    priority = {pair: i for i, pair in enumerate(merges)}
    while True:
        best_rank = None
        best_index = None
        for i in range(len(symbols) - 1):
            pair = (symbols[i], symbols[i + 1])
            rank = priority.get(pair)
            if rank is not None and (best_rank is None or rank < best_rank):
                best_rank = rank
                best_index = i
        if best_index is None:
            break
        a, b = symbols[best_index], symbols[best_index + 1]
        symbols = symbols[:best_index] + [a + b] + symbols[best_index + 2:]
    return symbols
