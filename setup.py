from setuptools import setup, find_packages


setup(
    name='docker-bootstrap',
    version='0.0.3',
    description='Docker container bootstrapper',
    packages=find_packages(),
    install_requires=['jinja2', 'pyaml'],
    package_data={
        'docker_bootstrap': ['templates/*.jinja2']
    }
)
