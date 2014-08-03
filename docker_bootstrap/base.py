# -*- coding: utf-8 -*-
'''
Prepare the config files for the other docker inhabitants starting from
the environment variables.
'''

import os
import time
import sys
import subprocess

from jinja2 import Environment, FileSystemLoader

SYSLOG_SOCKET = '/dev/log'

TEMPLATE_DIR = os.path.join(os.path.os.path.dirname(__file__), 'templates')

__all__ = ['setup_logging', 'bootstrap']


def prepare_python_logging_config(log_level='INFO'):
    # create and write logging config file
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('logging.conf.jinja2')
    contents = template.render(log_level=log_level, syslog_socket=SYSLOG_SOCKET)

    with open('logging.conf', 'w') as f:
        f.write(contents)


def logger_excepthook(exc_type, exc_value, exc_traceback):
    import logging
    logging.fatal('Unhandled exception',
                  exc_info=(exc_type, exc_value, exc_traceback))


def setup_logging():
    import logging.config
    import yaml
    with open('logging.conf', 'r') as f:
        logging_config = yaml.load(f)
    logging.config.dictConfig(logging_config)
    sys.excepthook = logger_excepthook


def setup_rsyslog_logging(log_level, logentries_token=None,
                          rsyslog_debug=False):
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template('rsyslog.conf.jinja2')
    contents = template.render(logentries_token=logentries_token,
                               syslog_socket=SYSLOG_SOCKET,
                               rsyslog_debug=rsyslog_debug)

    with open('/rsyslog.conf', 'w') as f:
        f.write(contents)

    # spawn rsyslog
    rsyslog = subprocess.Popen(['rsyslogd', '-i', '/rsyslog.pid',
                                '-f', '/rsyslog.conf'],
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


def bootstrap(log_level='INFO', logentries_token=None, rsyslog_debug=False,
              rsyslog=True, logging=True, circusd=True):
    '''Setup python logging, rsyslog and spawn circusd.

    Args:
      log_level (default to `INFO`)
      logentries_token: token for logentries logging
      rsyslog_debug: debug rsyslog loggin logally
    '''
    if logging:
        prepare_python_logging_config(log_level=log_level)
    if rsyslog:
        setup_rsyslog_logging(log_level=log_level, rsyslog_debug=rsyslog_debug,
                              logentries_token=logentries_token)
    if circusd:
        become_circusd()
