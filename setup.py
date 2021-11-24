# -*- coding: utf-8 -*-

from codecs import open
from setuptools import setup, find_packages
import re

with open('osmapi/__init__.py', 'r') as fd:
    version = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
                        fd.read(), re.MULTILINE).group(1)

if not version:
    raise RuntimeError('Cannot find version information')

with open('README.md', 'r', encoding="utf-8") as f:
    long_description = f.read()

setup(
    name='osmapi',
    packages=find_packages(),
    version=version,
    install_requires=['requests'],
    description='Python wrapper for the OSM API',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Etienne Chové',
    author_email='chove@crans.org',
    maintainer='Stefan Oderbolz',
    maintainer_email='odi@metaodi.ch',
    url='https://github.com/metaodi/osmapi',
    download_url='https://github.com/metaodi/osmapi/archive/v%s.zip' % version,
    keywords=['openstreetmap', 'osm', 'api'],
    license='GPLv3',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Software Development :: Libraries',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
