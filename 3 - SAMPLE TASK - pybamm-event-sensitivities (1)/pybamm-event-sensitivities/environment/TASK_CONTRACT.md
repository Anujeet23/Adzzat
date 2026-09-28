# Event-aligned experiment sensitivities

Upstream: PyBaMM v25.4.0, commit `a2a0330fbcd518dbcedf2b1dcee7730bcb9a9042`, BSD-3-Clause. Source and existing tests are in `/app/repo`. This is a feature extension to a documented limitation, not a claim that the original API promises event-time derivatives.

## Calling convention

Use normal `pybamm.Simulation` and `pybamm.Experiment` objects. Opt in by passing both `calculate_sensitivities=True` and `calculate_event_sensitivities=True` to `Simulation.solve`. Inputs are named physical scalar values, and derivatives are with respect to those raw values, not their logarithms. All selected parameters occur in every processed step model. The supported domain and exclusions are stated in `instruction.md`.

The added flag must work with constant-current, rest, and implicit constant-voltage steps; event-terminated and prescribed-duration steps may be mixed. A continuation uses an event-sensitive `starting_solution` computed at the same input values. Reusing a simulation for different input values must recompute its derivatives correctly. No behavior is required for continuation from history that lacks event-sensitivity information.

## Derivative meanings

Let a step start at absolute time `a(p)` and end at `b(p)`. At an interior observation with fixed elapsed duration `r`, the sample is evaluated at `a(p)+r`. At the terminating endpoint, it is evaluated at the actual `b(p)`, even when that endpoint was located by a termination event.

- Existing `solution[variable].sensitivities` retain their fixed-absolute-time interpretation. Their state dependence must include all preceding event transitions.
- New `solution[variable].phase_sensitivities` give the total derivative of the output when the observation follows the step-relative convention above. The endpoint is evaluated on the terminating step's side. This includes explicit dependence of an output on absolute time.
- New `solution.time_sensitivities` give the derivative of the absolute timestamp of each sample under the same convention. Interior samples hold their nominal elapsed time fixed; this does not mean differentiating the solver's adaptive mesh-selection algorithm. A prescribed-duration endpoint holds that duration fixed; an event endpoint follows the event.

Both added properties return dictionaries with one entry per input parameter and an `"all"` entry. Scalar parameter entries have one column. `"all"` stacks columns in alphabetical parameter-name order, matching native all-input sensitivities. Time arrays have shape `(len(solution.t), number_of_columns)`. Output arrays use the same time-major flattened shape as the existing processed-variable `sensitivities` property. The graded processed outputs are scalar.

The full solution, its cycles and steps must expose aligned derivatives. `first_state`, `last_state`, `copy()`, and chronological addition must preserve the corresponding samples and derivatives. Accessing or combining solutions must not mutate the original solution's derivative data. Forward output values, event order and timing remain consistent with the original solver. Without the opt-in flag, existing calls remain valid.

## Verification and numerical tolerances

Tests use analytic models with known event behavior and independent central differences of complete pristine-upstream forward experiments. Perturbations preserve event ordering and use converged step sizes. Interior fixed-time comparisons are safely within the same step for both perturbations. Interior step-relative queries coincide with the nominal experiment output grid; no new interpolation API is required.

Forward step-end times must agree within `0.001 s`; scalar output values within `5e-6` in their stated units. Event-time derivatives allow `0.05 + 2e-4*abs(reference)` in seconds per input unit. Other derivatives allow `3e-4 + 3e-4*abs(reference)` in output units per input unit, tightened to `3e-5 + 3e-5*abs(reference)` for analytic models. Array dimensions, column order and sample alignment must match exactly. Metadata state extraction and copies are checked to `1e-8` absolute where applicable. Non-finite results fail.

The independent criteria are: analytic event/DAE derivatives (20%), battery discharge/relaxation derivatives (25%), implicit voltage-control derivatives (25%), continuation and reuse (20%), and fixed-duration/native compatibility (10%). These weights produce diagnostic partial scores; the harness reward is 1 only when all criteria pass.

## Delivery and development

Copy the entire modified `/app/repo/src/pybamm` directory to `/app/submission/pybamm`. The verifier imports only that submitted package plus the installed pinned dependencies. It does not use changes left solely in `/app/repo`, install new dependencies, or execute your build scripts. Do not remove bundled parameter data or required package modules. The verifier runs submitted Python as an unprivileged user in a separate container.

`/app/reproduce.py` demonstrates the original limitation using an analytic experiment. The original test suite is available; for example, run `python -m pytest -n 0 tests/unit/test_solvers/test_idaklu_solver.py` from `/app/repo`. The task does not prescribe a differentiation algorithm or an implementation layout.
