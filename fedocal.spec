%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           fedocal
Version:        0.1.0
Release:        2%{?dist}
Summary:        A web based calendar application

License:        GPLv3+
URL:            http://fedorahosted.org/fedocal/
Source0:        https://fedorahosted.org/releases/f/e/fedocal/%{name}-%{version}.tar.gz

BuildArch:      noarch

BuildRequires:  python2-devel
BuildRequires:  python-flask
BuildRequires:  python-sqlalchemy
BuildRequires:  pytz
BuildRequires:  python-wtforms
BuildRequires:  python-flask-wtf
BuildRequires:  python-vobject
BuildRequires:  python-kitchen
BuildRequires:  python-fedora
BuildRequires:  python-fedora-flask
BuildRequires:  python-alembic
BuildRequires:  python-dateutil <= 1.5
BuildRequires:  python-setuptools

Requires:  python-flask
Requires:  python-sqlalchemy
Requires:  pytz
Requires:  python-wtforms
Requires:  python-flask-wtf
Requires:  python-vobject
Requires:  python-kitchen
Requires:  python-fedora
Requires:  python-fedora-flask
Requires:  python-alembic
Requires:  python-dateutil <= 1.5
Requires:  python-setuptools
Requires:  mod_wsgi

%description
fedocal is a web- based calendar application for Fedora. It aims at replacing
the tables in the wiki which are hard to edit and maintain.
Calendar can be exported to an iCal format allowing read-only integration with
most calendar application.

%prep
%setup -q

rm fedocal/flask_fas.py

%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Install wsgi, apache configuration and fedocal configuration files
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 fedocal.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/fedocal.conf

install -m 644 fedocal.wsgi $RPM_BUILD_ROOT/%{python_sitelib}/fedocal/fedocal.wsgi

mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal
install -m 644 fedocal.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal/fedocal.cfg


%files
%doc README.rst LICENSE doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/fedocal.conf
%config(noreplace) %{_sysconfdir}/fedocal/fedocal.cfg
%dir %{_sysconfdir}/fedocal/
%{python_sitelib}/fedocal/
%{python_sitelib}/fedocal*.egg-info


%changelog
* Tue Feb 26 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-2
- Fix BR to python2-devel
- Be more specific on the %%{python_sitelib} inclusion in %%files
- Remove flask_fas for a BR and R on python-fedora-flask

* Fri Feb 15 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.1.0-1
- Initial packaging work for Fedora

