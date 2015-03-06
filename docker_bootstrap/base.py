# -*- coding: utf-8 -*-
'''
Prepare the config files for the other docker inhabitants starting from
the environment variables.
'''

import os
import time
import sys
import subprocess
from six import StringIO

from jinja2 import Environment, FileSystemLoader

SYSLOG_SOCKET = '/dev/log'

TEMPLATE_DIR = os.path.join(os.path.os.path.dirname(__file__), 'templates')

__all__ = ['setup_logging', 'bootstrap']


# These are also dupicated in templates
LOGGING_CONFIG_PATH = 'logging.conf'
RSYSLOG_CONFIG_PATH = '/rsyslog.conf'
RSYSLOG_PID_PATH = '/rsyslog.pid'


def get_logging_config(log_level=None, log_rsyslog=None, log_console=None):
    '''Generate logging config dict from template.'''
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('logging.conf.jinja2')
    config = template.render(
        log_level=log_level or os.environ.get('LOG_LEVEL') or 'INFO',
        log_rsyslog=log_rsyslog if log_rsyslog is not None else True,
        log_console=log_console if log_console is not None else False,
        syslog_socket=SYSLOG_SOCKET)
    return config


def logger_excepthook(exc_type, exc_value, exc_traceback):
    import logging
    logging.fatal('Unhandled exception',
                  exc_info=(exc_type, exc_value, exc_traceback))


def setup_logging(log_level=None, log_console=None, log_rsyslog=None):
    '''Configure the python logger from the python code.

    Use the `logging.conf` file created by `bootstrap`.

    Can also work when `bootstrap` hasn't been called yet (during tests).
    '''
    import logging.config
    import yaml
    if os.path.exists(LOGGING_CONFIG_PATH):
        with open(LOGGING_CONFIG_PATH, 'r') as f:
            logging_config = yaml.load(f)
    else:
        # Useful when testing, and we don't call bootstrap()
        logging.warning('no logging configuration found')
        logging_config = yaml.load(
            StringIO(
                get_logging_config(log_level=log_level,
                                   log_console=log_console,
                                   log_rsyslog=log_rsyslog)
            )
        )
    logging.config.dictConfig(logging_config)
    sys.excepthook = logger_excepthook


def setup_rsyslog_logging(log_level=None, logentries_token=None,
                          rsyslog_debug=None, rsyslog_config_path=None,
                          rsyslog_pid_path=None):
    '''Configures and spawns rsyslog. '''
    _rsyslog_config_path = rsyslog_config_path or RSYSLOG_CONFIG_PATH
    _rsyslog_pid_path = rsyslog_pid_path or RSYSLOG_PID_PATH
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('rsyslog.conf.jinja2')
    contents = template.render(
        logentries_token=logentries_token,
        syslog_socket=SYSLOG_SOCKET,
        rsyslog_debug=(rsyslog_debug if rsyslog_debug is not None
                       else os.environ.get('RSYSLOG_DEBUG', False))
    )

    with open(_rsyslog_config_path, 'w') as f:
        f.write(contents)

    # spawn rsyslog
    rsyslog = subprocess.Popen(['rsyslogd', '-i', _rsyslog_pid_path,
                                '-f', _rsyslog_config_path],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    print('Spawning rsyslog...')

    stdout, stderr = rsyslog.communicate()

    def print_rsyslog_streams():
        print('Rsyslogd stderr: {}'.format(stderr)) if stderr else None
        print('Rsyslogd stdout: {}'.format(stdout)) if stdout else None

    if rsyslog.returncode:
        print('Error spawning rsyslogd. Code: {}'.format(rsyslog.returncode))
        print_rsyslog_streams()
        sys.exit(1)

    for i in range(10):
        if os.path.exists(SYSLOG_SOCKET):
            break
        time.sleep(.2)
    else:
        print('Could not find rsyslog socket {}'.format(SYSLOG_SOCKET))
        print_rsyslog_streams()
        sys.exit(1)
    print('Rsyslogd successfully started.')
    print_rsyslog_streams()


def become_circusd():
    print('Bootstrapping done, spawning circusd')
    os.execlp('circusd', 'circusd', 'circus.ini')


def bootstrap(log_level=None, logentries_token=None, rsyslog_debug=False,
              console=False, rsyslog=True, circusd=True):
    '''Setup python logging, rsyslog and spawn circusd.

    Args:
      log_level: if not provided `LOG_LEVEL` env var is used
      logentries_token: token for logentries logging
      rsyslog_debug: make rsyslog log in a local file too. Can also be
        controlled through `RSYSLOG_DEBUG` env var
      rsyslog: configure and log to rsyslog
      console: log to console (default False)
    '''
    config = get_logging_config(log_level=log_level,
                                log_rsyslog=rsyslog,
                                log_console=console)
    with open(LOGGING_CONFIG_PATH, 'w') as f:
        f.write(config)
    if rsyslog:
        setup_rsyslog_logging(log_level=log_level,
                              rsyslog_debug=rsyslog_debug,
                              logentries_token=logentries_token)
    if circusd:
        become_circusd()
