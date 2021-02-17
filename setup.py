#!/usr/bin/env python

import os
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

README = open(os.path.join(HERE, 'README.md')).read()
CHANGES = open(os.path.join(HERE, 'CHANGES.md')).read()

setup(
    name='terra-opp',
    version=open(os.path.join(HERE, 'terra_opp', 'VERSION.md')).read().strip(),
    include_package_data=True,
    author="Makina Corpus",
    author_email="terralego-pypi@makina-corpus.com",
    description='Observatoire Photographique des Paysages',
    long_description=README + '\n\n' + CHANGES,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    url='https://github.com/Terralego/terra-opp.git',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=[
        'Django>=2.2',
        'djangorestframework',
        'coreapi',
        'coreschema',
        'djangorestframework-gis',
        'django-url-filter',
        'django-geostore>=0.3.15',
        'django-datastore>=0.1.1,<0.2',
        'django-terra-accounts>=0.3.11',
        "django-terra-settings",
        "psycopg2>=2.7",
        "django-versatileimagefield",
        "weasyprint",
        "django-filter",
    ],
    extras_require={
        'dev': [
            'factory-boy',
            'flake8',
            'black',
            'coverage',
        ]
    }
)
