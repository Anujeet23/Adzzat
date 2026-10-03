"""Finds complete top-level JSON values in a growing text buffer.

This implementation finds a value's end by counting `{`/`[`/`}`/`]`
characters anywhere in the buffered text -- including ones that appear
literally inside a string value. A value like `{"shape": "{curly}"}`
gets cut off (or handed to the JSON decoder incomplete) long before its
real closing brace. See /app/TASK_CONTRACT.md.
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
        while i < n:
            ch = buf[i]
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
                if depth == 0:
                    return buf[start:i + 1], buf[i + 1:]
            i += 1
        return None, buf
