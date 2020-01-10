Summary: TCP port reservation utility
Name: portreserve
Version: 0.0.4
Release: 11%{?dist}
License: GPLv2+
Group: System Environment/Daemons
URL: http://cyberelk.net/tim/portreserve/
Source0: http://cyberelk.net/tim/data/portreserve/stable/%{name}-%{version}.tar.bz2
Patch1: portreserve-infinite-loop.patch
Patch2: portreserve-list-remove.patch
Patch3: portreserve-initscript-fixes.patch
Patch4: portreserve-memleak.patch
Patch5: portreserve-allow-overlap.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires(post): chkconfig
Requires(preun): chkconfig

BuildRequires: xmlto
Obsoletes: portreserve-selinux < 0.0.3-3

%description
The portreserve program aims to help services with well-known ports that
lie in the portmap range.  It prevents portmap from a real service's port
by occupying it itself, until the real service tells it to release the
port (generally in the init script).

%prep
%setup -q
# Prevent infinite loop.
%patch1 -p1 -b .infinite-loop
# Fixed linked list handling when removing items (bug #718178).
%patch2 -p1 -b .list-remove
# Initscript status code fixes (bug #614924).
%patch3 -p1 -b .initscript-fixes
# Fix small memory leak and move malloc() check close to call (bug #718176).
%patch4 -p1 -b .memleak
# Allow overlapping ports (bug #848414).
%patch5 -p1 -b .allow-overlap

%build
%configure --sbindir=/sbin
make

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}%{_localstatedir}/run/portreserve
mkdir -p %{buildroot}%{_initrddir}
install -m755 portreserve.init %{buildroot}%{_initrddir}/portreserve
mkdir -p %{buildroot}%{_sysconfdir}/portreserve

%clean
rm -rf %{buildroot}

%post
# Do this unconditionally to fix up the initscript's start priority.
# Earlier versions had an incorrect dependency (bug #487250).
/sbin/chkconfig --add portreserve

%preun
if [ "$1" = 0 ]; then
  /sbin/service portreserve stop >/dev/null 2>&1
  /sbin/chkconfig --del portreserve
fi

%postun
if [ "$1" -ge "1" ]; then
  /sbin/service portreserve condrestart >/dev/null 2>&1
fi

%files
%defattr(-,root,root)
%doc ChangeLog README COPYING NEWS
%dir %{_localstatedir}/run/portreserve
%dir %{_sysconfdir}/portreserve
%attr(755,root,root) %{_initrddir}/portreserve
/sbin/*
%{_mandir}/*/*

%changelog
* Thu Mar 17 2016 Martin Sehnoutka <msehnout@redhat.com> - 0.0.4-11
- Revert change for bug #813300

* Tue Jan 12 2016 Tim Waugh <twaugh@redhat.com> 0.0.4-10
- Allow overlapping ports (bug #848414).
- Another initscript status code fix (bug #813300).

* Wed Feb  1 2012 Tim Waugh <twaugh@redhat.com> 0.0.4-9
- Even more initscript status code fixes (bug #614924).

* Thu Jan 26 2012 Tim Waugh <twaugh@redhat.com> 0.0.4-8
- More initscript status code fixes (bug #614924).

* Thu Jan 19 2012 Tim Waugh <twaugh@redhat.com> 0.0.4-7
- Fix small memory leak and move malloc() check close to call (bug #718176).
- Requires chkconfig (bug #712362).

* Thu Dec  1 2011 Tim Waugh <twaugh@redhat.com> 0.0.4-6
- Initscript status code fixes (bug #614924).

* Wed Aug 31 2011 Tim Waugh <twaugh@redhat.com> 0.0.4-5
- Fixed linked list handling when removing items (bug #718178).

* Thu Mar  4 2010 Tim Waugh <twaugh@redhat.com> 0.0.4-4
- Added comments to all patches.

* Fri Jan 22 2010 Tim Waugh <twaugh@redhat.com> 0.0.4-3
- Walk the list of newmaps correctly (bug #557785).

* Mon Nov 30 2009 Dennis Gregorovic <dgregor@redhat.com> - 0.0.4-2.1
- Rebuilt for RHEL 6

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Fri Feb 27 2009 Tim Waugh <twaugh@redhat.com> 0.0.4-1
- 0.0.4:
  - Fixed initscript so that it will not be reordered to start after
    rpcbind (bug #487250).

* Thu Feb 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Feb  4 2009 Tim Waugh <twaugh@redhat.com> 0.0.3-3
- No longer need SELinux policy as it is now part of the
  selinux-policy package.

* Wed Oct 15 2008 Tim Waugh <twaugh@redhat.com> 0.0.3-2
- New selinux sub-package for SELinux policy.  Policy contributed by
  Miroslav Grepl (thanks!).

* Tue Jul  1 2008 Tim Waugh <twaugh@redhat.com> 0.0.3-1
- 0.0.3:
  - Allow multiple services to be defined in a single configuration
    file.
  - Allow protocol specifications, e.g. ipp/udp.

* Mon Jun 30 2008 Tim Waugh <twaugh@redhat.com> 0.0.2-1
- 0.0.2.

* Fri May  9 2008 Tim Waugh <twaugh@redhat.com> 0.0.1-2
- More consistent use of macros.
- Build requires xmlto.
- Don't use %%makeinstall.
- No need to run make check.

* Thu May  8 2008 Tim Waugh <twaugh@redhat.com> 0.0.1-1
- Default permissions for directories.
- Initscript should not be marked config.
- Fixed license tag.
- Better buildroot tag.

* Wed Sep  3 2003 Tim Waugh <twaugh@redhat.com>
- Initial spec file.
