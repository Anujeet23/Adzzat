# Scalar autodiff engine — contract

Source: an original, minimal starter at `/app/repo/autodiff`, not a fork of an existing project.

## API

`autodiff.Value(data)` wraps a Python float and builds a computation graph as operations are applied. Required operators/methods: `+`, `-`, `*`, `/`, unary `-`, `**` (integer or float constant exponent only, never `Value ** Value`), `.relu()`, `.tanh()`, `.exp()`, `.log()`. Mixing a `Value` with a plain `int`/`float` operand (on either side) must work. `.data` holds the forward value; `.grad` holds the gradient accumulated by the most recent `.backward()` call.

`value.backward()` computes `d(value)/d(x)` for every `Value` `x` that was used (directly or indirectly) to compute `value`, and stores it in `x.grad`. The call seeds `value.grad = 1.0` and propagates in reverse topological order.

## The guarantee that matters

If a `Value` is used as an input to more than one operation -- directly reused in Python code, e.g. `t = x * x` (where the same object `x` is both operands) or `y = f(x) + g(x)` -- its `.grad` after `backward()` must equal the **sum** of the gradient contributions along every path from it to the output, not just the contribution from one of those paths. This is the standard multivariate chain rule for a computation graph that is not a tree (a DAG with shared nodes), and it is the entire source of difficulty here: every local backward rule must accumulate into a parent's `.grad`, never overwrite it.

## What's out of scope

Tensors/arrays (this is scalar-only), second derivatives, and graph reuse across multiple `.backward()` calls without resetting `.grad` first (grading always constructs a fresh graph and calls `.backward()` exactly once per check).

## Delivery

Copy the complete `autodiff` package to `/app/submission/autodiff`. The verifier imports only that path, as an unprivileged user, in a separate container from the one you worked in. It does not read `/app/repo` and installs nothing beyond the Python standard library.
