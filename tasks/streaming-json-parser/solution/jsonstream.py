"""Reference implementation. Author-only; not shipped to agents.

The key move versus the naive starter: the scanner tracks whether it is
currently inside a string literal, and whether the previous character
inside that string was an unconsumed escaping backslash, so brace
characters and escaped quotes inside strings never disturb the
structural depth count.
"""
import json as _json


class StreamingParser:
    def __init__(self):
        self._buf = ""

    def feed(self, chunk):
        self._buf += chunk
        results = []
        while True:
            value, rest = self._try_extract(self._buf)
            if value is None:
                break
            results.append(_json.loads(value))
            self._buf = rest
        return results

    def _try_extract(self, buf):
        i = 0
        n = len(buf)
        while i < n and buf[i] in " \t\r\n":
            i += 1
        if i >= n or buf[i] not in "{[":
            return None, buf
        start = i
        depth = 0
        in_string = False
        escaped = False
        while i < n:
            ch = buf[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch in "{[":
                    depth += 1
                elif ch in "}]":
                    depth -= 1
                    if depth == 0:
                        return buf[start:i + 1], buf[i + 1:]
            i += 1
        return None, buf
