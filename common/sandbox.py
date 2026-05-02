import subprocess
import tempfile
import os
import signal
from pathlib import Path
from typing import Optional

SANDBOX_TIMEOUT = 30


def _seccomp_filter_path() -> Optional[Path]:
    path = Path('/etc/aiden/seccomp/default.bpf')
    if path.exists():
        return path
    return None


def run_sandboxed(
    code: str,
    language: str = 'python',
    timeout: int = SANDBOX_TIMEOUT,
    network: bool = False,
    env: Optional[dict] = None,
) -> dict:
    interpreters = {
        'python': ('python3', '-c'),
        'bash': ('bash', '-c'),
        'sh': ('sh', '-c'),
        'javascript': ('node', '-e'),
        'ruby': ('ruby', '-e'),
        'perl': ('perl', '-e'),
        'lua': ('lua', '-e'),
    }

    if language not in interpreters:
        raise ValueError(f'Unsupported language: {language}')

    exe, flag = interpreters[language]

    bwrap_args = [
        'bwrap',
        '--unshare-ipc',
        '--unshare-pid',
        '--unshare-uts',
        '--unshare-cgroup',
        '--ro-bind', '/usr', '/usr',
        '--ro-bind', '/lib', '/lib',
        '--ro-bind', '/lib64', '/lib64',
        '--ro-bind', '/etc/alternatives', '/etc/alternatives',
        '--tmpfs', '/tmp',
        '--tmpfs', '/var/tmp',
        '--tmpfs', '/home',
        '--tmpfs', '/root',
        '--tmpfs', '/run',
        '--proc', '/proc',
        '--dev', '/dev',
        '--die-with-parent',
        '--hostname', 'sandbox',
    ]

    if not network:
        bwrap_args.append('--unshare-net')

    seccomp_filter = _seccomp_filter_path()
    if seccomp_filter:
        bwrap_args.extend(['--seccomp', str(seccomp_filter)])

    bwrap_args.extend([str(timeout), exe, flag, code])

    env_vars = os.environ.copy()
    if env:
        env_vars.update(env)

    try:
        result = subprocess.run(
            bwrap_args,
            capture_output=True,
            timeout=timeout + 5,
            env=env_vars,
        )
        return {
            'exit_code': result.returncode,
            'stdout': result.stdout.decode('utf-8', errors='replace'),
            'stderr': result.stderr.decode('utf-8', errors='replace'),
            'timeout': False,
        }
    except subprocess.TimeoutExpired:
        return {
            'exit_code': -1,
            'stdout': '',
            'stderr': 'Execution timed out',
            'timeout': True,
        }


def generate_key_in_sandbox(target_path: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix='aiden-keygen-') as tmpdir:
        key_path = Path(tmpdir) / 'id_aiden_mesh'
        try:
            subprocess.run(
                [
                    'bwrap',
                    '--unshare-net',
                    '--unshare-ipc',
                    '--ro-bind', '/usr', '/usr',
                    '--ro-bind', '/lib', '/lib',
                    '--ro-bind', '/lib64', '/lib64',
                    '--tmpfs', '/tmp',
                    '--tmpfs', '/home',
                    '--die-with-parent',
                    'ssh-keygen', '-t', 'ed25519',
                    '-f', str(key_path),
                    '-N', '', '-q',
                ],
                check=True, capture_output=True, timeout=30
            )
            pub_key = (key_path.parent / 'id_aiden_mesh.pub').read_bytes()
            priv_key = key_path.read_bytes()

            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(priv_key)
            target_path.with_suffix('.pub').write_bytes(pub_key)
            os.chmod(target_path, 0o600)

            return {'success': True, 'path': str(target_path)}
        except subprocess.CalledProcessError as e:
            return {
                'success': False,
                'error': e.stderr.decode() if e.stderr else str(e),
            }
