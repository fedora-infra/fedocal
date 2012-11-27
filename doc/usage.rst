Usage
=====

Users
-----

Fedocal has basically two levels for the users:

 - administrators
 - users

Administrators
~~~~~~~~~~~~~~

Administrators are people with an account on the
`Fedora account system (FAS) <https://admin.fedoraproject.org/accounts/>`_ and
belong the administrator group as set in the :doc:`configuration`.

Administrators are the only people allowed to create a calendar and edit all
the meetings.


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
``Admin`` entry in the left menu containing a link to ``Create calendar``.
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

- ``calendar managers group``: the name of the
  `FAS <https://admin.fedoraproject.org/accounts/>`_
  group to which people should belong that will manage the calendar
  (ie: create meetings).

- ``multiple meetings``: by default a calendar does not allow someone to create
  a meeting or an event on a specific date if there is already something
  planned at that time that day. By turning on this option, the calendar will
  become less strict and allow multiple meetings at the same time on the same
  day. This option should remain off for calendars handling for example IRC
  meetings.  It should be turned on for calendar handling for example
  Ambassadors events where mutiple events can occur on the same day at
  different locations in the world.

- ``region meetings``: by default, you can not associate a meeting with a region,
  by turning on this option you can. This allows to "tag" a meeting or an event
  as concerning a specfic region and thus allows someone to check out only
  the meeting within his region.

  Regions are meant to be 'NA', 'APAC', 'EMEA', 'LATAM'.

  Note that this can also be used to filter meetings retrieved via the API.



Edit a calendar
---------------

One can edit a calendar if she/he is an administrator as defined
above.

To edit a calendar, select the calendar to edit in the main menu by
clicking on its name. Then go to the ``Admin`` entry of the main menu and
select ``Edit calendar``.

When editing a calendar you will have the same field as when creating one
(see :ref:`create_calendar`).



Delete a calendar
-----------------

One can always delete a calendar if she/he is an administrator as defined
above.

To delete a calendar, select the calendar to delete in the main menu by
clicking on its name. Then go to the ``Admin`` entry of the main menu and
select ``Delete calendar``.

You will see a confirmation page where you will have to select the checkbox
to confirm the deletion of the Calendar.

.. note:: Deletion of calendar is a permanent operation which will also
   destroy all meetings of the calendar. You will thus loose all the
   history of the calendar without possibility to undo it.



.. _create_meeting:

Create meeting
--------------

After logging in with your `FAS account
<https://admin.fedoraproject.org/accounts/>`_ you can create a meeting in one
of the available calendar. 


When creating a meeting you will have to fill the form asking for:

- ``meeting name``: this is the name of the meeting has presented in main
  calendar as well as by email.

- ``meetin date``: the date at which the meeting will occur. If you use a
  browser with javascript enable you will have a pop-up enabling to choose
  the date in a calendar. Otherwise, you will have to provide the date using
  the format: ``yyyy-mm-dd``.

- ``meeting start time``: the time at which the meeting starts. It can be
  any time although the calendar will only displays half-hour time slots.
  It should be of the format: ``HH:MM``.

- ``meeting stop time``: the time at which the meeting stops. It can be
  any time although the calendar will only displays half-hour time slots.
  It should be of the format: ``HH:MM``.

- ``co-manager``: by default the person creating the meeting is the manager of
  the meeting. However, sometime you want to allow someone else to manage
  the meeting as well. This field allows you to provide a comma separated
  list of people you trust to manage the meeting with you.

- ``meeting information``: this is a free-text field containing as much 
  information as you wish about the meeting.

- ``meeting region``: when the calendar supports it, you may associate your
  meeting with a world region (APAC, EMEA, LATAM, NA)

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


.. note:: After the text field where to enter the times will be the
   timezone in which those times should be entered. This timezone is
   retrieved from your account on the `FAS
   <https://admin.fedoraproject.org/accounts/>`_, otherwise the timezone
   is `UTC <http://en.wikipedia.org/wiki/Coordinated_Universal_Time>`_.



Edit meeting
------------

One can only edit a meeting if he is one of the manager of the meeting or if
he is an administrator of fedocal.


In these cases, once logged-in, go to the ``User`` section in the main
menu and select ``Manage your meetings``. This page will present a list
of the meetings for which you are a manager and that you can edit.


When editing a meeting you will have the same field as when creating one
(see :ref:`create_meeting`),plus when the meeting is recursive an option
to update all the future meetings or just this one (default).



Delete meeting
--------------

One can only delete a meeting if he is one of the manager of the meeting or if
he is an administrator of fedocal.


In these cases, once logged-in, go to the ``User`` section in the main
menu and select ``Manage your meetings``. This page will present a list
of the meetings for which you are a manager and that you can delete.


You will be asked to confirm the deletion of the meeting and for recursive
meetings you will have to specify if you want to delete all the future meetings
or just this one (default). 


For archives purposes, you can never delete meetings from the past.



iCal feed
---------

Fedocal provides for each calendar an iCal feed allowing integration with your
own calendar application.

This iCal is read-only and can be found at::

 http://<url to fedocal>/ical/<calendar name>/



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
    <meeting name> on <meetin date> from <starting time> to <ending time>

 The meeting will be about:
  <meeting description>


