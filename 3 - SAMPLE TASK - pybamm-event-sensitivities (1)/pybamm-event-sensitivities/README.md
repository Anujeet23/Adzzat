# PyBaMM event sensitivities

The agent extends the pinned PyBaMM scientific library so parameter derivatives remain correct through event-terminated battery experiments. The feature includes event-time derivatives, step-relative output derivatives, fixed-time propagation, implicit voltage control, and solution continuation. See [instruction.md](instruction.md) and [TASK_CONTRACT.md](environment/TASK_CONTRACT.md) for the public API and acceptance requirements.

## Environment

The source archive is pristine PyBaMM v25.4.0, commit `a2a0330fbcd518dbcedf2b1dcee7730bcb9a9042`, distributed with its BSD-3-Clause license. Both images use a digest-pinned Python 3.12.11 Debian Bookworm base and pinned Python dependencies. The target is Linux x86-64 because the pinned native solver wheel requires that architecture. On Apple Silicon, Docker emulation is required. Agent and verifier each receive two CPU cores and 2 GiB RAM; the agent has four hours, and verification has fifty minutes with a 300-second limit per probe.

The agent image contains the source, existing upstream tests, pytest development dependencies, and a public numerical reproduction. No API credentials are needed inside either container. Only a complete package submitted at `/app/submission/pybamm` is transferred to the separate verifier.

## Verification

| Criterion | Diagnostic weight | Behavior |
|---|---:|---|
| Analytic ODE and DAE | 20% | Event derivatives, explicit-time output, duration semantics |
| Battery models | 25% | SPM and SPMe discharge-to-relaxation propagation |
| Voltage control | 25% | Implicit constant-voltage termination and later relaxation |
| Continuation and reuse | 20% | Starting solutions, repeated solves, metadata and extraction |
| Native compatibility | 10% | Existing fixed-duration API without the new flag |

All criteria are numerical and deterministic. Private references come from independent pristine-upstream forward perturbations with checked convergence and event ordering. Analytic references were independently checked against closed-form differentiation. The harness reward is binary: every criterion must pass. A weighted score and numerical residuals are retained separately for diagnosis.

The verifier imports submitted code only as UID 65534. Reference answers and reward files remain inaccessible to that process. Submitted JSON must be finite, bounded, and a regular file. Child processes are terminated after each probe.

## Layout

- `instruction.md`: agent request.
- `task.toml`: Harbor resources, artifacts, and separate verifier configuration.
- `environment/`: pinned runtime, pristine source archive, contract and reproduction.
- `solution/`: author-only reference patch and installation script.
- `tests/`: private numerical references, probe, isolated grader and verifier image.

## Running

From a host with Docker and Harbor 0.7.1:

```sh
harbor run -p /absolute/path/to/pybamm-event-sensitivities -a oracle -k 5 -n 2
harbor run -p /absolute/path/to/pybamm-event-sensitivities -a nop
```

Calibration uses `bedrock/global.anthropic.claude-opus-5`, adaptive thinking and `reasoning_effort=max`. The companion authoring runner accepts the Bedrock token through the host environment and redacts it from provider debug logs. Run five independent attempts against one frozen task revision; preserve trajectories, per-criterion outcomes and model settings.

Validation status is recorded in the companion evidence directory. This package is not certified as meeting the difficulty gate until five valid model rollouts and their step-count analysis are complete. Customer `dq_audit.py` and `dq_post.py` are not bundled with the supplied runbook and have not been executed.
