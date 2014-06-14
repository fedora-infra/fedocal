%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from
%distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:           fedocal
Version:        0.7
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
BuildRequires:  python-fedora >= 0.3.33
BuildRequires:  python-fedora-flask >= 0.3.33
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

sed -i -e 's|script_location = alembic|script_location = /usr/share/fedocal/alembic|' alembic.ini.sample

%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Install apache configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/
install -m 644 fedocal.conf $RPM_BUILD_ROOT/%{_sysconfdir}/httpd/conf.d/fedocal.conf

# Install configuration file
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal
install -m 644 fedocal.cfg.sample $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal/fedocal.cfg
install -m 644 alembic.ini.sample $RPM_BUILD_ROOT/%{_sysconfdir}/fedocal/alembic.ini

# Install WSGI file
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/fedocal
cp -r alembic/ $RPM_BUILD_ROOT/%{_datadir}/fedocal/
install -m 644 fedocal.wsgi $RPM_BUILD_ROOT/%{_datadir}/fedocal/fedocal.wsgi

# Install the createdb script
install -m 644 createdb.py $RPM_BUILD_ROOT/%{_datadir}/fedocal/fedocal_createdb.py


%files
%doc README.rst LICENSE doc/
%config(noreplace) %{_sysconfdir}/httpd/conf.d/fedocal.conf
%config(noreplace) %{_sysconfdir}/fedocal/fedocal.cfg
%config(noreplace) %{_sysconfdir}/fedocal/alembic.ini
%dir %{_sysconfdir}/fedocal/
%{_datadir}/fedocal/
%{python_sitelib}/fedocal/
%{python_sitelib}/fedocal*.egg-info
%{_bindir}/fedocal_cron.py


%changelog
* Sat Jun 14 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.7-1
- Update to 0.7
- Rework the meeting detail view
- Add date/time in UTC as titles to the dates on the meeting detail view
- Add shortcuts to interact more easily with the calendars (calendar and
  list views)
- Fix bug in recursive meetings
- Add notifications informing if there are meetings hidden below or above the
  current view
- Add permalink allowing one to copy/paste the url and send it to someone else
- Add countdown on the meeting detail view
- Auto-scroll to today or the future meetings in the list view
- Bug fix in displaying the full day meetings
- Add a dedicated field to set the address used to send fedocal reminder
- Embed the background image in the sources to fix complaints when using https

* Sat May 03 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6.3-1
- Security update, prevent fedocal to redirect to malicious website

* Wed Apr 23 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6.2-1
- Update to 0.6.2
- Fix cron job

* Fri Apr 18 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6.1-1
- Update to 0.6.1
- Use cantarell as default font
- Highlight the current calendar in the list
- Forbid `#` in meeting location
- Fix fedmsg messages to avoid empty meeting_id
- Fix editing one's meeting

* Wed Mar 12 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.6.0-1
- Update to 0.6.0
- CSS fix in the monthly calendar
- Use custom timezone ID in the ical output which should fix importing the iCal
  feed into google calendar or evolution
- Revert the meaning of the orange week in the monthly calendar

* Tue Mar 04 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5.1-1
- Update to 0.5.1
- Fix the link in the reminder email sent (does not hardcode the url anymore and
  has the appropriate meeting id)

* Tue Mar 04 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.5.0-1
- Update to 0.5.0
- Rework the monthly calendar
- Add a list view to locations
- Fix visualization of full day meeting over multiple days

* Wed Feb 26 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.7-1
- Update to 0.4.7
- Add the 3 and 4 weeks recursion frequency

* Thu Feb 13 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.6-1
- Update to 0.4.6
- Bug fix release fixing bug in the propagation of the manager in recurrent
  meetings

* Sat Feb 08 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.5-1
- Update to 0.4.5
- Bug fix release fixing bug in the reminder/fedmsg msg for recursive meetings

* Thu Jan 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.4-1
- Update to 0.4.4
- Bug fix release fixing bug when editing recursive meeting that have never
  occured so far

* Thu Jan 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.3-1
- Update to 0.4.3
- Bug fix release fixing bug when deleting recursive meeting that have never
  occured so far

* Thu Jan 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.2-1
- Update to 0.4.2
- Bug fix release fixing bug in the iCal output

* Thu Jan 30 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.1-1
- Update to 0.4.1

* Tue Jan 28 2014 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.4.0-1
- Update to 0.4.0

* Fri Nov 15 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.1-1
- Update to 0.3.1

* Thu Nov 14 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.3.0-1
- Update to 0.3.0
- Move the createdb script into %%{_datadir}/fedocal/

* Mon Oct 28 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.9-1
- First pre-release before 0.3.0

* Fri Sep 27 2013 Pierre-Yves Chibon <pingou@pingoured.fr> - 0.2.0-1
- Update to release 0.2.0

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.1.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

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

