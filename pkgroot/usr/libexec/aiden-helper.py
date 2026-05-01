#!/usr/bin/env python3
"""Minimal privileged helper for AIDEN.

This script is a scaffold: it demonstrates how to expose limited privileged
operations. It MUST be installed by a package manager to a system path and be
invoked via polkit (pkexec) or a systemd service with appropriate policy.

Do not enable this un-reviewed; only add the specific operations you need.
"""
import argparse
import subprocess
import sys
import logging

"""Hardened privileged helper.

Only allows specific actions. For 'run' action, commands must match an explicit
whitelist. This script should be installed with root ownership and executed via
pkexec or another polkit mechanism.
"""

ALLOWED_RUN_COMMANDS = [
    # specify allowed commands as lists of tokens
    ['ls', '/root'],
    ['/usr/bin/apt', 'update'],
]


def reboot_system():
    subprocess.check_call(['systemctl', 'reboot'])


def is_allowed(cmd_list):
    # exact match against whitelist entries
    for allowed in ALLOWED_RUN_COMMANDS:
        if cmd_list == allowed:
            return True
    return False


def run_command(cmd):
    if not is_allowed(cmd):
        raise PermissionError('command not permitted')
    return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')


def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', required=True, choices=['reboot', 'run'])
    parser.add_argument('--cmd', nargs='+')
    args = parser.parse_args()

    try:
        if args.action == 'reboot':
            logging.info('Performing reboot')
            reboot_system()
            print('rebooting')
            return

        if args.action == 'run':
            if not args.cmd:
                print('missing --cmd', file=sys.stderr)
                sys.exit(2)
            out = run_command(args.cmd)
            print(out)
    except PermissionError as e:
        print(f'Permission denied: {e}', file=sys.stderr)
        sys.exit(3)
    except subprocess.CalledProcessError as e:
        print(e.output.decode('utf-8', errors='ignore'), file=sys.stderr)
        sys.exit(e.returncode)


if __name__ == '__main__':
    main()
