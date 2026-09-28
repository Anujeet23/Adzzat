Fix the byte-pair-encoding trainer and encoder at `/app/repo/bpe` so training breaks frequency ties deterministically and encoding always applies the single highest-priority available merge, not whatever a left-to-right pass happens to find first. Read `/app/TASK_CONTRACT.md` for the exact algorithm before changing anything; `/app/reproduce.py` shows both bugs firing on small, hand-checkable examples.

## Interface

`bpe.train_bpe(word_freqs: dict[str, int], num_merges: int) -> list[tuple[str, str]]` and `bpe.encode(word: str, merges: list[tuple[str, str]]) -> list[str]`. Every word starts split into individual characters plus a trailing `"</w>"` end-of-word symbol; merges never cross word boundaries.

## Training

Repeat up to `num_merges` times: find the adjacent symbol pair with the highest total count across all words (weighted by word frequency), stopping early if the best count is `1` or fewer. **Ties are broken by the lexicographically smallest pair** (as a 2-tuple). Merge every occurrence of the winner in every word and append it to the returned list. Counts must reflect the words' actual state after each previous merge -- get the counting right for a word like `"aaaa"`, where `("a", "a")` occurs 3 times before any merge, and where merging `("a", "a")` itself changes that count.

## Encoding

`merges` is priority-ordered (index 0 = highest priority). Repeatedly find the single applicable pair with the lowest index in `merges` anywhere in the current symbol sequence, apply only that one merge, then search again from scratch; stop when nothing in the sequence matches any entry in `merges`. This is not a single left-to-right sweep: a later-priority merge occurring earlier in the string must still wait if a higher-priority merge is currently applicable anywhere else in the sequence.

## Deliverable

Copy the complete, working `bpe` package to `/app/submission/bpe`. The verifier imports only `/app/submission/bpe` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each checked exactly against the grader's own independent reference implementation of the algorithm above: basic training with no ties (20%); an exact frequency tie during training (25%); encoding that requires respecting merge priority rather than left-to-right order (25%); a repeated-character word stressing correct pair-count recomputation (15%); and an integration case training on a larger corpus and then encoding several words, checking both the merge list and every encoded output (15%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.

Only the Python standard library is available at verification time; no network access.
