Debian packaging instructions

1. Populate package metadata in control file (Maintainer, Depends as needed).
2. Place files into a directory tree matching install paths, then run dpkg-deb --build.
3. Ensure aiden-helper.py is installed to /usr/libexec/aiden-helper.py and owned by root with mode 750.
4. Install polkit action to /usr/share/polkit-1/actions/org.acreetionos.aiden.policy
