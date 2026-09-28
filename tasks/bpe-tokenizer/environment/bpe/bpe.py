"""Byte-pair-encoding trainer and encoder. Training breaks max-frequency
ties using whatever pair happened to be counted first, and encoding merges
greedily left-to-right in a single pass rather than always applying the
single highest-priority merge available anywhere in the sequence. See
/app/TASK_CONTRACT.md.
"""

END = "</w>"


def _word_symbols(word):
    return list(word) + [END]


def train_bpe(word_freqs, num_merges):
    word_symbols_freqs = [(_word_symbols(word), freq) for word, freq in word_freqs.items()]
    merges = []
    for _ in range(num_merges):
        counts = {}
        for symbols, freq in word_symbols_freqs:
            for i in range(len(symbols) - 1):
                pair = (symbols[i], symbols[i + 1])
                counts[pair] = counts.get(pair, 0) + freq
        if not counts:
            break
        best = max(counts, key=lambda p: counts[p])
        if counts[best] <= 1:
            break
        merges.append(best)
        a, b = best
        new_word_symbols_freqs = []
        for symbols, freq in word_symbols_freqs:
            out = []
            i = 0
            while i < len(symbols):
                if i < len(symbols) - 1 and symbols[i] == a and symbols[i + 1] == b:
                    out.append(a + b)
                    i += 2
                else:
                    out.append(symbols[i])
                    i += 1
            new_word_symbols_freqs.append((out, freq))
        word_symbols_freqs = new_word_symbols_freqs
    return merges


def encode(word, merges):
    merge_set = set(merges)
    symbols = _word_symbols(word)
    changed = True
    while changed:
        changed = False
        out = []
        i = 0
        while i < len(symbols):
            if i < len(symbols) - 1 and (symbols[i], symbols[i + 1]) in merge_set:
                out.append(symbols[i] + symbols[i + 1])
                i += 2
                changed = True
            else:
                out.append(symbols[i])
                i += 1
        symbols = out
    return symbols
