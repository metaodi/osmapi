#-*- coding: utf-8 -*-

import os

version = __import__('osmapi').__version__
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__))
)

try:
    import pypandoc
    description = pypandoc.convert(
        os.path.join(__location__, 'README.md'), 'rst'
    )
except (IOError, ImportError):
    description = 'Python wrapper for the OSM API'

from distutils.core import setup
setup(
    name='osmapi',
    packages=['osmapi'],
    version=version,
    description='Python wrapper for the OSM API',
    long_description=description,
    author=u'Etienne Chové',
    author_email='chove@crans.org',
    maintainer='Stefan Oderbolz',
    maintainer_email='odi@readmore.ch',
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
    ],
)
