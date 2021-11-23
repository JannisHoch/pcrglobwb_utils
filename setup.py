#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

with open('requirements_dev.txt') as requirements_file:
    requirements = requirements_file.read()

setup_requirements = ['pytest-runner', ]

test_requirements = ['pytest>=3', ]

setup(
    author="Jannis M. Hoch",
    author_email='j.m.hoch@uu.nl',
    python_requires='>=3.7',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    description="Handy functions to work with PCR-GLOBWB input and output",
    entry_points={
        'console_scripts': [
            'pcru_eval_tims = pcrglobwb_utils.scripts.evaluate_tims:cli',
            'pcru_eval_poly = pcrglobwb_utils.scripts.evaluate_poly:main',
            'pcru_preprocess = pcrglobwb_utils.scripts.preprocessing:cli',
        ],
    },
    install_requires=requirements,
    license="GNU General Public License v3",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='pcrglobwb_utils',
    name='pcrglobwb_utils',
    packages=find_packages(include=['pcrglobwb_utils', 'pcrglobwb_utils.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://pcrglobwb-utils.readthedocs.io/',
    version='0.3.2',
    zip_safe=False,
)
