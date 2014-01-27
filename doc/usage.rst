Usage
=====

Users
-----

Fedocal has basically four levels for the users:

 - administrators
 - calendar administrators
 - calendar managers
 - users



Administrators
~~~~~~~~~~~~~~

Administrators are people with an account on the
`Fedora account system (FAS) <https://admin.fedoraproject.org/accounts/>`_ and
belong the administrator group as set in the :doc:`configuration`.

Administrators are the only people allowed to create a calendar and edit/delete
meetings in all calendar.



Calendar administrators
~~~~~~~~~~~~~~~~~~~~~~~

Calendar administrators are set when the calendar is created. They are the members
of the FAS group set as `Admin group` when the calendar is created.

Administrators can edit and delete over all meetings of a calendar.



Calendar editors
~~~~~~~~~~~~~~~~~

Calendar editors are set when the calendar is created. They are the members of
the FAS group set as `Editor group` when the calendar is created.

Editors are used when one wants to restrict the edition (adding meetings)
of the calendar to members of a certain group.



Users
~~~~~

Users are people with an account on the
`Fedora account system (FAS) <https://admin.fedoraproject.org/accounts/>`_ and
belong to at least one more group than the ``fedora_cla`` group which
every contributor should sign to contribute to Fedora.



.. _create_calendar:

Create calendar
---------------

After logging in, if you are in the administrator group, you will see an
``Admin`` entry in the top menu containing a link to ``Add calendar``.
Use this link to create a calendar.

The form to will ask for:

- ``calendar name``: the name of the calendar as used in the link and as title
  for this calendar.

- ``calendar contact``: an address email that will be publish as contact point
  for this calendar. This is not linked to :ref:`reminders` but it is more
  aimed at providing an email to people wanted to obtain information about a
  specific calendar.

- ``calendar description``: a short description of what the calendar is used for.
  This description will also show up on the page of the calendar and should
  thus not be too long.

- ``Editor groups``: the name of the
  `FAS <https://admin.fedoraproject.org/accounts/>`_
  group to which people should belong that will manage the calendar
  (ie: create meetings). This is used to restrict the creation of meetings
  in a calendar to a specific group.

- ``calendar admin group``: the name of the
  `FAS <https://admin.fedoraproject.org/accounts/>`_
  group to which people should belong that will administrate the calendar
  (ie: edit/delete meetings). This gives administrator privilege to a group
  of people but for this calendar only.

- ``calendar status``: the status of the calendar (ie: `Enabled` or `Disabled`).
  By default the calendar will be `Enabled`.


.. note:: To create a new calendar in the `Fedora instance of fedocal
          <https://apps.fedoraproject.org/calendar>`_ you will need to
          create a ticket on the `infrastructure trac
          <https://fedorahosted.org/fedora-infrastructure/>`_


Edit a calendar
---------------

One can edit a calendar if she/he is a fedocal administrator or a list
administrator as defined above.

To edit a calendar, select the calendar to edit in the left menu by
clicking on its name. Then go to the ``Admin`` entry of the main menu and
select ``Edit calendar``. Or via the ``Admin`` entry in the top menu, you may
specify via the drop-down list which calendar you want to edit.

When editing a calendar you will have the same field as when creating one
(see :ref:`create_calendar`).



Clear a calendar
----------------

From version 0.4.0 fedocal gives the option to clear a calendar of all its
meetings. Only admins (calendar admin and fedocal admin) can clear a calendar.
To do so, select the calendar to clear in the left menu by clicling on its name.
Then go to the ``Admin`` entry of the main menu and select ``Clear calendar``.

You will see a confirmation page where you will have to select the checkbox
to confirm clearing the Calendar of all its meetings.

.. note:: Once confirmed this operation cannot be un-done.



Delete a calendar
-----------------

One can edit a calendar if she/he is a fedocal administrator or a list
administrator as defined above.

To delete a calendar, select the calendar to delete in the left menu by
clicking on its name. Then go to the ``Admin`` entry of the left menu and
select ``Delete calendar``. Or via the ``Admin`` entry in the top menu, you may
specify via the drop-down list which calendar you want to delete.

You will see a confirmation page where you will have to select the checkbox
to confirm the deletion of the Calendar.

.. note:: Deletion of calendar is a permanent operation which will also
   destroy all meetings of the calendar. You will thus loose all the
   history of the calendar without possibility to undo it.



.. _create_meeting:

Create meeting
--------------

After logging in with your `FAS account
<https://admin.fedoraproject.org/accounts/>`_ you can create a meeting in
one of the available calendars.


When creating a meeting you will have to fill the form asking for:

- ``meeting name``: this is the name of the meeting has presented in main
  calendar as well as by email.

- ``meeting date``: the date at which the meeting will occur. If you use a
  browser with javascript enable you will have a pop-up enabling to choose
  the date in a calendar. Otherwise, you will have to provide the date using
  the format: ``yyyy-mm-dd``.

- ``meeting end date``: the date at which the meeting will end. If you use a
  browser with javascript enable you will have a pop-up enabling to choose
  the date in a calendar. Otherwise, you will have to provide the date using
  the format: ``yyyy-mm-dd``.

- ``meeting start time``: the time at which the meeting starts. It can be
  any time although the calendar will only displays half-hour time slots.
  It should be of the format: ``HH:MM``.

- ``meeting stop time``: the time at which the meeting stops. It can be
  any time although the calendar will only displays half-hour time slots.
  It should be of the format: ``HH:MM``.

- ``full day``: checkbox to specify that the meeting is full day. Full day
  meeting are recorded as being from the specified date midnight to the
  next day midnight, UTC times.

- ``meeting timezone``: the timezone in which to store the meeting. If stored in
  UTC the meeting time will change according to the `Daylight saving time (DST)
  <http://en.wikipedia.org/wiki/Daylight_saving_time>`_, if stored in a specific
  timezone the time will remain constant over the year despite of DST.

- ``meeting information``: this is a free-text field containing as much
  information as you wish about the meeting. This field support the
  `markdown syntax <http://daringfireball.net/projects/markdown/syntax>`_
  allowing formating the text and adding links.

- ``More information URL``: field explicitely asking to provide an URL where
  more information can be found about the meeting.
  This URL is then appended into the description.

- ``meeting location``: the location where this meeting will happen. This
  location can then be found via the `locations` entry in the top menu.

- ``meeting frequency``: for recursive meetings, you can set here the recursion
  frequency (7 days or 14 days).

- ``meeting recursion ends``: you may want to specify when the recursivity for
  this meeting should end (for example at the next election). If left empty a
  default end date will be used (in this case: 2025-12-31)

- ``remdind when``: you may want to set a reminder for your meeting this field
  allows you to specify when this reminder should be sent: 12 hours before, 24
  hours before, 48 hours before or 7 days before the start of the meeting.


  See the :ref:`reminders` section below for more information about the
  reminders.

- ``remind who``: this field allows you to specify the email addresses to which
  the reminder should be sent. Each email addresses should be separated by a
  coma.

  See the :ref:`reminders` section below for more information about the
  reminders.



Edit meeting
------------

One can only edit a meeting if he is one of the manager of the meeting or if
he is an administrator of fedocal.


In these cases, once logged-in, click on `My meetings` on the top menu bar or
on the top left corner on your nickname. This page will present a list of the
meetings for which you are a manager and that you can edit.


When editing a meeting you will have the same field as when creating one
(see :ref:`create_meeting`), plus the possibility to add co-managers to the
meeting.
When the meeting is recursive there will be three buttons at the bottom, one to
edit only this instance of the meeting, one to edit all future meeting in the
recursion and the cancel button.



Delete meeting
--------------

One can only delete a meeting if he is one of the manager of the meeting or if
he is an administrator of fedocal.


In these cases, once logged-in, go to the ``User`` section in the top menu and
select ``My meetings``. This page will present a list of the meetings for which
you are a manager and that you can delete.


You may also delete a meeting by clicking on the delete icon when viewing the
details of a meeting on the calendar view.


You will be asked to confirm the deletion of the meeting and for recursive
meetings you will have to specify if you want to delete all the future meetings
or just this one (default).



Upload an iCalendar file
------------------------

From version 0.4.0 fedocal supports the possibility to upload an iCalendar file
into an existing calendar. Only admins (calendar admin and fedocal admin) can
upload an iCalendar file. To do so, select the calendar in which to upload the
iCalendar file in the left menu (or in the front page) by clicling on its name.
Then go to the ``Admin`` entry of the main menu and select ``Upload iCalendar``.

You will see a page offering you the traditionnal button that allows to choose
which file to upload.

.. note:: Recurrent events are not supported (yet) in fedocal 0.4.0.

.. note:: TODO are converted into full-day meetings and displayed as such.



iCal feed
---------

Fedocal provides for each calendar an iCal feed allowing integration with your
own calendar application.

This iCal is read-only and can be found at::

 http://<url to fedocal>/ical/<calendar name>/

A general iCal feed is available for all the calendar at once at::

 http://<url to fedocal>/ical/



List view
---------

Sometime it is interesting to have an overview of all the meetings over
a given time period. The easiest way to achieve this is simply to have a
list of all the meetings in this period.

This list view can be found at::

 http://<url to fedocal>/list/<calendar name>/

This page can also be accessed from the main menu, for each calendar
under the `List view` link.

By default this will show you the list of all the meetings in the current
year, but you can restrict or change the period by specifying a year or
a year and a month or even a year, a month and a day::

 http://<url to fedocal>/list/<calendar name>/<year>/
 http://<url to fedocal>/list/<calendar name>/<year>/<month>/
 http://<url to fedocal>/list/<calendar name>/<year>/<month>/<day>/


From fedocal 0.4.0, a green line provides a visual indication of the meetings
which are in the past vs the meetings in the future. If there are meetings
planned on that day, they will appear with a salmonish background between a red
line delimiting meeting of the day from meetings from the past and the green
line mentionned above.


.. _reminders:

Reminders
---------

When creating a meeting you can set the option to send a reminder. You will be
asked for:

- ``when`` to send the reminder
- ``who`` to send the reminder to

The reminder is sent in the name of the person who created the meeting.

.. note:: when sending the reminder to a mailing-list, make sure that the
          person that created the meeting is registered to the list in order
          for the reminder to be allowed.

The reminder will be formated as such:

subject:

::

 [Fedocal] Reminder meeting : <meeting name>


content:

::

 Dear all,

 You are kindly invited to the meeting :
    <meeting name> on <meetin date> from <starting time> to <ending time> <meeting timezone>
    <at meeting location>

 The meeting will be about:
  <meeting description>

 Source: <url to the meeting in fedocal where more information can be found>

