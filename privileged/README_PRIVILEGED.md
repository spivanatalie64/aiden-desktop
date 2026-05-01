Privileged helper (polkit)

This folder contains a minimal scaffold for a polkit-activated helper that performs system-level tasks on behalf of the desktop frontend.

Installation notes (packaging required):
 - Copy aiden-helper.py to /usr/libexec/aiden-helper (or similar) and make executable
 - Install org.acreetionos.aiden.policy to /usr/share/polkit-1/actions/
 - Create a systemd service or install as a normal executable called by polkit

The helper is intentionally minimal and must be audited before enabling. It should be installed by the system packager with correct ownership and permissions.
