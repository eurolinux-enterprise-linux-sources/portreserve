Summary: TCP port reservation utility
Name: portreserve
Version: 0.0.4
Release: 0.1
License: GPLv2+
Group: System Environment/Daemons
URL: http://cyberelk.net/tim/portreserve/
Source0: http://cyberelk.net/tim/data/portreserve/stable/%{name}-%{version}.tar.bz2
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: xmlto

%description
The portreserve program aims to help services with well-known ports that
lie in the portmap range.  It prevents portmap from a real service's port
by occupying it itself, until the real service tells it to release the
port (generally in the init script).

%prep
%setup -q

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
if [ "$1" = 1 ]; then
  /sbin/chkconfig --add portreserve
fi

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
* Thu May  8 2008 Tim Waugh <twaugh@redhat.com>
- More consistent use of macros.
- Build requires xmlto.
- Don't use %%makeinstall.
- No need to run 'make check'.
- Default permissions for directories.
- Initscript should not be marked config.
- Fixed license tag.
- Better buildroot tag.

* Wed Sep  3 2003 Tim Waugh <twaugh@redhat.com>
- Initial spec file.
