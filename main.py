import argparse
import subprocess

import ffmpeg

import logic


def ffmpeg_writer(out_filename, in_audio, framerate):
    audio = ffmpeg.input(in_audio).audio
    args = (
        ffmpeg.input("pipe:", format="png_pipe", r=framerate)
        .output(
            audio,
            out_filename,
            vcodec="h264",
            pix_fmt="yuv444p",
            crf="0",
            preset="slow",
        )  # , **{'profile:v': 'high444'})
        .overwrite_output()
        .compile()
    )
    return subprocess.Popen(args, stdin=subprocess.PIPE)


def main():
    parser = argparse.ArgumentParser(
        prog="VScope", description="Oscilloscope music visualizer"
    )
    parser.add_argument("input_audio")
    parser.add_argument("output_video")
    parser.add_argument("-r", "--framerate", type=int, required=False, default=60)
    parser.add_argument("-s", "--size", type=int, required=False, default=1000)
    args = parser.parse_args()

    framerate = args.framerate
    size = args.size
    audio = args.input_audio
    writer = ffmpeg_writer(args.output_video, audio, framerate)
    logic.process(framerate, size, audio, writer)


if __name__ == "__main__":
    main()
