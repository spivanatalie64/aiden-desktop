Debian packaging scaffold

This folder contains minimal files for a Debian package. It's a scaffold — you must fill in maintainer, version, dependencies and install paths before building.

Suggested install locations:
 - /usr/bin/aiden (wrapper that launches /usr/lib/aiden/main.py)
 - /usr/lib/aiden/ (python files and resources)
 - /usr/libexec/aiden-helper.py (privileged helper, mode 750 root:root)
 - /usr/share/polkit-1/actions/org.acreetionos.aiden.policy

Use dpkg-deb --build after populating control and install scripts.
