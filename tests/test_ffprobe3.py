#!/usr/bin/env python3
#
# Test the `ffprobe3` function & class API for two known media files.
# These tests are crude but comprehensive.
#
# Usage from this `tests` directory:
#   python3 test_ffprobe3.py
#
# Usage from the root directory of the repo:
#   python3 tests/test_ffprobe3.py
#
# If all the tests run, and nothing is printed on stderr, and the script ends
# with "All tests passed." printed to stdout, then the tests have succeeded.
# If any tests fail, the script will halt immediately, with the error printed
# to stderr.

import os
import ffprobe3


def test_SampleVideo_720x480_5mb(data_dir):
    test_filename = os.path.join(data_dir, "SampleVideo_720x480_5mb.mp4")
    p = ffprobe3.probe(test_filename)

    # `FFprobe` instance:
    assert repr(p).startswith("FFprobe(split_cmdline=[")
    assert "], parsed_json={" in repr(p)
    assert repr(p).endswith("})")
    assert str(p) == ('FFprobe(ffprobe "%s" => (mov,mp4,m4a,3gp,3g2,mj2): 00:00:31.00, 5.2 MB, 1353.182 kb/s, 2 streams, 0 chapters)' % test_filename)

    assert p.get_attr_names() == [
            'attachment',
            'audio',
            'chapters',
            'executed_cmd',
            'format',
            'media_filename',
            'parsed_json',
            'split_cmdline',
            'streams',
            'subtitle',
            'video',
    ]
    for k in ['chapters', 'format', 'streams']:
        assert k in p.keys()

    assert isinstance(p.split_cmdline, list)
    assert isinstance(p.executed_cmd, str)
    assert isinstance(p.media_filename, str)
    assert p.media_filename == test_filename

    assert p.format is not None
    assert repr(p.format).startswith("FFformat(parsed_json={")
    assert p.get("format") is not None
    assert p["format"] is not None
    assert p["format"] is p.get("format")
    assert p["format"] is p.format.parsed_json

    assert isinstance(p.streams, list)
    assert len(p.streams) == 2
    assert isinstance(p.chapters, list)
    assert len(p.chapters) == 0
    assert isinstance(p.attachment, list)
    assert len(p.attachment) == 0
    assert isinstance(p.audio, list)
    assert len(p.audio) == 1
    assert isinstance(p.subtitle, list)
    assert len(p.subtitle) == 0
    assert isinstance(p.video, list)
    assert len(p.video) == 1

    # `FFformat` instance:
    f = p.format
    assert repr(f).startswith("FFformat(parsed_json={")
    assert str(f) == "FFformat((mov,mp4,m4a,3gp,3g2,mj2): 00:00:31.00, 5.2 MB, 1353.182 kb/s)"

    for k in [
            'bit_rate',
            'duration',
            'filename',
            'format_long_name',
            'format_name',
            'nb_programs',
            'nb_streams',
            'probe_score',
            'size',
            'start_time',
            'tags',
    ]:
        assert k in f.keys()

    assert f.get("format_name") == 'mov,mp4,m4a,3gp,3g2,mj2'
    assert f.get_as_float("duration") == 30.998
    assert f.get_as_int("nb_streams") == 2
    assert f.get_as_int('size') == 5243244

    assert f.get_attr_names() == [
            'bit_rate_bps',
            'bit_rate_kbps',
            'duration_human',
            'duration_secs',
            'format_long_name',
            'format_name',
            'num_streams',
            'parsed_json',
            'size_B',
            'size_human',
    ]

    assert f.bit_rate_bps == 1353182
    assert f.bit_rate_kbps == 1353.182
    assert f.duration_human == '00:00:31.00'
    assert f.duration_secs == 30.998
    assert f.format_long_name == 'QuickTime / MOV'
    assert f.format_name == 'mov,mp4,m4a,3gp,3g2,mj2'
    assert f.num_streams == 2
    assert f.size_B == 5243244
    assert f.size_human == '5.2 MB'

    assert f.get_datasize_as_human('size') == '5.2 M'
    assert f.get_duration_as_human() == '00:00:31.00'

    # The streams:
    a = p.audio[0]
    v = p.video[0]
    assert p.streams[0] is v
    assert p.streams[1] is a

    # The video stream, a `FFvideoStream` instance:
    assert repr(v).startswith("FFvideoStream(parsed_json={")
    assert str(v) == "FFvideoStream(streams[0]: video(h264): 640x480, 25/1 fps, 966.247 kb/s)"

    for k in [
            'avg_frame_rate',
            'bit_rate',
            'bits_per_raw_sample',
            'chroma_location',
            'codec_long_name',
            'codec_name',
            'codec_tag',
            'codec_tag_string',
            'codec_time_base',
            'codec_type',
            'coded_height',
            'coded_width',
            'display_aspect_ratio',
            'disposition',
            'duration',
            'duration_ts',
            'has_b_frames',
            'height',
            'index',
            'is_avc',
            'level',
            'nal_length_size',
            'nb_frames',
            'pix_fmt',
            'profile',
            'r_frame_rate',
            'refs',
            'sample_aspect_ratio',
            'start_pts',
            'start_time',
            'tags',
            'time_base',
            'width',
    ]:
        assert k in v.keys()

    assert v.get("codec_type") == 'video'
    assert v.get_as_float("duration") == 30.96
    assert v.get_as_float("start_time") == 0.0
    assert v.get_as_int("height") == 480
    assert v.get_as_int("width") == 640

    assert v.get_attr_names() == [
            'avg_frame_rate',
            'bit_rate_bps',
            'bit_rate_kbps',
            'codec_long_name',
            'codec_name',
            'codec_type',
            'duration_secs',
            'height',
            'index',
            'num_frames',
            'parsed_json',
            'width',
    ]

    assert v.avg_frame_rate == '25/1'
    assert v.bit_rate_bps == 966247
    assert v.bit_rate_kbps == 966.247
    assert v.codec_long_name == 'H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10'
    assert v.codec_name == 'h264'
    assert v.codec_type == 'video'
    assert v.duration_secs == 30.96
    assert v.height == 480
    assert v.index == 0
    assert v.num_frames == 774
    assert v.width == 640

    assert v.get_duration_as_human() == '00:00:30.96'
    assert v.get_frame_shape() == (640, 480)
    assert not v.is_attachment()
    assert not v.is_audio()
    assert not v.is_subtitle()
    assert v.is_video()

    # The audio stream, a `FFaudioStream` instance:
    assert repr(a).startswith("FFaudioStream(parsed_json={")
    assert str(a) == "FFaudioStream(streams[1]: audio(aac): 6 channels (5.1), 48000 Hz, 383.29 kb/s)"

    for k in [
            'nb_frames',
            'r_frame_rate',
            'channel_layout',
            'start_pts',
            'codec_long_name',
            'tags',
            'sample_fmt',
            'duration',
            'max_bit_rate',
            'sample_rate',
            'codec_type',
            'duration_ts',
            'disposition',
            'codec_name',
            'codec_time_base',
            'bit_rate',
            'time_base',
            'codec_tag_string',
            'avg_frame_rate',
            'index',
            'channels',
            'start_time',
            'profile',
            'codec_tag',
            'bits_per_sample',
    ]:
        assert k in a.keys()

    assert a.get("codec_type") == 'audio'
    assert a.get_as_float("duration") == 30.997333
    assert a.get_as_float("start_time") == 0.0
    assert a.get_as_int("channels") == 6
    assert a.get_as_int("sample_rate") == 48000

    assert a.get_attr_names() == [
            'bit_rate_bps',
            'bit_rate_kbps',
            'channel_layout',
            'codec_long_name',
            'codec_name',
            'codec_type',
            'duration_secs',
            'index',
            'num_channels',
            'num_frames',
            'parsed_json',
            'sample_rate_Hz',
    ]

    assert a.bit_rate_bps == 383290
    assert a.bit_rate_kbps == 383.29
    assert a.channel_layout == '5.1'
    assert a.codec_long_name == 'AAC (Advanced Audio Coding)'
    assert a.codec_name == 'aac'
    assert a.codec_type == 'audio'
    assert a.duration_secs == 30.997333
    assert a.index == 1
    assert a.num_channels == 6
    assert a.num_frames == 1453
    assert a.sample_rate_Hz == 48000

    assert a.get_duration_as_human() == '00:00:31.00'
    assert not a.is_attachment()
    assert a.is_audio()
    assert not a.is_subtitle()
    assert not a.is_video()


def test_errors(data_dir):
    # Test handling of a non-existent local media file.
    non_existent_media_filename = "this-media-file-does-not-exist"
    try:
        ffprobe3.probe(non_existent_media_filename)
    except ffprobe3.FFprobeMediaFileError as e:
        # This is the exception that was expected.
        assert e.file_path == non_existent_media_filename

    # Test handling of a non-zero exit status from `ffprobe` command
    # (in this case, due to a non-existent local media file,
    # which we have told `ffprobe3.probe` NOT to verify beforehand).
    try:
        ffprobe3.probe(non_existent_media_filename,
                verify_local_mediafile=False)
    except ffprobe3.FFprobeSubprocessError as e:
        # This is the exception that was expected.
        assert e.exit_status == 1
        # `e.stderr` will look like:
        #   this-media-file-does-not-exist: No such file or directory\n
        # (with a trailing newline)
        error_message = e.stderr.strip()
        assert error_message == ('%s: No such file or directory' %
                non_existent_media_filename)

    # Test handling of a non-zero exit status from `ffprobe` command
    # (in this case, due to a file which exists but is NOT a media file.
    not_a_media_file = __file__
    try:
        ffprobe3.probe(not_a_media_file)
    except ffprobe3.FFprobeSubprocessError as e:
        # This is the exception that was expected.
        assert e.exit_status == 1
        # `e.stderr` will look like:
        #   tests/test_ffprobe3.py: Invalid data found when processing input\n
        # (with a trailing newline)
        error_message = e.stderr.split(':', 1)[-1].strip()
        assert error_message == 'Invalid data found when processing input'

    # Test handling of a non-existent command specified by the caller.
    test_filename = os.path.join(data_dir, "SampleVideo_720x480_5mb.mp4")
    non_existent_command_name = "this-command-does-not-exist"
    try:
        ffprobe3.probe(test_filename,
                ffprobe_cmd_override=non_existent_command_name)
    except ffprobe3.FFprobeOverrideFileError as e:
        # This is the exception that was expected.
        assert e.file_path == non_existent_command_name

    # Test handling of when no `ffprobe` command is found in `$PATH`.
    # We will do this by temporarily replacing the normally-valid `"ffprobe"`
    # command with `"this-command-does-not-exist"`.
    from ffprobe3 import ffprobe3 as ffprobe3_actual
    # Save the valid ffprobe command so we can restore it after the test.
    valid_ffprobe_command = ffprobe3_actual._SPLIT_COMMAND_LINE[0]
    ffprobe3_actual._SPLIT_COMMAND_LINE[0] = non_existent_command_name
    try:
        ffprobe3.probe(test_filename)
    except ffprobe3.FFprobeExecutableError as e:
        # This is the exception that was expected.
        assert e.cmd == non_existent_command_name
    # Now restore the valid ffprobe command for any subsequent tests.
    ffprobe3_actual._SPLIT_COMMAND_LINE[0] = valid_ffprobe_command


_TEST_FUNCS = [
        test_SampleVideo_720x480_5mb,
        test_errors,
]


def main():
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(tests_dir, "data")

    for tf in _TEST_FUNCS:
        print("* %s" % tf.__name__)
        tf(data_dir)

    print("All tests passed.")


if __name__ == "__main__":
    main()