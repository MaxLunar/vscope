import io

import cairo
import audioread

from utils import *


def process(framerate, size, audio, writer):
    with audioread.audio_open(audio) as sound:
        channels = sound.channels
        if channels != 2:
            raise Exception(f"there should be 2 channels, found {channels} instead.")
        samplerate = sound.samplerate
        data = sound.read_data()
        frame_window = samplerate // framerate
        frame_incr = 0
        for dots in grouper(get_channels(data, channels), frame_window):
            with cairo.SVGSurface(None, size, size) as surface:
                incr = 0
                buf = io.BytesIO()
                context = cairo.Context(surface)
                context.set_antialias(cairo.Antialias.BEST)
                context.scale(size // 2, size // 2)
                context.translate(1, 1)
                context.set_source_rgb(0, 0, 0)
                context.rectangle(-1, -1, 2, 2)
                context.fill()
                context.set_source_rgb(0, 1, 1)

                for p1, p2 in slide_window(dots, 2):
                    l = length(p1, p2)
                    context.set_line_width(clamp(0.005 - 0.002 * l, 0.00025, 0.005))
                    context.set_source_rgba(
                        *hsv_to_rgb(
                            (
                                (incr / (frame_window * 3.25) + 0.67)
                                + frame_incr / frame_window * 1.5
                            )
                            % 1,
                            1,
                            1,
                        ),
                        clamp(1 - l * 15, 0.1, 1 - l),
                    )
                    context.move_to(*p1)
                    context.line_to(*p2)
                    context.stroke()
                    incr += 1
                frame_incr += 1
                surface.write_to_png(buf)
                writer.stdin.write(buf.getvalue())
