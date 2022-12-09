#!/usr/bin/env python

from setuptools import setup
# from distutils.core import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='ffprobe3-python3',
    version='2.0.0',
    description="""A Python3 wrapper-library around the 'ffprobe' command-line program to extract metadata from media files or streams.""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Simon Hargreaves, Dheerendra Rathor, Mark Ma, James Boyden',
    author_email='jboy@jboy.me',
    maintainer='James Boyden',
    maintainer_email='jboy@jboy.me',
    url='https://github.com/jboy/ffprobe3-python3',
    packages=['ffprobe3'],
    keywords='ffmpeg, ffprobe, mpeg, mp4, media, audio, video, json, metadata',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3 :: Only',
        'Natural Language :: English',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Video',
    ])
