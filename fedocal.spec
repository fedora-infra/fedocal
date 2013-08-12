%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           fedocal
Version:        0.2.0
Release:        1%{?dist}
Summary:        A web based calendar application

License:        GPLv3+
URL:            http://fedorahosted.org/fedocal/
Source0:        https://fedorahosted.org/releases/f/e/fedocal/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  pytz
BuildRequires:  python-wtforms
BuildRequires:  python-flask-wtf
BuildRequires:  python-vobject
BuildRequires:  python-kitchen
BuildRequires:  python-fedora >= 0.3.32.3-3
BuildRequires:  python-fedora-flask
BuildRequires:  python-alembic
BuildRequires:  python-dateutil <= 1.5
BuildRequires:  python-setuptools
BuildRequires:  python-markdown
BuildRequires:  python-docutils

# EPEL6
%if ( 0%{?rhel} && 0%{?rhel} == 6 )
BuildRequires:  python-sqlalchemy0.7
Requires:  python-sqlalchemy0.7
%else
BuildRequires:  python-sqlalchemy > 0.5
Requires:  python-sqlalchemy > 0.5
%endif

Requires:  python-flask
Requires:  pytz
Requires:  python-wtforms
Requires:  python-flask-wtf
Requires:  python-vobject
Requires:  python-kitchen
Requires:  python-fedora >= 0.3.32.3-3
Requires:  python-fedora-flask
Requires:  python-alembic
Requires:  python-dateutil <= 1.5
Requires:  python-setuptools
Requires:  python-markdown
Requires:  python-docutils
Requires:  mod_wsgi

%description
fedocal is a web- based calendar application for Fedora. It aims at replacing
the tables in the wiki which are hard to edit and maintain.
Calendar can be exported to an iCal format allowing read-only integration with
most calendar application.

%prep
%setup -q

%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Install wsgi, apache configuration and fedocal configuration files
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 fedocal.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/fedocal.conf

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal
install -m 644 fedocal.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal/fedocal.cfg
install -m 644 alembic.ini.sample $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal/alembic.ini

mkdir -p $RPM_BUILD_ROOT/%{_datadir}/fedocal
cp -r alembic/ $RPM_BUILD_ROOT/%{_datadir}/fedocal/
install -m 644 fedocal.wsgi $RPM_BUILD_ROOT/%{_datadir}/fedocal/fedocal.wsgi

%files
%doc README.rst LICENSE doc/
%doc createdb.py
%config(noreplace) %{_sysconfdir}/httpd/conf.d/fedocal.conf
%config(noreplace) %{_sysconfdir}/fedocal/fedocal.cfg
%config(noreplace) %{_sysconfdir}/fedocal/alembic.ini
%dir %{_sysconfdir}/fedocal/
%{_datadir}/fedocal/
%{python_sitelib}/fedocal/
%{python_sitelib}/fedocal*.egg-info
%{_bindir}/fedocal_cron.py


%changelog
* Mon Aug 12 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.0-1
- Update to release 0.2.0

* Fri Mar 15 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.2.-1
- Update to 0.1.2 which includes the alembic files

* Fri Mar 15 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.1.-1
- Update to 0.1.1
- Include the createdb.py script as %%doc
- Add the alembic.ini into /etc/fedocal

* Fri Mar 08 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-3
- Fix import of flask-fas which fixes build on EL6
- Fix Requires and BuilRequires for EL6

* Tue Feb 26 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-2
- Fix BR to python2-devel
- Be more specific on the %%{python_sitelib} inclusion in %%files
- Remove flask_fas for a BR and R on python-fedora-flask

* Fri Feb 15 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial packaging work for Fedora

