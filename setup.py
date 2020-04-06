#!/usr/scripts/env python
"""
BrkAnalysis: Python-based online fMRI analysis tool for Bruker preclinical MRI scanner
"""
from distutils.core import setup
from setuptools import find_packages
import re, io

__version__ = re.search(
    r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
    io.open('brkfmri/__init__.py', encoding='utf_8_sig').read()
    ).group(1)

__author__ = 'SungHo Lee'
__email__ = 'shlee@unc.edu'
__url__ = 'https://github.com/dvm-shlee/brk-fmri'

setup(name='bruker-fmri',
      version=__version__,
      description='Python-based online fMRI analysis tool for Bruker preclinical MRI scanner',
      python_requires='>3.5, <3.8',
      author=__author__,
      author_email=__email__,
      url=__url__,
      license='GNLv3',
      packages=find_packages(),
      install_requires=['numpy',
                        'shleeh',
                        'bruker',
                        'PySide2',
                        'pyqtgraph==0.11.0rc0'],
      entry_points={
          'console_scripts': [
              'brk-fmri=brkfmri.scripts.brkfmri:main',
          ],
      },
      classifiers=[
          # How mature is this project? Common values are
          'Development Status :: 1 - Planning',
          'Environment :: X11 Applications :: Qt',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Operating System :: MacOS',
          'Operating System :: Microsoft :: Windows :: Windows 10',
          'Programming Language :: Python :: 3.7',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'Topic :: Scientific/Engineering :: Medical Science Apps.',
      ],
      keywords = 'bruker data_handler converter administrator_tool'
     )
