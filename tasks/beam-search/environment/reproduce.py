"""Demonstrates the current implementation pruning away a short, high-
scoring completed sequence in favor of continuing a longer one, because it
compares partial hypotheses of different lengths using a length-normalized
score instead of the raw cumulative log-probability."""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from beamsearch import beam_search  # noqa: E402


def main():
    vocab_size, start_token, end_token = 4, 4, 0
    table = {
        "0": [-1.0484347089, -1.1432854572, -1.6346571021, -1.9971256659],
        "1": [-1.3693702765, -1.5567360337, -1.0062076669, -1.7760412749],
        "2": [-1.6021571398, -1.435205177, -1.0515906479, -1.5554685428],
        "3": [-1.788900094, -0.9976385168, -1.1702477139, -1.8719929213],
        "4": [-1.3779158564, -1.3088125144, -1.4804974813, -1.3853689928],
    }
    transition_logprobs = {int(k): v for k, v in table.items()}

    result = beam_search(transition_logprobs, start_token, end_token, vocab_size, 2, 4)
    print("beam_width=2 results:")
    for seq, score in result:
        length = len(seq)
        print("  seq=%s raw_logprob=%.4f normalized=%.4f" % (seq, score, score / length))

    if [0] not in [seq for seq, _ in result]:
        print("BUG REPRODUCED: the immediately-completed sequence [end_token], "
              "which has the best length-normalized score of any candidate, "
              "never survives to the final beam.")


if __name__ == "__main__":
    main()
