# Docker bootstrapper for python projects

Helps setting up logging and rsyslogd.


## Usage:


```
import docker_bootstrap

docker_bootstrap.bootstrap(log_level='WARNING', logging_template=''
)
