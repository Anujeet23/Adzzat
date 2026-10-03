"""Demonstrates the full-buffer corruption and the full/empty length
ambiguity with the current implementation."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from ringbuffer import RingBuffer, Empty  # noqa: E402


def main():
    rb = RingBuffer(capacity=2)
    rb.push("a")
    rb.push("b")
    print("len after filling to capacity:", len(rb), "(should be 2)")
    pushed = rb.push("c")
    first = rb.pop()
    if pushed and first != "a":
        print("BUG REPRODUCED: push('c') on a full buffer returned %r and "
              "silently overwrote the oldest unread item -- pop() returned "
              "%r instead of 'a'." % (pushed, first))
    else:
        print("push correctly rejected on a full buffer")

    print()
    rb2 = RingBuffer(capacity=2)
    rb2.push("x")
    rb2.push("y")
    full_len = len(rb2)
    rb2.pop()
    rb2.pop()
    empty_len = len(rb2)
    if full_len == empty_len:
        print("BUG REPRODUCED: a full buffer and an empty buffer both report "
              "len()=%d -- head==tail is ambiguous between the two states." % full_len)
    else:
        print("full len=%d, empty len=%d -- correctly distinguished" % (full_len, empty_len))


if __name__ == "__main__":
    main()
