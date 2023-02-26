import io
import math
import struct
import argparse
import itertools
import subprocess

from collections import deque

import cairo
import ffmpeg
import audioread
 
def clamp(v, mn, mx): 
    return min(max(v, mn), mx)

def slide_window(l, n):
    it = iter(l)
    buf = deque(itertools.islice(it, n-1), n)
    for i in it:
        buf.append(i)
        yield tuple(buf)

def grouper(l, n):
    chunks = zip(*[iter(l)]*n) #itertools.zip_longest(*[iter(l)]*n)
    for chunk in chunks:
        yield chunk
        
def length(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def get_channels(reader, channels):
    for samples in grouper((bytes(x) for x in grouper(itertools.chain.from_iterable(reader), 2)), channels):
        group = [x/32768 for x in struct.unpack('<'+'h'*channels, b''.join(samples))]
        group[1] = group[1]*-1 # fix orientation
        yield group
    
def hsv_to_rgb(h, s, v):
        if s == 0.0: return (v, v, v)
        i = int(h*6.)
        f = (h*6.)-i; p,q,t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f)); i%=6
        if i == 0: return (v, t, p)
        if i == 1: return (q, v, p)
        if i == 2: return (p, v, t)
        if i == 3: return (p, q, v)
        if i == 4: return (t, p, v)
        if i == 5: return (v, p, q)
 
def ffmpeg_writer(out_filename, in_audio, framerate): 
    audio = ffmpeg.input(in_audio).audio
    args = ( 
        ffmpeg 
        .input('pipe:', format='png_pipe', r=framerate)
        .output(audio, out_filename, vcodec='h264', pix_fmt='yuv444p', crf='0', preset='slow')#, **{'profile:v': 'high444'}) 
        .overwrite_output() 
        .compile()
    ) 
    return subprocess.Popen(args, stdin=subprocess.PIPE) 

def main():
    parser = argparse.ArgumentParser(
                    prog = 'VScope',
                    description = 'Oscilloscope music visualizer'
                    )
    parser.add_argument('input_audio')
    parser.add_argument('output_video')
    parser.add_argument('-r', '--framerate', type=int, required=False, default=60)
    parser.add_argument('-s', '--size', type=int, required=False, default=1000)
    args = parser.parse_args()
    
    framerate = args.framerate
    size = args.size
    audio = args.input_audio
    writer = ffmpeg_writer(args.output_video, audio, framerate)
    with audioread.audio_open(audio) as sound:
        channels = sound.channels
        if channels != 2:
            raise Exception(f'there should be 2 channels, found {channels} instead.')
        samplerate = sound.samplerate
        data = sound.read_data()
        frame_window = samplerate//framerate
        frame_incr = 0
        for dots in grouper(get_channels(data, channels), frame_window):
            with cairo.SVGSurface(None, size, size) as surface: 
                incr = 0
                buf = io.BytesIO()
                context = cairo.Context(surface) 
                context.set_antialias(cairo.Antialias.BEST) 
                context.scale(size//2, size//2)
                context.translate(1, 1)
                context.set_source_rgb(0, 0, 0)
                context.rectangle(-1, -1, 2, 2)
                context.fill()
                context.set_source_rgb(0, 1, 1)
                
                for p1, p2 in slide_window(dots, 2):
                    l = length(p1, p2)
                    context.set_line_width(clamp(0.005-0.002*l, 0.00025, 0.005))
                    context.set_source_rgba(*hsv_to_rgb(((incr/(frame_window*3.25)+0.67)+frame_incr/frame_window*1.5)%1, 1, 1), clamp(1-l*15, 0.1, 1-l)))
                    context.move_to(*p1)
                    context.line_to(*p2)
                    context.stroke()
                    incr += 1
                frame_incr += 1
                surface.write_to_png(buf)
                writer.stdin.write(buf.getvalue())
            
main()