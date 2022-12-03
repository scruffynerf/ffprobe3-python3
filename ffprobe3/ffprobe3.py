"""
A Python3 wrapper-library around the ``ffprobe`` command-line program.

Example usage::

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
    # Each of these derived classes only has attributes & methods relevant to
    # that kind of stream.

    # The total size of the media in Bytes (if provided by `ffprobe`):
    if media_format.size_B is not None:
        media_format_size_B = int(media_format.size_B)

    # Derived class `FFvideoStream` has a method `.get_frame_shape_as_ints()`,
    # which returns the frame (width, height) in pixels as a pair of ints;
    # or returns `None` upon any error:
    video_frame_shape = video_stream.get_frame_shape_as_ints()
    if video_frame_shape is not None:
        video_frame_shape = '%d,%d' % video_frame_shape

    # Derived class `FFaudioStream` has an attribute `.sample_rate_Hz`
    # (which defaults to `None` if no value was provided by `ffprobe`):
    if audio_stream.sample_rate_Hz is not None:
        audio_stream_sample_rate_Hz = int(audio_stream.sample_rate_Hz)

    # Which keys are in the dictionary of parsed JSON for this `FFaudioStream`?
    print(audio_stream.keys())

(**Note:** This wrapper-library depends on the ``ffprobe`` command-line program
to extract metadata from media files or streams.  The ``ffprobe`` program must
be installed, with an ``ffprobe`` executable that can be found by searching the
``$PATH`` environment variable.)

This package is a fork (actually now a complete rewrite) of package
``ffprobe-python`` which is/was maintained by Mark Ma:

- https://pypi.org/project/ffprobe-python/
- https://github.com/gbstack/ffprobe-python

Significant changes in this fork include:

- Fixed a few Python3 compatibility bugs in the pre-fork code.
- Re-wrote the ``ffprobe`` call to request & parse the ``json`` print-format.
- Re-wrote all client-facing parsed-ffprobe-output classes to wrap parsed JSON.
- Re-wrote the subprocess code to use convenient new Python3 library features.
- **No longer support Python 2 or Python3 < 3.3**.
- **Changed the client-facing API of functions & class-names**.
- Added optional sanity-checking code (disabled using ``verify_`` switches).
- Added several derived exception classes for more-informative error reporting.
- Support remote media streams (as the ``ffprobe`` program already does).
- Handle "Chapters" in media.

Read the updated ``README.md`` file for a longer list of changes & reasons.
"""

import json
import os
import subprocess

from .exceptions import *


# A list, so you can modify the command-line arguments if you really insist.
# Don't shoot yourself in the foot!
_SPLIT_COMMAND_LINE = [
        'ffprobe',
        '-v',
        # Use log-level (flag == '-v') of 'error' rather than 'quiet'
        # so that `ffprobe` at least reports a single-line error message
        # in the case of failure.
        'error', #'quiet',
        '-print_format',
        'json',
        '-show_chapters',
        '-show_format',
        '-show_streams',
]


def probe(path_to_media, *,
        communicate_timeout=10.0,  # a timeout in seconds
        ffprobe_cmd_override=None,
        verify_ffprobe_found=True,
        verify_mediafile_found=True):
    """
    Wrap the ``ffprobe`` command; parse the ffprobe JSON output into dicts.

    **Note:** This function is the entry point to this module;
    it's the first function you want to call.  This function will return
    a valid, appropriately-populated instance of class :class:`FFprobe`
    (or raise some derived class of the exception base class
    :class:`ffprobe3.exceptions.FFprobeError` trying).

    Args:
        path_to_media (str):
            full-path to local media or URI of remote media to probe
        communicate_timeout (positive float, optional):
            a timeout in seconds for ``subprocess.Popen.communicate``
        ffprobe_cmd_override (str, optional):
            a command to invoke instead of the default ``"ffprobe"``
        verify_ffprobe_found (bool, optional):
            verify ffprobe command can be found in ``$PATH`` (sanity check)
        verify_mediafile_found (bool, optional):
            verify `path_to_media` exists as a local file (sanity check)

    Returns:
        a new instance of class :class:`FFprobe`

    Raises:
        FFprobeError: the base class of all exception classes in this package
        FFprobeExecutableError: ffprobe command not found in ``$PATH``
        FFprobeInvalidArgumentError: invalid value to `communicate_timeout`
        FFprobeJsonParseError: JSON parser was unable to parse ffprobe output
        FFprobeMediaFileError: specified local media file does not exist
        FFprobeOverrideFileError: `ffprobe_cmd_override` command not found
        FFprobePopenError: ``subprocess.Popen`` failed, raised an exception
        FFprobeSubprocessError: ffprobe command returned non-zero exit status

    Example usage::

        import ffprobe3

        # Local media file
        ffprobe_output = ffprobe3.probe('media-file.mov')

        # or, Remote video stream
        ffprobe_output = ffprobe3.probe('http://some-streaming-url.com:8080/stream')
    """

    split_cmdline = list(_SPLIT_COMMAND_LINE)  # Roger, copy that.
    ffprobe_cmd = split_cmdline[0]

    if ffprobe_cmd_override is not None:
        if not os.path.isfile(ffprobe_cmd_override):
            raise FFprobeOverrideFileError(ffprobe_cmd_override)
        else:
            ffprobe_cmd = ffprobe_cmd_override
            split_cmdline[0] = ffprobe_cmd_override

    if communicate_timeout is not None:
        # Verify that this non-None value is some kind of positive number.
        if not isinstance(communicate_timeout, (int, float)):
            raise FFprobeInvalidArgumentError('communicate_timeout',
                    'Supplied timeout is non-None and non-numeric',
                    communicate_timeout)
        if communicate_timeout <= 0.0:
            raise FFprobeInvalidArgumentError('communicate_timeout',
                    'Supplied timeout is non-None and non-positive',
                    communicate_timeout)

    # Verify that the `ffprobe` command can be found in the $PATH.
    # We perform this by default as a helpful safety/sanity check.
    if verify_ffprobe_found:
        try:
            # From the docs for `subprocess.check_call`:
            #  https://docs.python.org/3/library/subprocess.html#subprocess.check_call
            #   '''
            #   Wait for command to complete. If the return code was zero
            #   then return, otherwise raise `CalledProcessError`.
            #   The `CalledProcessError` object will have the return code
            #   in the `returncode` attribute. If `check_call()` was unable
            #   to start the process it will propagate the exception that
            #   was raised.
            #   '''
            #
            # Docs for exception `subprocess.CalledProcessError`:
            #  https://docs.python.org/3/library/subprocess.html#subprocess.CalledProcessError
            subprocess.check_call(
                    [ffprobe_cmd, '-h'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
        except FileNotFoundError as e:
            raise FFprobeExecutableError(ffprobe_cmd) from e
        except subprocess.CalledProcessError as e:
            raise FFprobeSubprocessError(split_cmdline, e.returncode) from e

    # Verify that the specified media exists as a local file.
    # We perform this by default as a helpful safety/sanity check.
    #
    # But it's an optional check, to allow `ffprobe` to access files
    # over HTTP or FTP -- as requested in this issue, for example:
    #  https://github.com/gbstack/ffprobe-python/issues/4
    if verify_mediafile_found:
        if not os.path.isfile(path_to_media):
            raise FFprobeMediaFileError(path_to_media)

    # NOTE #1: Python3 docs say that its `Popen` does not call a system shell:
    #  https://docs.python.org/3/library/subprocess.html#security-considerations
    #   '''
    #   Security Considerations
    #
    #   Unlike some other popen functions, this implementation will never
    #   implicitly call a system shell. This means that all characters,
    #   including shell metacharacters, can safely be passed to child
    #   processes.
    #   '''
    #
    # So we should not need to shell-quote the command-line arguments.
    #
    # NOTE #2: I found some info about command-line arguments on Windows:
    #  https://docs.python.org/3/library/subprocess.html#converting-argument-sequence
    #
    # But I don't use Windows, so I can't test anything, sorry...
    split_cmdline.append(path_to_media)

    try:
        # https://docs.python.org/3/library/subprocess.html#subprocess.Popen
        proc = subprocess.Popen(split_cmdline,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True)
    # We catch the following plausible exceptions specifically,
    # in case we decide that we want to process any of them specially.
    except OSError as e:
        # https://docs.python.org/3/library/subprocess.html#exceptions
        #   '''
        #   The most common exception raised is `OSError`. This occurs,
        #   for example, when trying to execute a non-existent file.
        #   '''
        raise FFprobePopenError(e, 'OSError') from e
    except ValueError as e:
        #   '''
        #   A `ValueError` will be raised if `Popen` is called with
        #   invalid arguments.
        #   '''
        raise FFprobePopenError(e, 'ValueError') from e
    except subprocess.SubprocessError as e:
        #   '''
        #   Exceptions defined in this module all inherit from
        #   `SubprocessError`.
        #
        #   New in version 3.3: The `SubprocessError` base class was added.
        #   '''
        raise FFprobePopenError(e, 'subprocess.SubprocessError') from e

    # NOTE #3: We allow the caller of this constructor to specify remote
    # media files at HTTP or FTP URIs, which might be very slow if there
    # are network problems.
    #
    # Hence, we specify a `timeout` argument to the following subprocess
    # function (a timeout value which may be configured by the caller
    # using the optional parameter `communicate_timeout`).
    #
    # NOTE #4: We use `Popen.communicate` rather than `Popen.wait`,
    # because as the docs for `Popen.wait` warn us:
    #  https://docs.python.org/3/library/subprocess.html#subprocess.Popen.wait
    #   '''
    #   Note: This will deadlock when using `stdout=PIPE` or `stderr=PIPE`
    #   and the child process generates enough output to a pipe such that
    #   it blocks waiting for the OS pipe buffer to accept more data.
    #   Use `Popen.communicate()` when using pipes to avoid that.
    #   '''
    #
    # The docs for `Popen.communicate` helpfully provide the code idiom
    # that we should use here:
    #  https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
    #   '''
    #   If the process does not terminate after `timeout` seconds,
    #   a `TimeoutExpired` exception will be raised. Catching this
    #   exception and retrying communication will not lose any output.
    #
    #   The child process is not killed if the timeout expires, so
    #   in order to cleanup properly a well-behaved application should
    #   kill the child process and finish communication:
    #   '''
    try:
        (outs, errs) = proc.communicate(timeout=communicate_timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        (outs, errs) = proc.communicate()
    # Because we specified `universal_newlines=True` to `subprocess.Popen`,
    # `outs` & `errs` are text strings.
    #
    # XXX: I'm using `Popen.communicate`; so this function will close the
    # pipes for me automatically, right?  Because `Popen.communicate` waits
    # for the process to terminate?  Meaning it internally calls `Popen.wait`
    # or something similar?  Which closes the pipes?  I'm just being extra
    # careful, because the docs are not entirely clear on the matter:
    #   '''
    #   Read data from stdout and stderr, until end-of-file is reached.
    #   Wait for process to terminate and set the `returncode` attribute.
    #   '''
    # and:
    #   '''
    #   The child process is not killed if the timeout expires, so in order
    #   to cleanup properly a well-behaved application should kill the
    #   child process and finish communication:
    #   '''

    try:
        parsed_json = json.loads(outs)
    except json.decoder.JSONDecodeError as e:
        raise FFprobeJsonParseError(e, 'json.decoder.JSONDecodeError') from e
    exit_status = proc.returncode
    if exit_status != 0:
        raise FFprobeSubprocessError(split_cmdline, exit_status, errs)

    return FFprobe(split_cmdline=split_cmdline, parsed_json=parsed_json)


class ParsedJson:
    """
    Class `ParsedJson` contains a dictionary of confirmed-valid parsed JSON.

    This class is a lightweight wrapper around the dictionaries of parsed JSON.
    The multiple classes that derive from this class will provide some extra
    data attributes for convenience; but ultimately the parsed JSON can always
    be inspected directly using dictionary lookups in the ``.parsed_json``
    attribute.

    We use this container class as an alternative to mixing arbitrary JSON keys
    (produced by an external program) into a top-level class ``__dict__``.

    This class also provides some convenient accessor methods:

    - Pythonic ``dict``-like (eg, ``.get(key, default=None)`` & ``.keys()``)
    - type-converting (eg, ``.get_as_int(key, default=None)``).

    In general, client code should not need to construct this class manually.
    Derived classes of this class are constructed by function :func:`probe`.
    But client code *will* want to invoke the methods of returned instances
    of those derived classes.
    """
    def __init__(self, parsed_json):
        # Verify that `parsed_json` allows value lookup by string keys
        # (even if `parsed_json` is actually empty).
        # We rely on this assumption later.
        try:
            "foo" in parsed_json
            parsed_json.get("foo", None)
        except (AttributeError, TypeError, ValueError) as e:
            raise FFprobeInvalidArgumentError('parsed_json',
                    'Supplied parsed JSON is not a dictionary',
                    parsed_json) from e

        self.parsed_json = parsed_json

    def __repr__(self):
        """Return a string that would yield an object with the same value."""
        return '%s(parsed_json=%s)' % \
                (type(self).__qualname__, self.parsed_json)

    def get(self, key, default=None):
        """Return the value for `key`, if `key` in parsed JSON; else `default`.

        If `key` is not found in parsed JSON, default to `default`.
        If `default` is not supplied, default to `None`.
        This method will never raise a `KeyError`.
        """
        return self.parsed_json.get(key, default)

    def get_as_float(self, key, default=None):
        """Return the value for `key` as a ``float``, if `key` is in parsed JSON
        and can be converted to a ``float``; else `default`.

        If `key` is not found in parsed JSON, default to `default`.
        If conversion to ``float`` fails, default to `default`.
        If `default` is not supplied, default to `None`.
        This method will never raise an exception.
        """
        try:
            return float(self.parsed_json[key])
        except Exception:
            return default

    def get_as_int(self, key, default=None):
        """Return the value for `key` as an ``int``, if `key` is in parsed JSON
        and can be converted to an ``int``; else `default`.

        If `key` is not found in parsed JSON, default to `default`.
        If conversion to ``int`` fails, default to `default`.
        If `default` is not supplied, default to `None`.
        This method will never raise an exception.
        """
        try:
            return int(self.parsed_json[key])
        except Exception:
            return default

    def get_datasize_as_human(self, key, suffix='', default=None, *,
            use_base_10=True):
        """Return a data-size for `key` in a "human-readable” base-10 format;
        else `default`.

        Args:
            key (str): parsed JSON dictionary key to look-up the data-size value
            suffix (str, optional): units of data-size (e.g., ``"B"`` for Bytes)
            default (str, optional): fall-back value to return if this method fails
            use_base_10 (bool, optional): use base-10 units rather than base-2 units

        Returns:
            ``str`` (e.g., ``"567.8 MB"`` or ``"1.3 GiB"``)

        If `key` is not found in parsed JSON, default to `default`.
        If conversion of data-size to ``float`` fails, default to `default`.
        If `default` is not supplied, default to `None`.
        This method will never raise an exception.
        """
        if use_base_10:
            # This is the default, because it's what `ls -lh` does.
            divisor = 1000.0
        else:
            # Use base 2 instead.
            divisor = 1024.0

        try:
            num = float(self.parsed_json[key])
            for unit in ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z']:
                if abs(num) < divisor:
                    if unit and not use_base_10:
                        # We're not using base 10; it must be base 2 instead.
                        # And there is a non-empty unit (eg, 'k', 'M', etc.).
                        # So, postfix the unit by 'i' (eg, 'ki', 'Mi', etc.).
                        return "%3.1f %si%s" % (num, unit, suffix)
                    return "%3.1f %s%s" % (num, unit, suffix)
                num /= divisor
            # The number is large enough that we've reached "Yotta-" ('Y'),
            # the largest decimal unit prefix in the metric system:
            #  https://en.wikipedia.org/wiki/Yotta-
            if not use_base_10:
                # We're not using base 10; it must be base 2 instead.
                # So, postfix the unit by 'i' (ie, 'Yi').
                return "%.1f %s%s" % (num, 'Yi', suffix)
            return "%.1f %s%s" % (num, 'Y', suffix)
        except Exception:
            return default

    def get_duration_as_HH_MM_SS_ss(self, default=None):
        """Return the duration as a string ``"HH:MM:SS.ss"``; else `default`.

        Returns:
            ``str`` (e.g., ``"01:04:14.80"``)

        If ``"duration"`` key is not found in parsed JSON, default to `default`.
        If conversion of duration to ``float`` fails, default to `default`.
        If `default` is not supplied, default to `None`.
        This method will never raise an exception.
        """
        try:
            # Only the seconds
            duration_secs = float(self.parsed_json["duration"])
            # Minutes, seconds
            duration_mins = duration_secs // 60
            duration_secs -= duration_mins * 60
            # Hours, minutes, seconds
            duration_hours = duration_mins // 60
            duration_mins -= duration_hours * 60
            return "%02d:%02d:%02.2f" % \
                    (int(duration_hours), int(duration_mins), duration_secs)
        except Exception:
            return default

    def keys(self):
        """Return the keys in the top-level dictionary of parsed JSON."""
        return self.parsed_json.keys()


class FFprobe(ParsedJson):
    """
    Class `FFprobe` contains the parsed probe output of the ``ffprobe`` command.

    **Note:** Function :func:`probe` is the entry point to this module; it's
    the first function you want to call.  Function :func:`probe` will return
    a valid, appropriately-populated instance of this class `FFprobe`
    (or raise some derived class of the exception base class
    :class:`ffprobe3.exceptions.FFprobeError` trying).

    This class `FFprobe` is a lightweight, convenient wrapper around the JSON
    printed by the ``ffprobe`` command, which has been parsed into dictionaries
    by function :func:`probe`.  This class is both the "root" of a "tree" of
    JSON-wrapper classes, and the "container" of this tree of classes.

    The following data attributes provide convenient access to frequently-used
    keys & values in the "root" level of JSON:

    :ivar format: (:class:`FFformat`) parsed format metadata
    :ivar streams: (list of derived classes of :class:`FFstream`) all parsed streams
    :ivar chapters: (list of :class:`FFchapter`) parsed chapters
    :ivar attachment: (list of :class:`FFattachmentStream`) only parsed attachment streams
    :ivar audio: (list of :class:`FFaudioStream`) only parsed audio streams
    :ivar subtitle: (list of :class:`FFsubtitleStream`) only parsed subtitle streams
    :ivar video: (list of :class:`FFvideoStream`) only parsed video streams

    In addition, the original ``dict`` of the parsed JSON output from ``ffprobe``
    can always be accessed directly in the ``.parsed_json`` attribute of
    base class :class:`ParsedJson`.

    The following data attributes enable retrospective review of the command
    that was executed to produce this parsed probe output:

    :ivar split_cmdline: split command-line that was executed
    :ivar executed_cmd: command executable filename that was executed
    :ivar media_file_path: media-file path that was probed

    In general, client code should not need to construct this class manually.
    It is constructed and returned by function :func:`probe`.  But client code
    *will* want to examine the attributes of a returned instance of this class.

    Example construction::

        ffprobe_output = FFprobe(split_cmdline=[...], parsed_json={...})

    Args:
        split_cmdline (list of strings, optional): split command-line that was executed
        parsed_json (dict, optional): valid parsed JSON output from ``ffprobe`` command

    Raises:
        FFprobeInvalidArgumentError: invalid value supplied for function argument
    """
    def __init__(self, *, split_cmdline=[], parsed_json={}):
        # Verify that `split_cmdline` is a non-string sequence that contains
        # at least 2 strings (ie, the command name & the media file name).
        # We rely on this assumption later.
        if isinstance(split_cmdline, str):
            raise FFprobeInvalidArgumentError('split_cmdline',
                    'Supplied split command-line is actually a single string',
                    split_cmdline)

        try:
            if len(split_cmdline) < 2:
                raise FFprobeInvalidArgumentError('split_cmdline',
                        'Supplied split command-line has too few elements',
                        split_cmdline)
        except (AttributeError, TypeError, ValueError) as e:
            raise FFprobeInvalidArgumentError('split_cmdline',
                    'Supplied split command-line is not a sequence',
                    split_cmdline) from e

        try:
            for s in split_cmdline:
                if not isinstance(s, str):
                    raise FFprobeInvalidArgumentError('split_cmdline',
                            'Supplied split command-line contains non-strings',
                            split_cmdline)
        except (AttributeError, TypeError, ValueError) as e:
            raise FFprobeInvalidArgumentError('split_cmdline',
                    'Supplied split command-line is not a sequence',
                    split_cmdline) from e

        self.split_cmdline = split_cmdline
        self.executed_cmd = split_cmdline[0]
        self.media_file_path = split_cmdline[-1]

        super().__init__(parsed_json)
        # Pick out some particular expected keys from the parsed JSON.
        self.format = FFformat(self.parsed_json.get("format", {}))
        self.streams = [_construct_ffstream_subclass(stream)
                for stream in self.parsed_json.get("streams", [])]
        self.chapters = [FFchapter(chapter)
                for chapter in self.parsed_json.get("chapters", [])]

        self.attachment =   [s for s in self.streams if s.is_attachment()]
        self.audio =        [s for s in self.streams if s.is_audio()]
        self.subtitle =     [s for s in self.streams if s.is_subtitle()]
        self.video =        [s for s in self.streams if s.is_video()]

    def __repr__(self):
        """Return a string that would yield an object with the same value."""
        return '%s(split_cmdline=%s, parsed_json=%s)' % \
                (type(self).__qualname__, self.split_cmdline, self.parsed_json)

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s(%s("%s") => (%s): %s, %s, %s kb/s, %d streams, %d chapters)' % \
                (type(self).__qualname__,
                        self.executed_cmd, self.media_file_path,
                        self.format.format_name,
                        self.format.duration_HH_MM_SS_ss,
                        self.format.size_human,
                        self.format.bit_rate_kbps,
                        len(self.streams), len(self.chapters))


class FFformat(ParsedJson):
    """
    Class `FFformat` contains the format metadata for some media probed by ``ffprobe``.

    **Note:** Function :func:`probe` is the entry point to this module; it's
    the first function you want to call.  Function :func:`probe` will return
    a valid, appropriately-populated instance of :class:`FFprobe`, which in
    turn will contain a valid, appropriately-populated instance of this class
    `FFformat`.

    This class `FFformat` is a lightweight, convenient wrapper around the
    JSON sub-tree for the ``"format"`` key.

    The following data attributes provide convenient access to frequently-used
    keys & values expected in the "format" metadata returned by ``ffprobe``:

    :ivar format_name: short name of the format
    :ivar format_long_name: long name of the format
    :ivar duration_secs: media duration in seconds
    :ivar duration_HH_MM_SS_ss: media duration in ``HH:MM:SS.ss`` format (e.g., ``"01:04:14.80"``)
    :ivar num_streams: number of streams in the media
    :ivar bit_rate_bps: media bit-rate in bits-per-second
    :ivar bit_rate_kbps: media bit-rate in kilobits-per-second
    :ivar size_B: media size in Bytes
    :ivar size_human: media size in "human-readable" base-10 prefix format (e.g., ``"567.8 MB"``)

    In addition, the original ``dict`` of the parsed JSON output from ``ffprobe``
    can always be accessed directly in the ``.parsed_json`` attribute of
    base class :class:`ParsedJson`.

    In general, client code should not need to construct this class manually.
    It is constructed by function :func:`probe`.  But client code *will* want
    to examine the attributes of a returned instance of this class.
    """
    def __init__(self, parsed_json):
        super().__init__(parsed_json)
        self.format_name =          self.parsed_json.get('format_name')
        self.format_long_name =     self.parsed_json.get('format_long_name')
        self.duration_secs =        self.parsed_json.get('duration')
        self.duration_HH_MM_SS_ss = self.get_duration_as_HH_MM_SS_ss()
        self.num_streams =          self.parsed_json.get('nb_streams')
        self.bit_rate_bps =         self.parsed_json.get('bit_rate')
        try:
            self.bit_rate_kbps = int(self.bit_rate_bps) // 1000
        except (TypeError, ValueError):
            self.bit_rate_kbps = None
        self.size_B =               self.parsed_json.get('size')
        self.size_human =           self.get_datasize_as_human('size', 'B')

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s((%s): %s, %s, %s kb/s)' % \
                (type(self).__qualname__, self.format_name,
                        self.duration_HH_MM_SS_ss, self.size_human,
                        self.bit_rate_kbps)


class FFchapter(ParsedJson):
    """
    Class `FFchapter` is an individual chapter in some media probed by ``ffprobe``.

    **Note:** Function :func:`probe` is the entry point to this module; it's
    the first function you want to call.  Function :func:`probe` will return
    a valid, appropriately-populated instance of :class:`FFprobe`, which in
    turn will contain zero or more valid, appropriately-populated instances
    of this class `FFchapter`.

    This class `FFchapter` is a lightweight, convenient wrapper around each
    JSON sub-tree in the list for the ``"chapters"`` key.

    The following data attributes provide convenient access to frequently-used
    keys & values expected in the metadata for an individual chapter:

    :ivar id: chapter identifier
    :ivar title: chapter title

    In addition, the original ``dict`` of the parsed JSON output from ``ffprobe``
    can always be accessed directly in the ``.parsed_json`` attribute of
    base class :class:`ParsedJson`.

    In general, client code should not need to construct this class manually.
    It is constructed by function :func:`probe`.  But client code *will* want
    to examine the attributes of a returned instance of this class.
    """
    def __init__(self, parsed_json):
        super().__init__(parsed_json)
        self.id = self.parsed_json.get('id')
        # This JSON might not have a "tags" key; or the value of the "tags" key
        # might not be a nested dictionary; or that nested dictionary might not
        # have a "title" key.
        try:
            self.title = self.parsed_json['tags']['title']
        except Exception:
            self.title = None

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s(chapters[%s]: "%s")' % \
                (type(self).__qualname__, self.id, self.title)


class FFstream(ParsedJson):
    """
    Class `FFstream` is an individual stream in some media probed by ``ffprobe``.

    **Note:** Function :func:`probe` is the entry point to this module; it's
    the first function you want to call.  Function :func:`probe` will return
    a valid, appropriately-populated instance of :class:`FFprobe`, which in
    turn will contain zero or more valid, appropriately-populated instances
    of this class `FFstream`.

    This class `FFstream` is a lightweight, convenient wrapper around each
    JSON sub-tree in the list for the ``"streams"`` key.

    This class `FFstream` is also the **non-abstract base class** for several
    derived classes that correspond to specific kinds of stream (as indicated
    by the ``codec_type``).  Each derived class has attributes & methods
    relevant to its own corresponding kind of stream.  Currently-implemented
    derived classes:

    - :class:`FFattachmentStream`: ``(codec_type == "attachment")``
    - :class:`FFaudioStream`: ``(codec_type == "audio")``
    - :class:`FFsubtitleStream`: ``(codec_type == "subtitle")``
    - :class:`FFvideoStream`: ``(codec_type == "video")``

    If no ``codec_type`` is specified, or the specified ``codec_type`` is not
    recognized, then a plain old `FFstream` will be returned.

    The following data attributes provide convenient access to frequently-used
    keys & values expected in the metadata for an individual stream:

    :ivar index: index in the list of streams
    :ivar codec_type: type-name of the kind of stream
    :ivar codec_name: short name of the specific codec used
    :ivar codec_long_name: long name of the specific codec used
    :ivar duration_secs: stream duration in seconds

    In addition, the original ``dict`` of the parsed JSON output from ``ffprobe``
    can always be accessed directly in the ``.parsed_json`` attribute of
    base class :class:`ParsedJson`.

    In general, client code should not need to construct this class manually.
    It is constructed by function :func:`probe`.  But client code *will* want
    to examine the attributes of a returned instance of this class.
    """
    def __init__(self, parsed_json):
        super().__init__(parsed_json)
        self.index =            self.parsed_json.get('index')
        self.codec_type =       self.parsed_json.get('codec_type')
        self.codec_name =       self.parsed_json.get('codec_name')
        self.codec_long_name =  self.parsed_json.get('codec_long_name')
        self.duration_secs =    self.parsed_json.get('duration')

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s(streams[%s]: %s(%s))' % \
                (type(self).__qualname__, self.index,
                        self.codec_type, self.codec_name)

    def is_attachment(self):
        """Return whether this `FFstream` instance is an attachment stream."""
        return self.codec_type == 'attachment'

    def is_audio(self):
        """Return whether this `FFstream` instance is an audio stream."""
        return self.codec_type == 'audio'

    def is_subtitle(self):
        """Return whether this `FFstream` instance is a subtitle stream."""
        return self.codec_type == 'subtitle'

    def is_video(self):
        """Return whether this `FFstream` instance is a video stream."""
        return self.codec_type == 'video'


class FFattachmentStream(FFstream):
    """
    Class `FFattachmentStream` is an individual attachment stream in some media
    probed by ``ffprobe``.

    This class `FFattachmentStream` is a derived class of base class
    :class:`FFstream` that has additional data attributes & methods relevant
    to an attachment stream (currently none).

    **Note:** An instance of this class `FFattachmentStream` may **only** be
    constructed for `parsed_json` with ``(codec_type == "attachment")``.
    Otherwise an exception :class:`FFprobeStreamSubclassError` will be raised.

    Raises:
        FFprobeStreamSubclassError: ``(codec_type != "attachment")``
    """
    def __init__(self, parsed_json):
        super().__init__(parsed_json)
        if self.codec_type != 'attachment':
            raise FFprobeStreamSubclassError(
                    type(self).__qualname__, self.codec_type, 'attachment')

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s(streams[%s]: %s(%s))' % \
                (type(self).__qualname__, self.index,
                        self.codec_type, self.codec_name)


class FFaudioStream(FFstream):
    """
    Class `FFaudioStream` is an individual audio stream in some media
    probed by ``ffprobe``.

    This class `FFaudioStream` is a derived class of base class
    :class:`FFstream` that has additional data attributes & methods relevant
    to an audio stream.

    The following data attributes provide convenient access to frequently-used
    keys & values expected in the metadata for an audio stream:

    :ivar num_channels: number of audio channels
    :ivar channel_layout: audio channel configuration (e.g., ``"stereo"``)
    :ivar sample_rate_Hz: audio sample-rate in Hz
    :ivar bit_rate_bps: audio bit-rate in bits-per-second
    :ivar bit_rate_kbps: audio bit-rate in kilobits-per-second

    **Note:** An instance of this class `FFaudioStream` may **only** be
    constructed for `parsed_json` with ``(codec_type == "audio")``.
    Otherwise an exception :class:`FFprobeStreamSubclassError` will be raised.

    Raises:
        FFprobeStreamSubclassError: ``(codec_type != "audio")``
    """
    def __init__(self, parsed_json):
        super().__init__(parsed_json)
        if self.codec_type != 'audio':
            raise FFprobeStreamSubclassError(
                    type(self).__qualname__, self.codec_type, 'audio')

        self.num_channels =    self.parsed_json.get('channels')
        self.channel_layout =  self.parsed_json.get('channel_layout')
        self.sample_rate_Hz =  self.parsed_json.get('sample_rate')
        self.bit_rate_bps =    self.parsed_json.get('bit_rate')
        try:
            self.bit_rate_kbps = int(self.bit_rate_bps) // 1000
        except (TypeError, ValueError):
            self.bit_rate_kbps = None

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s(streams[%s]: %s(%s): %s channels (%s), %s Hz, %s kb/s)' % \
                (type(self).__qualname__, self.index,
                        self.codec_type, self.codec_name,
                        self.num_channels, self.channel_layout,
                        self.sample_rate_Hz, self.bit_rate_kbps)


class FFsubtitleStream(FFstream):
    """
    Class `FFsubtitleStream` is an individual subtitle stream in some media
    probed by ``ffprobe``.

    This class `FFsubtitleStream` is a derived class of base class
    :class:`FFstream` that has additional data attributes & methods relevant
    to a subtitle stream (currently none).

    **Note:** An instance of this class `FFsubtitleStream` may **only** be
    constructed for `parsed_json` with ``(codec_type == "subtitle")``.
    Otherwise an exception :class:`FFprobeStreamSubclassError` will be raised.

    Raises:
        FFprobeStreamSubclassError: ``(codec_type != "subtitle")``
    """
    def __init__(self, parsed_json):
        super().__init__(parsed_json)
        if self.codec_type != 'subtitle':
            raise FFprobeStreamSubclassError(
                    type(self).__qualname__, self.codec_type, 'subtitle')

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s(streams[%s]: %s(%s))' % \
                (type(self).__qualname__, self.index,
                        self.codec_type, self.codec_name)


class FFvideoStream(FFstream):
    """
    Class `FFvideoStream` is an individual video stream in some media
    probed by ``ffprobe``.

    This class `FFvideoStream` is a derived class of base class
    :class:`FFstream` that has additional data attributes & methods relevant
    to a video stream.

    The following data attributes provide convenient access to frequently-used
    keys & values expected in the metadata for a video stream:

    :ivar width_px: frame width in pixels
    :ivar height_px: frame height in pixels
    :ivar avg_frame_rate: average frame rate
    :ivar bit_rate_bps: video bit-rate in bits-per-second
    :ivar bit_rate_kbps: video bit-rate in kilobits-per-second

    **Note:** An instance of this class `FFvideoStream` may **only** be
    constructed for `parsed_json` with ``(codec_type == "video")``.
    Otherwise an exception :class:`FFprobeStreamSubclassError` will be raised.

    Raises:
        FFprobeStreamSubclassError: ``(codec_type != "video")``
    """
    def __init__(self, parsed_json):
        super().__init__(parsed_json)
        if self.codec_type != 'video':
            raise FFprobeStreamSubclassError(
                    type(self).__qualname__, self.codec_type, 'video')

        self.width_px =        self.parsed_json.get('width')
        self.height_px =       self.parsed_json.get('height')
        self.avg_frame_rate =  self.parsed_json.get('avg_frame_rate')
        self.bit_rate_bps =    self.parsed_json.get('bit_rate')
        try:
            self.bit_rate_kbps = int(self.bit_rate_bps) // 1000
        except (TypeError, ValueError):
            self.bit_rate_kbps = None

    def __str__(self):
        """Return a string containing a human-readable summary of the object."""
        return '%s(streams[%s]: %s(%s): %sx%s, %s fps, %s kb/s)' % \
                (type(self).__qualname__, self.index,
                        self.codec_type, self.codec_name,
                        self.width_px, self.height_px,
                        self.avg_frame_rate, self.bit_rate_kbps)

    def get_frame_shape_as_ints(self, default=None):
        """Return the frame (width, height) as a pair of ints; else `default`.

        If `default` is not supplied, it defaults to `None`, so this method
        will never raise a `KeyError`.
        """
        try:
            width = int(self.width_px)
            height = int(self.height_px)
            return (width, height)
        except Exception:
            return default


_KNOWN_FFSTREAM_SUBCLASSES = dict(
    attachment= FFattachmentStream,
    audio=      FFaudioStream,
    subtitle=   FFsubtitleStream,
    video=      FFvideoStream,
)

def _construct_ffstream_subclass(parsed_json):
    codec_type = parsed_json.get('codec_type')
    if codec_type is not None:
        constructor = _KNOWN_FFSTREAM_SUBCLASSES.get(codec_type)
        if constructor is not None:
            return constructor(parsed_json)
    return FFstream(parsed_json)
