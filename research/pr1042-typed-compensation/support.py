"""I/O and immutable-source loading for the selected compensation integration."""
from contextlib import contextmanager
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
T37 = ROOT / 'research/complex-t37-owners'
T21 = ROOT / 'research/complex-t21-owners'
SOURCE = ROOT / 'research/complex-k492-owner-repair/vendor/multicold'
PR635 = ROOT / 'research/complex-sw4-frame8/vendor/pr635/research/complex-571-cold14-st2'
PR558 = SOURCE / 'vendor/pr558'
PR552 = PR558 / 'vendor/pr552'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    p = Path(path)
    raw = p.read_bytes()
    return json.loads(gzip.decompress(raw) if p.suffix == '.gz' else raw)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def payload_sha(path):
    p = Path(path)
    data = p.read_bytes()
    return hashlib.sha256(gzip.decompress(data) if p.suffix == '.gz' else data).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def gzip_json(path, value):
    Path(path).write_bytes(gzip.compress(json.dumps(value, sort_keys=True, separators=(',', ':')).encode(), mtime=0))


def fresh_directory(path):
    p = Path(path).resolve()
    require(not p.exists() and not p.is_relative_to(ROOT), 'Use a fresh output directory outside the source checkout')
    p.mkdir(parents=True)
    return p


@contextmanager
def source_context(directory):
    """Keep a retained script's import context alive through delayed calls."""
    previous = sys.modules.pop('common', None)
    previous_path = list(sys.path)
    sys.path.insert(0, str(Path(directory).resolve()))
    try:
        yield
    finally:
        sys.path[:] = previous_path
        sys.modules.pop('common', None)
        if previous is not None:
            sys.modules['common'] = previous


def load_source(path, name):
    path = Path(path).resolve()
    with source_context(path.parent):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module


def environment(**extra):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', PYTHONINTMAXSTRDIGITS='0',
               PYTHON=sys.executable, SW4_FRAME8_PYTHON=sys.executable,
               MULTICOLD_SOURCE=str(SOURCE), GAIN_PR564_SOURCE=str(SOURCE))
    for key in ('PYTHONOPTIMIZE', 'WITNESS_DISCOVER', 'WITNESS_RECORD', 'WITNESS_SPEC',
                'XPARAM', 'EXTRAH', 'PAIRING_RANKS', 'DIAG', 'HYBBUDGET', 'PR635_CODE'):
        env.pop(key, None)
    env.update({k: str(v) for k, v in extra.items()})
    return env


def run_stage(directory, stages, name, script, *arguments, env=None, portable=False):
    directory = Path(directory)
    log = directory / (name + '.log')
    command = [sys.executable, '-B']
    if portable:
        command.append(str(SOURCE / 'code/run_portable.py'))
    command += [str(script), *map(str, arguments)]
    start = time.monotonic()
    with log.open('x') as stream:
        proc = subprocess.run(command, cwd=ROOT, env=env or environment(), stdout=stream, stderr=subprocess.STDOUT)
    stages.append(dict(name=name, exit_code=proc.returncode, seconds=round(time.monotonic()-start, 3),
                       source=str(Path(script).resolve().relative_to(ROOT)) if Path(script).resolve().is_relative_to(ROOT) else str(script),
                       source_sha256=sha(script), log_sha256=sha(log)))
    dump(directory / 'STAGES.json', stages)
    require(proc.returncode == 0, name + ' failed: ' + log.read_text(errors='replace')[-6000:])
    print('PASS', name, stages[-1]['seconds'], flush=True)


def validate_sources():
    descriptor = read(HERE/'SOURCES.json')
    for relative,digest in descriptor['source_sha256'].items():
        path = (ROOT/relative).resolve()
        require(not Path(relative).is_absolute() and path.is_relative_to(ROOT), 'Source path containment')
        require(sha(path) == digest, 'Pinned source changed: '+relative)
    return dict(descriptor_sha256=sha(HERE/'SOURCES.json'), source_sha256=descriptor['source_sha256'])
