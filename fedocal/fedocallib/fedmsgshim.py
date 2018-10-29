""" This is a temporary shim that allows fedmsg to be an optional dependency of
pkgdb.  If fedmsg is installed, these function calls will try to actually send
messages.  If it is not installed, it will return silently.

  :Author: Ralph Bean <rbean@redhat.com>

"""

import warnings


def publish(*args, **kwargs):  # pragma: no cover
    try:
        import fedmsg
        fedmsg.publish(*args, **kwargs)
    except Exception as err:
        warnings.warn(str(err))
