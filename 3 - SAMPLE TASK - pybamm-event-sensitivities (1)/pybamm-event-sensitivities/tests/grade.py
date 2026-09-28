"""Grade numerical API behavior without importing the submitted package as root."""
import json
import os
from pathlib import Path
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

import numpy as np

HERE = Path(__file__).resolve().parent
LOGS = Path('/logs/verifier')
SUBMISSION = Path('/app/submission')
WEIGHTS = {'1': 20, '2': 25, '3': 25, '4': 20, '5': 10}


def read_json(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd) as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 32_000_000:
            raise ValueError('Expected bounded regular JSON file')
        return json.loads(stream.read(32_000_001))


def compare(actual, expected, absolute, relative=0):
    a = np.asarray(actual); b = np.asarray(expected)
    if (a.shape != b.shape or a.dtype.kind not in 'fi' or b.dtype.kind not in 'fi'
            or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b))):
        raise ValueError('Invalid numerical shape/type/value')
    delta = np.abs(a-b)
    if np.any(delta > absolute + relative*np.abs(b)):
        raise ValueError(f'Numerical error {float(delta.max())} exceeds tolerance')
    return float(delta.max()) if delta.size else 0.


def kill_children():
    for _ in range(10):
        found = False
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                line = next(s for s in (entry/'status').read_text().splitlines() if s.startswith('Uid:'))
                if 65534 in map(int, line.split()[1:]):
                    os.kill(int(entry.name), signal.SIGKILL); found = True
            except (FileNotFoundError, ProcessLookupError):
                pass
        if not found:
            return
        time.sleep(.01)


def main():
    LOGS.mkdir(exist_ok=True, parents=True)
    base = Path(tempfile.mkdtemp(prefix='event-eval-'))
    os.chmod(base, 0o755)
    probe = base/'probe.py'
    shutil.copyfile(HERE/'probe.py', probe); os.chmod(probe, 0o644)
    counter = 0
    timings = {}

    def invoke(name, config):
        nonlocal counter
        if not (SUBMISSION/'pybamm/__init__.py').is_file():
            raise ValueError('Submitted package is missing')
        counter += 1
        source = base/f'input-{counter}.json'
        source.write_text(json.dumps(config)); os.chmod(source, 0o644)
        directory = base/f'output-{counter}'
        directory.mkdir(mode=0o700); os.chown(directory, 65534, 65534)
        output = directory/'result.json'
        environment = {'PATH': '/usr/local/bin:/usr/bin:/bin', 'HOME': str(directory),
            'PYTHONPATH': str(SUBMISSION), 'PYTHONNOUSERSITE': '1',
            'PYTHONDONTWRITEBYTECODE': '1', 'PYBAMM_DISABLE_TELEMETRY': 'true',
            'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1',
            'MPLCONFIGDIR': str(directory/'mpl'), 'MPLBACKEND': 'Agg'}
        started = time.monotonic()
        with (LOGS/f'invocation-{counter}.log').open('wb') as log:
            process = subprocess.Popen([sys.executable, str(probe), '--input', str(source), '--output', str(output)],
                cwd=directory, env=environment, stdout=log, stderr=subprocess.STDOUT,
                user=65534, group=65534, extra_groups=[], start_new_session=True)
            try:
                code = process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
                raise ValueError(f'{name}: 300-second probe limit')
            finally:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                kill_children()
        timings[name] = time.monotonic()-started
        if code:
            raise ValueError(f'{name}: exited {code}; invocation-{counter}.log')
        return read_json(output)

    def check(name):
        fixture = read_json(HERE/'fixtures'/f'{name}.json')
        config = fixture['input']; expected = fixture['expected']
        actual = invoke(name, config)
        detail = {}
        if config.get('compatibility'):
            for key in ['end_times', 'end_values', 'phase_values', 'fixed_values']:
                detail[key] = compare(actual[key], expected[key], 1e-3 if key == 'end_times' else 5e-6)
            for variable, reference in expected['fixed_gradients'].items():
                compare(actual['fixed_gradients'][variable], reference, 3e-5, 3e-5)
            return detail
        if name in ['resume', 'reuse']:
            meta = actual['metadata']
            if 'error' in meta:
                raise ValueError('Metadata access failed: ' + meta['error'])
            names = sorted(config['parameters'])
            for p in names + ['all']:
                before = np.asarray(meta['before'][p])
                if before.shape != (meta['samples'], len(names) if p == 'all' else 1):
                    raise ValueError('Metadata sample/column shape mismatch')
                for version in ['copy', 'combined', 'after']:
                    compare(meta[version][p], before, 1e-8)
                compare(meta['first'][p], before[:1], 1e-8)
                compare(meta['last'][p], before[-1:], 1e-8)
            compare(meta['before']['all'], np.hstack([meta['before'][p] for p in names]), 1e-8)
            for variable in config['variables']:
                item = meta['variables'][variable]
                if np.asarray(item['all']).shape != (meta['samples'], len(names)):
                    raise ValueError('Phase sensitivity all-column shape mismatch')
                compare(item['all'], item['named'], 1e-8)
                for p in names:
                    compare(item['first'][p], item['full_first'][p], 1e-8)
                    compare(item['last'][p], item['full_last'][p], 1e-8)
            if len(meta['steps']) != len(config['steps']):
                raise ValueError('Step metadata count mismatch')
            ending = np.asarray(expected['derivatives']['end_times'])
            for i, step in enumerate(meta['steps']):
                start = ending[i-1] if i else np.zeros(len(names))
                wanted = np.broadcast_to(start, (step['samples'], len(names))).copy()
                wanted[-1] = ending[i]
                compare(step['time']['all'], wanted, .05, 2e-4)
                for column, p in enumerate(names):
                    compare(step['time'][p], wanted[:, column:column+1], .05, 2e-4)
            ends = [config['resume_after']-1, len(config['steps'])-1] if config.get('resume_after') else [len(config['steps'])-1]
            if len(meta['cycles']) != len(ends):
                raise ValueError('Cycle metadata count mismatch')
            for p in names + ['all']:
                compare(np.vstack([c['time'][p] for c in meta['cycles']]), meta['before'][p], 1e-8)
            for cycle, endpoint in zip(meta['cycles'], ends, strict=True):
                compare(cycle['end_time'], expected['values']['end_times'][endpoint], 1e-3)
                for vi, variable in enumerate(config['variables']):
                    for pi, p in enumerate(names):
                        tolerance = 3e-5 if config['model'] == 'analytic' else 3e-4
                        compare(cycle['phase_end'][variable][p], [[expected['derivatives']['end_values'][endpoint][vi][pi]]], tolerance, tolerance)
        for key in expected['values']:
            detail[key] = compare(actual['values'][key], expected['values'][key], 1e-3 if key == 'end_times' else 5e-6)
        tolerance = 3e-5 if config['model'] == 'analytic' else 3e-4
        for key in expected['derivatives']:
            detail['derivative_'+key] = compare(actual['derivatives'][key], expected['derivatives'][key],
                .05 if key == 'end_times' else tolerance, 2e-4 if key == 'end_times' else tolerance)
        return detail

    groups = {'1': ['analytic', 'analytic-dae', 'duration'], '2': ['battery', 'battery-spme'],
              '3': ['voltage-control'], '4': ['resume', 'reuse'], '5': ['compatibility']}
    outcomes = {}; diagnostics = {}
    for number, cases in groups.items():
        try:
            diagnostics[number] = {name: check(name) for name in cases}
            outcomes[number] = 1
        except (ValueError, KeyError, TypeError, OSError, IndexError) as error:
            outcomes[number] = 0; diagnostics[number] = {'error': str(error)}
    reward = int(all(outcomes.values()))
    report = {'task_id': 'pybamm-event-sensitivities', 'reward': reward,
              'weighted_score': sum(WEIGHTS[k]*outcomes[k] for k in outcomes)/100,
              'per_criterion': outcomes, 'full_pass': bool(reward), 'weights': WEIGHTS,
              'diagnostics': diagnostics, 'probe_seconds': timings}
    (LOGS/'criteria.json').write_text(json.dumps(report, indent=2, allow_nan=False))
    (LOGS/'reward.txt').write_text(str(reward))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
