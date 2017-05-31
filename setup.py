"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

import re

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

def read(*names, **kwargs):
    with open(
        path.join(here, *names),
        encoding=kwargs.get("encoding", "utf-8")
    ) as fp:
        return fp.read()

def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='gnosis-contracts',

    version=find_version('src', 'gnosis_contracts', '__init__.py'),

    description='Gnosis contracts',
    long_description=read('README.md'), # TODO: convert to rst

    url='https://github.com/gnosis/gnosis-contracts',

    author='Stefan George',
    author_email='stefan@gnosis.pm',

    license='GPLv3',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='gnosis-contracts gnosis cryptocurrency ethereum contract',

    packages=find_packages(where='src'),
    package_dir={"": "src"},

    # See: https://packaging.python.org/en/latest/requirements.html
    install_requires=[
        'requests',
        'click',
        'mpmath',
        'pytest',
        'ethereum',
        'ethjsonrpc',
    ],

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'gnosis_contracts': ['**/*.sol'],
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    # data_files=[('my_data', ['data/data_file'])],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'gnosis-ethabi=ethabi:setup',
            'gnosis-ethdeploy=ethdeploy:setup',
        ],
    },
)
