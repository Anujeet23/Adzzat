Fix the beam search at `/app/repo/beamsearch` so it prunes hypotheses using their raw cumulative log-probability at every intermediate step and only applies length normalization once, when ranking the final surviving hypotheses -- and so ties in score, at any selection step, are broken deterministically by preferring the lexicographically smaller sequence. Read `/app/TASK_CONTRACT.md` for the exact algorithm before changing anything; `/app/reproduce.py` shows a short, high-scoring completed sequence getting pruned away in favor of a longer, worse one.

## Interface

`beamsearch.beam_search(transition_logprobs, start_token, end_token, vocab_size, beam_width, max_length)`. `transition_logprobs` is a `dict[int, list[float]]` mapping the most recent token (or `start_token` initially) to `log P(next_token=i | previous_token)` for `i in range(vocab_size)`. Returns up to `beam_width` `(sequence, raw_logprob)` tuples, best-first, where `sequence` ends with `end_token` if the hypothesis finished, or has length exactly `max_length` with no `end_token` if it was cut off, and `raw_logprob` is the un-normalized sum of log-probabilities taken.

## The algorithm, precisely

Start from a single empty-sequence hypothesis. At each step, expand every active hypothesis into all `vocab_size` next tokens; keep the global top `beam_width` candidates (combined across hypotheses, never per-hypothesis) by *raw* cumulative log-probability, breaking ties by lexicographically smaller sequence. Stop at `max_length` steps or once every hypothesis has reached `end_token`. Only then, for the final output, re-rank the survivors by the length-normalized score `raw_logprob / len(sequence)`, again with the same tie-break rule. Normalizing before that final step -- using it to decide what survives intermediate pruning -- compares hypotheses of different lengths inconsistently and biases the search itself.

## Deliverable

Copy the complete, working `beamsearch` package to `/app/submission/beamsearch`. The verifier imports only `/app/submission/beamsearch` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria, each checked exactly against the grader's own independent implementation of the algorithm above (sequences and their order must match exactly; raw log-probabilities are checked to floating-point tolerance): a straightforward transition table (20%); a table where a short, immediately-completed sequence has the best final normalized score, exposing premature normalization during pruning (25%); a second, differently-shaped transition table stressing the same distinction (20%); an exact score tie at a pruning step, resolvable only by the lexicographic tie-break rule (20%); and a batch of three transition tables combining the above, checked in one run (15%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.

Only the Python standard library is available at verification time; no network access.
