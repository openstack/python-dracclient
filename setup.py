import re

from setuptools import setup


with open('requirements.txt', 'r') as fp:
    install_requires = [re.split(r'[<>=]', line)[0]
                        for line in fp if line.strip()]


setup(
    name = 'python-dracclient',
    version = '0.0.3',
    description = 'Library for managing machines with Dell iDRAC cards.',
    author = 'Imre Farkas',
    author_email = 'ifarkas@redhat.com',
    url = 'https://github.com/ifarkas/python-dracclient',
    packages = ['dracclient'],
    install_requires = install_requires,
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Environment :: OpenStack',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7'
    ],
    license = 'APL 2.0',
)
