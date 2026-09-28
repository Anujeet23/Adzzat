Fix the reverse-mode autodiff engine at `/app/repo/autodiff` so gradients are correct whenever a `Value` is used by more than one downstream operation, not just when every value is used exactly once. Read `/app/TASK_CONTRACT.md` for the exact API and the precise guarantee before changing anything; `/app/reproduce.py` shows `backward()` producing a wrong gradient for `y = x**2 + x**3`.

## Interface

`autodiff.Value(data)` wraps a float and builds a computation graph as operations are applied: `+`, `-`, `*`, `/`, unary `-`, `**` (constant exponent only), `.relu()`, `.tanh()`, `.exp()`, `.log()`, mixable with plain `int`/`float` on either side. `.data` is the forward value; `value.backward()` seeds `value.grad = 1.0` and propagates gradients in reverse topological order, storing `d(value)/d(x)` in `x.grad` for every `Value` `x` used to compute it.

## The guarantee that matters

If a `Value` is used as input to more than one operation -- `t = x * x` (the same object as both operands), or `y = f(x) + g(x)` -- its `.grad` after `backward()` must equal the sum of the gradient contributions along every path from it to the output, per the multivariate chain rule for a computation graph, not a tree. Every local backward rule must accumulate into a parent's `.grad`. This is the entire source of difficulty here.

## Deliverable

Copy the complete, working `autodiff` package to `/app/submission/autodiff`. The verifier imports only `/app/submission/autodiff` as an unprivileged user in a separate container; it does not read `/app/repo` and installs nothing beyond the Python standard library.

## Verification

Five independent, weighted criteria. Each builds a computation graph with the submission's `Value` class, calls `backward()`, and checks every leaf's `.grad` against an independently computed central-difference numerical gradient of the same mathematical function (never trusting the submission's own forward values for the comparison): a simple chain where every value is used once (15%); a graph where a single value is used by multiple operations, testing accumulation directly (30%); a graph built inside a Python loop over several distinct leaves (20%); a deeper graph mixing `relu`, `tanh`, `exp`, and `log` with value reuse (20%); and a small mixed integration case (two-input, two-hidden-unit scalar network) checking gradients on every one of its eleven parameters at once (15%). A full pass requires all five; per-criterion outcomes are retained separately for diagnosis.

Only the Python standard library is available at verification time; no network access.
