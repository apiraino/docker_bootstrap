# Docker bootstrapper for python projects

Helps setting up logging and rsyslogd.


## Usage:


```
from docker_bootstrap import boostrap

bootstrap(log_level='WARNING', logentries_token='adsf', rsyslog_debug=False)
```
