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


Create calendar
---------------

After logging in, if you are in the administrator group, you will see an
``Admin`` entry in the left menu containing a link to ``Create calendar``.
Use this link to create a calendar.

The form to will ask for:

- ``calendar name``: the name of the calendar as used in the link and as title
  for this calendar.

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


Create meeting
--------------


Edit meeting
------------

One can only edit a meeting if he is one of the manager of the meeting or if
he is an administrator of fedocal.


In these cases, once logged-in, go to the page ``Manage your meetings`` and
there is presented a list of the meetings for which you are a manager and that
you can edit.


When editing a meeting you will have the same field as when creating one,
plus when the meeting is recursive an option to update all the future meetings
or just this one (default).


Delete meeting
--------------

One can only delete a meeting if he is one of the manager of the meeting or if
he is an administrator of fedocal.


In these cases, once logged-in, go to the page ``Manage your meetings`` and
there is presented a list of the meetings for which you are a manager and that
you can delete.


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


