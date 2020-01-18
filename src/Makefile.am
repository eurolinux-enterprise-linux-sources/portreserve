sbin_PROGRAMS = src/portreserve
man_MANS = doc/portreserve.1 doc/portrelease.1

src_portreserve_SOURCES = src/portreserve.c

# The man pages are generated from DocBook XML.
$(man_MANS): doc/portreserve.xml
	xmlto man -o doc $<

# Special rules for portrelease, which is just a symlink.
src/portrelease$(EXEEXT): src/portreserve$(EXEEXT)
	ln -sf $(notdir $<) $@

install-exec-hook:
	ln -sf "`echo portreserve|sed '$(transform)'`" $(DESTDIR)$(sbindir)/"`echo portrelease|sed '$(transform)'`"

uninstall-hook:
	rm -f $(DESTDIR)$(bindir)/"`echo portrelease|sed '$(transform)'`"

CLEANFILES = src/portrelease $(man_MANS)

EXTRA_DIST = portreserve.spec portreserve.init doc/portreserve.xml

tag:
	cvs tag -c `echo V@VERSION@ | tr . _`
