# Beam search — contract

Source: an original, minimal starter at `/app/repo/beamsearch`, not a fork of an existing project.

## API

```python
def beam_search(transition_logprobs, start_token, end_token, vocab_size, beam_width, max_length):
    ...
```

`transition_logprobs` is a `dict[int, list[float]]` mapping a token id (the most recent token in a sequence, or `start_token` before anything has been generated) to a list of length `vocab_size` giving `log P(next_token=i | previous_token)` for `i in range(vocab_size)`. `start_token` never appears in generated output; `end_token` marks a finished sequence. `max_length` bounds the number of *generated* tokens (not counting `start_token`).

Returns a list of `(sequence, raw_logprob)` tuples, at most `beam_width` entries, sorted best-first. `sequence` is a list of generated token ids: it ends with `end_token` if the hypothesis reached `end_token` at or before `max_length` steps, or has no `end_token` (length exactly `max_length`) if it was still active when generation was cut off. `raw_logprob` is the sum of the transition log-probabilities actually taken to produce `sequence` -- never length-normalized.

## The algorithm, precisely

1. Start with one hypothesis: the empty sequence, score `0.0`.
2. At each step, expand every currently-active (not yet ended) hypothesis into all `vocab_size` possible next tokens, each producing a new candidate with its raw cumulative log-probability. Already-finished hypotheses pass through unchanged. Keep the top `beam_width` candidates **by raw cumulative log-probability**, combined across all active hypotheses together -- never per-hypothesis. Ties are broken by preferring the lexicographically smaller sequence (as a tuple of token ids); this same tie-break rule applies to every selection step, not only the final one.
3. Stop after `max_length` steps (or earlier if every hypothesis has already reached `end_token`).
4. Only now, for the final ranking of the (at most) `beam_width` surviving hypotheses, sort by the length-normalized score `raw_logprob / len(sequence)`, again breaking ties by lexicographically smaller sequence.

Normalizing by length at any point *before* the final ranking -- i.e. using it to decide which candidates survive intermediate pruning -- is incorrect: it compares hypotheses of different lengths on an inconsistent basis and biases which candidates ever reach the final step at all.

## What's out of scope

Vocabularies larger than a few dozen tokens, `max_length` beyond a few dozen steps, and any external language model -- `transition_logprobs` is given directly.

## Delivery

Copy the complete `beamsearch` package to `/app/submission/beamsearch`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
