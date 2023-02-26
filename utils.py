import math
import struct
import itertools

from collections import deque


def clamp(v, mn, mx):
    return min(max(v, mn), mx)


def slide_window(l, n):
    it = iter(l)
    buf = deque(itertools.islice(it, n - 1), n)
    for i in it:
        buf.append(i)
        yield tuple(buf)


def grouper(l, n):
    chunks = zip(*[iter(l)] * n)  # itertools.zip_longest(*[iter(l)]*n)
    for chunk in chunks:
        yield chunk


def length(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def get_channels(reader, channels):
    for samples in grouper(
        (bytes(x) for x in grouper(itertools.chain.from_iterable(reader), 2)), channels
    ):
        group = [
            x / 32768 for x in struct.unpack("<" + "h" * channels, b"".join(samples))
        ]
        group[1] = group[1] * -1  # fix orientation
        yield group


def hsv_to_rgb(h, s, v):
    if s == 0.0:
        return (v, v, v)
    i = int(h * 6.0)
    f = (h * 6.0) - i
    p, q, t = v * (1.0 - s), v * (1.0 - s * f), v * (1.0 - s * (1.0 - f))
    i %= 6
    if i == 0:
        return (v, t, p)
    if i == 1:
        return (q, v, p)
    if i == 2:
        return (p, v, t)
    if i == 3:
        return (p, q, v)
    if i == 4:
        return (t, p, v)
    if i == 5:
        return (v, p, q)
