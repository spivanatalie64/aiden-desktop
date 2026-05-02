all:
	semodule -i aiden.pp aiden_helper.pp aiden_sandbox.pp
	restorecon -Rv /usr/lib/aiden /usr/bin/aiden /usr/libexec/aiden-helper.py /etc/aiden

%.pp: %.te
	make -f /usr/share/selinux/devel/Makefile $@

clean:
	rm -f *.pp *.mod
