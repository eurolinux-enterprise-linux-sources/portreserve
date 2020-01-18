%define _hardened_build 1

Summary: TCP port reservation utility
Name: portreserve
Version: 0.0.5
Release: 11%{?dist}
License: GPLv2+
Group: System Environment/Daemons
URL: http://cyberelk.net/tim/portreserve/
Source0: http://cyberelk.net/tim/data/portreserve/stable/%{name}-%{version}.tar.bz2
Source1: portreserve.service
Patch1: portreserve-pid-file.patch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Requires(post): systemd-units
Requires(preun): systemd-units
Requires(postun): systemd-units

# This is actually needed for the %triggerun script but Requires(triggerun)
# is not valid.  We can use %post because this particular %triggerun script
# should fire just after this package is installed.
Requires(post): systemd-sysv

BuildRequires: xmlto
BuildRequires: systemd-units
Obsoletes: portreserve-selinux < 0.0.3-3

%description
The portreserve program aims to help services with well-known ports that
lie in the portmap range.  It prevents portmap from a real service's port
by occupying it itself, until the real service tells it to release the
port (generally in the init script).

%prep
%setup -q

# Avoid a race during start-up if there are no configured ports (bug #1034139).
%patch1 -p1 -b .pid-file

%build
%configure --sbindir=/sbin
make

%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install
mkdir -p %{buildroot}%{_localstatedir}/run/portreserve
mkdir -p %{buildroot}%{_unitdir}
install -m644 %{SOURCE1} %{buildroot}%{_unitdir}/portreserve.service
mkdir -p %{buildroot}%{_sysconfdir}/portreserve
mkdir -p %{buildroot}%{_tmpfilesdir}
cat <<EOF > %{buildroot}%{_tmpfilesdir}/portreserve.conf
d %{_localstatedir}/run/portreserve 0755 root root 10d
EOF

%clean
rm -rf %{buildroot}

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%triggerun -- portreserve < 0.0.5-3
# Save the current service runlevel info
# User must manually run systemd-sysv-convert --apply portreserve
# to migrate them to systemd targets
%{_bindir}/systemd-sysv-convert --save portreserve >/dev/null 2>&1 ||:

# Run these because the SysV package being removed won't do them
/sbin/chkconfig --del portreserve >/dev/null 2>&1 || :
/bin/systemctl try-restart portreserve.service >/dev/null 2>&1 || :

%files
%defattr(-,root,root)
%doc ChangeLog README COPYING NEWS
%dir %{_localstatedir}/run/portreserve
%dir %{_sysconfdir}/portreserve
%config %{_tmpfilesdir}/portreserve.conf
%{_unitdir}/portreserve.service
/sbin/*
%{_mandir}/*/*

%changelog
* Thu Jun 30 2016 Tim Waugh <twaugh@redhat.com> - 0.0.5-11
- Enabled hardened build (bug #1092563).

* Fri Jan 24 2014 Daniel Mach <dmach@redhat.com> - 0.0.5-10
- Mass rebuild 2014-01-24

* Fri Dec 27 2013 Daniel Mach <dmach@redhat.com> - 0.0.5-9
- Mass rebuild 2013-12-27

* Tue Nov 26 2013 Tim Waugh <twaugh@redhat.com> - 0.0.5-8
- Avoid a race during start-up if there are no configured ports (bug #1034139).
- Moved tmpfiles configuration file to correct location.
- Don't use %ghost in manifest for state directory, in order to make
  sure it is ready to use after installation.

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.5-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Tue Aug 21 2012 Tim Waugh <twaugh@redhat.com> 0.0.5-6
- Use macroized systemd scriptlets (bug #850275).

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.5-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.5-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Jul 12 2011 Tim Waugh <twaugh@redhat.com> 0.0.5-3
- Converted initscript to systemd service file (bug #617331).

* Fri Jul  1 2011 Tim Waugh <twaugh@redhat.com> 0.0.5-2
- Requires chkconfig (bug #718173).

* Fri Jun 24 2011 Tim Waugh <twaugh@redhat.com> 0.0.5-1
- 0.0.5 (bug #619089, bug #704567).

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.0.4-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Dec  2 2010 Tim Waugh <twaugh@redhat.com> 0.0.4-7
- /var/run changes for systemd (bug #656670).

* Thu Nov 18 2010 Tim Waugh <twaugh@redhat.com> 0.0.4-6
- Fixed initscript exit code for "status" action (bug #619089).

* Thu Mar  4 2010 Tim Waugh <twaugh@redhat.com> 0.0.4-5
- Added comments to all patches.

* Fri Jan 22 2010 Tim Waugh <twaugh@redhat.com> 0.0.4-4
- Walk the list of newmaps correctly (bug #557781).

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
