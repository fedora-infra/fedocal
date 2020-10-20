""" This is an utility module for sending notifications via fedora-messaging

  :Author: Ralph Bean <rbean@redhat.com>
  :Author: Pierre-Yves Chibon <pingou@pingoured.fr>

"""
from __future__ import unicode_literals, absolute_import

import logging

import fedora_messaging.api
from fedora_messaging.exceptions import PublishReturned, ConnectionException

import fedocal_messages
import fedocal_messages.messages as schema


_log = logging.getLogger(__name__)


def publish(topic, msg):  # pragma: no cover
    _log.debug('Publishing a message for %s: %s', topic, msg)
    try:

        msg_cls = fedocal_messages.get_message_object_from_topic(
            'fedocal.%s' % topic
        )

        if not hasattr(msg_cls, "app_name") is False:
            _log.warning(
                "fedocal is about to send a message that has no schemas: %s",
                topic
            )

        message = msg_cls(body=msg)
        fedora_messaging.api.publish(message)
        _log.debug("Sent to fedora_messaging")
    except PublishReturned as e:
        _log.exception(
            'Fedora Messaging broker rejected message %s: %s',
            message.id, e)
    except ConnectionException as e:
        _log.exception('Error sending message %s: %s', message.id, e)
