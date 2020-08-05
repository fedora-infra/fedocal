""" This is an utility module for sending notifications via fedora-messaging

  :Author: Ralph Bean <rbean@redhat.com>
  :Author: Pierre-Yves Chibon <pingou@pingoured.fr>

"""
from __future__ import unicode_literals, absolute_import

import logging

import fedora_messaging.api
from fedora_messaging.exceptions import PublishReturned, ConnectionException


_log = logging.getLogger(__name__)


def publish(topic, msg):  # pragma: no cover
    _log.debug('Publishing a message for %r: %s', topic, msg)
    try:
        message = fedora_messaging.api.Message(
            topic='fedocal.%s' % topic,
            body=msg
        )
        fedora_messaging.api.publish(message)
        _log.debug("Sent to fedora_messaging")
    except PublishReturned as e:
        _log.exception(
            'Fedora Messaging broker rejected message %s: %s',
            message.id, e)
    except ConnectionException as e:
        _log.exception('Error sending message %s: %s', message.id, e)