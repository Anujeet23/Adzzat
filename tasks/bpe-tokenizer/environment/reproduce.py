"""Demonstrates two current bugs: non-deterministic-looking tie-breaking
during training, and merges applied in the wrong order during encoding."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from bpe import train_bpe, encode  # noqa: E402


def main():
    # ('a','b') and ('c','d') are exactly tied at frequency 3; the spec
    # requires picking the lexicographically smaller pair, ('a', 'b').
    word_freqs = {"cd": 3, "ab": 3}
    merges = train_bpe(word_freqs, 1)
    print("tie-break: got", merges, "expected [('a', 'b')]")
    if merges != [("a", "b")]:
        print("BUG REPRODUCED: training picked whichever pair it counted "
              "first, not the lexicographically smaller one required by "
              "the tie-break rule.")

    print()
    # ('b','c') has higher priority (lower index) than ('a','b'). The
    # correct result applies ('b','c') first: 'a' + 'bc'. A left-to-right
    # single pass instead merges ('a','b') first because it appears
    # earlier in the string, producing 'ab' + 'c' -- ignoring priority.
    merge_list = [("b", "c"), ("a", "b")]
    result = encode("abc", merge_list)
    print("priority order: got", result, "expected ['a', 'bc', '</w>']")
    if result != ["a", "bc", "</w>"]:
        print("BUG REPRODUCED: encode applied merges in left-to-right "
              "string position order instead of merge-list priority order.")


if __name__ == "__main__":
    main()
