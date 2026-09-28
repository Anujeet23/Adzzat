"""Numerical API probe; inputs contain experiments, never expected answers."""
import argparse
import json
import os
from pathlib import Path

os.environ['PYBAMM_DISABLE_TELEMETRY'] = 'true'
import numpy as np
import pybamm


def make_simulation(config, steps=None):
    if config['model'] == 'analytic':
        model = pybamm.BaseModel()
        model.summary_variables = []
        q = pybamm.Variable('q')
        z = pybamm.Variable('z')
        p = pybamm.InputParameter('capacity')
        k = pybamm.InputParameter('relaxation')
        current = pybamm.Parameter('Current function [A]')
        model.rhs = {q: -current / p, z: (q - z) / (k * p)}
        model.initial_conditions = {q: 4, z: 4}
        model.variables = {'q': q, 'z': z, 'clock-weighted z': pybamm.t * z,
                           'Battery voltage [V]': q, 'Current [A]': current}
        if config.get('algebraic'):
            v = pybamm.Variable('constraint')
            model.algebraic = {v: v - q * q - k * z}
            model.initial_conditions[v] = 16 + 4 * k
            model.variables['constraint'] = v
        parameters = pybamm.ParameterValues({
            'Current function [A]': 1, 'Nominal cell capacity [A.h]': 1,
            'Initial temperature [K]': 298.15, 'Ambient temperature [K]': 298.15})
    else:
        model = getattr(pybamm.lithium_ion, config['model'])()
        parameters = model.default_parameter_values
        parameters.update({k: '[input]' for k in config['parameters']})
    experiment = pybamm.Experiment([tuple(steps or config['steps'])],
                                   period=config['period'])
    return pybamm.Simulation(model, parameter_values=parameters, experiment=experiment,
        solver=pybamm.IDAKLUSolver(rtol=1e-11, atol=1e-11))


def solve(config, enabled=False, reuse=None):
    simulation = reuse or make_simulation(config)
    kwargs = {'inputs': config['parameters'], 'calculate_sensitivities': enabled,
              'calc_esoh': False}
    if enabled:
        kwargs['calculate_event_sensitivities'] = True
    else:
        # Independent forward references retain dense Hermite interpolation;
        # fixed-time perturbations must not differentiate a coarse output grid.
        kwargs['t_interp'] = np.array([])
    split = config.get('resume_after')
    if split:
        first = make_simulation(config, config['steps'][:split])
        history = first.solve(**kwargs)
        second = make_simulation(config, config['steps'][split:])
        solution = second.solve(starting_solution=history, **kwargs)
    else:
        solution = simulation.solve(**kwargs)
    return solution


def steps_of(solution):
    return [step for cycle in solution.cycles for step in cycle.steps]


def values(solution, config):
    steps = steps_of(solution)
    rows = {'end_times': [], 'end_values': [], 'phase_values': [], 'fixed_values': []}
    for index, step in enumerate(steps):
        rows['end_times'].append(float(step.t[-1]))
        rows['end_values'].append([float(step[v].entries[-1]) for v in config['variables']])
        relative = config['queries'][index]['elapsed']
        absolute = config['queries'][index]['absolute']
        rows['phase_values'].append([float(step[v](step.t[0] + relative)) for v in config['variables']])
        rows['fixed_values'].append([float(step[v](absolute)) for v in config['variables']])
    return rows


def derivatives(solution, config):
    rows = {'end_times': [], 'end_values': [], 'phase_values': [], 'fixed_values': []}
    names = sorted(config['parameters'])
    for index, step in enumerate(steps_of(solution)):
        rows['end_times'].append([float(step.time_sensitivities[p][-1, 0]) for p in names])
        endpoint = []; phase = []; fixed = []
        for name in config['variables']:
            variable = step[name]
            phase_sens = variable.phase_sensitivities
            fixed_sens = variable.sensitivities
            endpoint.append([float(phase_sens[p][-1, 0]) for p in names])
            phase.append([float(np.interp(step.t[0] + config['queries'][index]['elapsed'],
                              step.t, np.asarray(phase_sens[p]).ravel())) for p in names])
            fixed.append([float(np.interp(config['queries'][index]['absolute'], step.t,
                              np.asarray(fixed_sens[p]).ravel())) for p in names])
        rows['end_values'].append(endpoint)
        rows['phase_values'].append(phase)
        rows['fixed_values'].append(fixed)
    return rows


def metadata(solution, config):
    names = sorted(config['parameters'])
    original = {k: np.asarray(v).copy() for k, v in solution.time_sensitivities.items()}
    copy = solution.copy()
    first = solution.first_state
    last = solution.last_state
    steps = steps_of(solution)
    combined = steps[0].copy()
    for step in steps[1:]:
        combined = combined + step
    def arrays(values):
        return {key: np.asarray(value).tolist() for key, value in values.items()}
    result = {'samples': len(solution.t), 'before': arrays(original),
              'copy': arrays(copy.time_sensitivities), 'first': arrays(first.time_sensitivities),
              'last': arrays(last.time_sensitivities), 'combined': arrays(combined.time_sensitivities),
              'after': arrays(solution.time_sensitivities), 'variables': {},
              'steps': [{'samples': len(s.t), 'time': arrays(s.time_sensitivities)} for s in steps],
              'cycles': [{'samples': len(c.t), 'time': arrays(c.time_sensitivities),
                          'end_time': float(c.t[-1]), 'phase_end': {
                              v: arrays({p: c[v].phase_sensitivities[p][-1:] for p in names})
                              for v in config['variables']}} for c in solution.cycles]}
    for variable in config['variables']:
        full = solution[variable].phase_sensitivities
        result['variables'][variable] = {
            'all': np.asarray(full['all']).tolist(),
            'named': np.hstack([full[p] for p in names]).tolist(),
            'full_first': arrays({p: full[p][:1] for p in names}),
            'full_last': arrays({p: full[p][-1:] for p in names}),
            'first': arrays({p: first[variable].phase_sensitivities[p] for p in names}),
            'last': arrays({p: last[variable].phase_sensitivities[p] for p in names})}
    return result


def run(config):
    if config.get('compatibility'):
        sim = make_simulation(config)
        sol = sim.solve(inputs=config['parameters'], calculate_sensitivities=True, calc_esoh=False)
        # Fixed-duration experiments retain their established native API.
        result = values(sol, config)
        result['fixed_gradients'] = {
            name: np.asarray(sol[name].sensitivities['all'])[-1].tolist()
            for name in config['variables']}
        return result
    sim = make_simulation(config)
    if config.get('reuse_parameters'):
        other = dict(config, parameters=config['reuse_parameters'])
        solve(other, enabled=True, reuse=sim)
    sol = solve(config, enabled=True, reuse=sim)
    result = {'values': values(sol, config), 'derivatives': derivatives(sol, config)}
    try:
        result['metadata'] = metadata(sol, config)
    except Exception as error:
        result['metadata'] = {'error': type(error).__name__ + ': ' + str(error)}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(json.loads(args.input.read_text()))
    args.output.write_text(json.dumps(result, allow_nan=False))
