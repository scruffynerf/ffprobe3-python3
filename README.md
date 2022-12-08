ffprobe3-python3 module
=======================

A Python3 wrapper-library around the `ffprobe` command-line program to extract
metadata from media files or streams.

(**Note:** This wrapper-library depends on the `ffprobe` command-line program
to extract metadata from media files or streams.  The `ffprobe` program must
be installed, with an `ffprobe` executable that can be found by searching the
`$PATH` environment variable.)

---

Example usage
-------------

```python
#!/usr/bin/env python3

import ffprobe3

# Function `ffprobe3.probe(path_to_media)` is the entry point to this module;
# it's the first function you want to call.

# Local media file:
ffprobe_output = ffprobe3.probe('media-file.mov')

# ... or, a remote video stream:
ffprobe_output = ffprobe3.probe('http://some-streaming-url.com:8080/stream')

# Examine the metadata in `ffprobe_output`:

# The "format" key in the parsed JSON becomes an `FFformat` instance:
media_format = ffprobe_output.format

# The size of the media in Bytes (if provided by `ffprobe`):
if media_format.size_B is not None:
    print("media size = %d Bytes" % int(media_format.size_B))

# For convenience & continuity with the previous code, the list attributes
# [`.attachment`, `.audio`, `.subtitle`, and `.video`] are also available
# in this new code version:
video_stream = ffprobe_output.video[0]  # assuming at least 1 video stream
audio_stream = ffprobe_output.audio[0]  # assuming at least 1 audio stream

# Previously, all 4 of these list attributes [`.attachment`, `.audio`,
# `.subtitle`, `.video`] contained instances of a single type `FFStream`
# (a class which had methods for all 4 kinds of stream, whether relevant
# to the actual kind of stream or not).
#
# But now in this new code version, each list attribute contains instances
# of only a *single specific derived class* of base class `FFstream`:
# - `FFattachmentStream`
# - `FFaudioStream`
# - `FFsubtitleStream`
# - `FFvideoStream`
#
# Each of these derived classes has only attributes & methods relevant to
# that kind of stream.

# Derived class `FFvideoStream` has a method `.get_frame_shape_as_ints()`,
# which returns the frame (width, height) in pixels as a pair of ints;
# or returns `None` upon any error:
video_frame_shape = video_stream.get_frame_shape_as_ints()
if video_frame_shape is not None:
    print("Video frame shape = (%d, %d)" % video_frame_shape)

# Derived class `FFaudioStream` has an attribute `.sample_rate_Hz`
# (which defaults to `None` if no value was provided by `ffprobe`):
if audio_stream.sample_rate_Hz is not None:
    print("Audio sample rate = %d Hz" % int(audio_stream.sample_rate_Hz))

# Which keys are in the dictionary of parsed JSON for this `FFaudioStream`?
print(audio_stream.keys())
```

---

Why does this fork exist?
-------------------------

The most recent PyPI release of Mark Ma's `ffprobe-python` is dated 2019-11-05
(more than 3 years ago).  Even the most recent Github commit is dated
2021-05-13.  If it's not dead, it's resting.  (Pining for the fjords?)

This fork fixes the following bugs / implements the following feature requests
that are "Open" issues on the `ffprobe-python` repo:

- [issue 2](https://github.com/gbstack/ffprobe-python/issues/2),
  [issue 16]( https://github.com/gbstack/ffprobe-python/issues/16):
  A request to handle "Chapters" in media files (which are already supported by
  the command-line `ffprobe` program; and which cause the `ffprobe-python` code
  to crash when it encounters them)
- [issue 4](https://github.com/gbstack/ffprobe-python/issues/4),
  [issue 16]( https://github.com/gbstack/ffprobe-python/issues/16):
  A suggestion to simplify the code by replacing the custom stream-parsing code
  with the JSON output already offered by the command-line `ffprobe` program.

Significant changes in this fork include:

- Fixed a few Python3 compatibility bugs in the pre-fork code.
- Re-wrote the ``ffprobe`` call to request & parse the ``json`` print-format.
- Re-wrote all client-facing parsed-ffprobe-output classes to wrap parsed JSON.
- Re-wrote the subprocess code to use convenient new Python3 library features.
- **No longer support Python 2 or Python3 < 3.3**.
- **Changed the client-facing API of functions & classes**.
- Support/allow remote media streams (as ``ffprobe`` program already does).
- Local-file-exists checks are optional (use ``verify_local_mediafile=False``).
- Handle "Chapters" in media.
- All parsed-ffprobe-output JSON-wrapper classes have introspection methods.
- Added several derived exception classes for more-informative error reporting.
- Documented the API (Sphinx/reST docstrings for modules, classes, methods).

**I renamed this forked repo to ``ffprobe3-python3``**, because:

- The client-facing API of functions & classes has changed; and
- The supported Python version has changed from Python2 to **Python3 >= 3.3**.

---

Where did this fork come from?
------------------------------

This forked repo began as a bug-fixing fork (and has since become
a **complete rewrite**) of package `ffprobe-python`, which is/was
maintained by Mark Ma:

- [https://pypi.org/project/ffprobe-python/](https://pypi.org/project/ffprobe-python/)
- [https://github.com/gbstack/ffprobe-python](https://github.com/gbstack/ffprobe-python)

In turn, `ffprobe-python` is a "maintained fork" of the original Python package
`ffprobe`, created by Simon Hargreaves:

- [https://pypi.org/project/ffprobe/](https://pypi.org/project/ffprobe/)

**NOTE:** There's *also* a PyPI package named `ffprobe3`, maintained
by Dheerendra Rathor, that appears to focus purely on porting the
original `ffprobe` module to Python3 (without fixing any other issues):

- [https://pypi.org/project/ffprobe3/](https://pypi.org/project/ffprobe3/)
- [https://github.com/DheerendraRathor/ffprobe3](https://github.com/DheerendraRathor/ffprobe3)

**This** forked repo is not related to that `ffprobe3` package at all.

---

Which versions of Python are supported?
---------------------------------------

The **minimum supported Python version** is **Python3 >= 3.3**.

Python 3.3 was released on 2012-09-29 (more than 10 years ago now!).
Setting Python 3.3 as the minimum allows us to use the following
convenient Python3 language & library features:

- `__qualname__` attribute for the qualified name of classes
   ([PEP 3155](https://peps.python.org/pep-3155/))
- `yield from`
  [syntax for generator delegation](https://docs.python.org/3/whatsnew/3.3.html#pep-380)
  ([PEP 380](https://peps.python.org/pep-0380/))
- `raise NewException() from None`
  [syntax for suppressing exception context](https://docs.python.org/3/whatsnew/3.3.html#pep-409-suppressing-exception-context)
  ([PEP 409](https://peps.python.org/pep-0409/))
- exception base class [`subprocess.SubprocessError`](https://docs.python.org/3/library/subprocess.html#exceptions)
- [`subprocess.DEVNULL`](https://docs.python.org/3/library/subprocess.html#subprocess.DEVNULL)
- the `timeout` argument to functions
  [`subprocess.check_call`](https://docs.python.org/3/library/subprocess.html#subprocess.check_call),
  [`subprocess.Popen.communicate`](https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate), and
  [`subprocess.Popen.wait`](https://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait)
- [function `shlex.quote`](https://docs.python.org/3/library/shlex.html#shlex.quote),
  if we ever need to shell-quote strings
- [function `shutil.which`](https://docs.python.org/3/library/shutil.html#shutil.which),
  if we ever want to guess what `Popen` will use
- [the `asyncio` module](https://docs.python.org/3/library/asyncio.html)
  ([initially a package on PyPI](https://pypi.org/project/asyncio/),
  before it was officially incorporated into the Python3 stdlib in Python 3.4),
  if we ever want to switch from `subprocess` to
  [`asyncio.subprocess`](https://docs.python.org/3/library/asyncio-subprocess.html)

---

License
-------

(The MIT License)

Copyright 2022 James Boyden <github@jboy.id.au>

Copyright 2013 Simon Hargreaves <simon@simon-hargreaves.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the Software), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED AS IS, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

