#
# Copyright 2015 University of Southern California
# Distributed under the Apache License, Version 2.0. See LICENSE for more info.
#

""" Installation script for the encode2bag utility.
"""

from setuptools import setup, find_packages

setup(
    name="encode2bag",
    description="ENCODE to BDBag Utility",
    url='https://github.com/ini-bdds/encode2bag/',
    maintainer='USC Information Sciences Institute ISR Division',
    maintainer_email='misd-support@isi.edu',
    version="0.1.0",
    packages=find_packages(),
    test_suite='test',
    entry_points={
        'console_scripts': [
            'encode2bag = encode2bag.encode2bag_cli:main'
        ]
    },
    requires=[
        'argparse',
        'os',
        'sys',
        'platform',
        'logging',
        'json',
        'shutil',
        'tempfile',
        'urlparse'],
    install_requires=['requests',
                      'certifi',
                      'bdbag==0.8.8'],
    dependency_links=[
         "http://github.com/ini-bdds/bdbag/archive/master.zip#egg=bdbag-0.8.8"
    ],
    license='Apache 2.0',
    classifiers=[
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ]
)

