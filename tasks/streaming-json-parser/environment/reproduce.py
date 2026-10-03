"""Demonstrates the brace-inside-a-string bug live."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "repo"))
from jsonstream import StreamingParser  # noqa: E402


def main():
    parser = StreamingParser()
    text = '{"shape": "{curly}"}'
    try:
        results = parser.feed(text)
        if results == [{"shape": "{curly}"}]:
            print("correctly parsed:", results)
        else:
            print("BUG REPRODUCED: fed %r in one call, got %r instead of "
                  "[{'shape': '{curly}'}] -- the brace inside the string "
                  "value threw off depth tracking." % (text, results))
    except Exception as exc:  # noqa: BLE001
        print("BUG REPRODUCED: feeding %r raised %s: %s -- the brace inside "
              "the string value was treated as a structural character." % (
                  text, type(exc).__name__, exc
              ))


if __name__ == "__main__":
    main()
