# BPE tokenizer — contract

Source: an original, minimal starter at `/app/repo/bpe`, not a fork of an existing project.

## API

```python
def train_bpe(word_freqs: dict[str, int], num_merges: int) -> list[tuple[str, str]]:
    ...

def encode(word: str, merges: list[tuple[str, str]]) -> list[str]:
    ...
```

`word_freqs` maps a whitespace-free word to its frequency count in some reference corpus. Every word starts split into its individual Unicode characters, followed by a trailing end-of-word symbol `"</w>"` as its own symbol -- so `"low"` starts as `["l", "o", "w", "</w>"]`. Merges never cross word boundaries; each word is processed independently.

## Training

Repeat `num_merges` times: across all words (each pair's count weighted by its word's frequency), find the adjacent symbol pair with the highest total count. If the best count is `1` or fewer, or there are no pairs left, stop early. **Ties are broken by preferring the pair that is lexicographically smallest as a 2-tuple of strings** (Python's default tuple/string ordering). Merge every occurrence of the winning pair, in every word, into a single new symbol (string concatenation of the two symbols), and record `(symbol_a, symbol_b)` as the next entry of the returned merge list, in order. Pair counts must be correct for the state of the words *after* every previous merge in this call -- a word like `"aaaa"` has 3 occurrences of the pair `("a", "a")` before any merge, not fewer, and that count changes once `("a", "a")` itself gets merged.

## Encoding

`merges` is a priority-ordered list: index `0` is the highest priority. Starting from `word`'s character-level symbols (with the trailing `"</w>"`), repeatedly find the single applicable pair with the **lowest index in `merges`** anywhere in the current symbol sequence, and apply only that one merge; then search again from scratch. Stop when no adjacent pair in the current sequence appears in `merges` at all. This is not the same as a single left-to-right pass, and not the same as applying merges in one in-order sweep through `merges` -- a later merge in the sequence can need to happen before an earlier-priority merge becomes possible, but whenever a higher-priority merge *is* currently applicable anywhere, it must be taken before any lower-priority one.

## What's out of scope

Byte-level (as opposed to Unicode-character-level) base symbols, sub-word regularization/sampling, and any pretrained vocabulary -- everything needed is in `word_freqs` and `merges` themselves.

## Delivery

Copy the complete `bpe` package to `/app/submission/bpe`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
