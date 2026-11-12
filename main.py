import os
import struct
import zlib
import math

# Palette
COLORS = {
    "WATER_TOP": (168, 223, 240),
    "WATER_MID": (196, 235, 245),
    "WATER_BOT": (222, 246, 250),
    "RAY": (207, 240, 248),
    "SAND": (255, 227, 179),
    "SAND_DARK": (242, 201, 143),
    "PEBBLE1": (232, 184, 120),
    "PEBBLE2": (255, 179, 193),
    "BODY": (255, 158, 158),
    "BODY_DARK": (244, 133, 143),
    "BELLY": (255, 214, 222),
    "SHEEN": (255, 211, 218),
    "SUCKER": (255, 194, 204),
    "CHEEK": (255, 143, 168),
    "EYE_WHITE": (255, 255, 255),
    "PUPIL": (43, 43, 58),
    "MOUTH": (122, 59, 77),
    "STAR_OUT": (245, 166, 38),
    "STAR_IN": (255, 211, 77),
    "BUBBLE": (234, 251, 255),
}

WIDTH, HEIGHT = 1024, 1024
canvas = bytearray(WIDTH * HEIGHT * 3)

# Faster pixel setting, bounds handled by callers
def set_px(x, y, color):
    idx = (y * WIDTH + x) * 3
    canvas[idx:idx+3] = bytes(color)

def fill_span(y, x1, x2, color):
    for x in range(max(0, x1), min(WIDTH, x2 + 1)):
        set_px(x, y, color)

def fill_ellipse(cx, cy, rx, ry, color):
    for y in range(max(0, int(cy - ry)), min(HEIGHT, int(cy + ry + 1))):
        dy = y - cy
        dx = int(math.sqrt(max(0, rx**2 * (1 - dy**2 / ry**2))))
        fill_span(y, int(cx - dx), int(cx + dx), color)

def fill_circle(cx, cy, r, color):
    fill_ellipse(cx, cy, r, r, color)

def fill_polygon(points, color):
    # Scanline polygon filler
    min_y = min(p[1] for p in points)
    max_y = max(p[1] for p in points)
    for y in range(int(min_y), int(max_y) + 1):
        intersections = []
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            if (p1[1] <= y < p2[1]) or (p2[1] <= y < p1[1]):
                x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                intersections.append(x)
        intersections.sort()
        for i in range(0, len(intersections), 2):
            fill_span(y, int(intersections[i]), int(intersections[i+1]), color)

def lerp_c(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

def stamp_arc(cx, cy, r, a0, a1, dot_r, col, steps=26):
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * (i / steps)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        fill_circle(int(x), int(y), dot_r, col)

def write_png(file_path):
    # PNG implementation
    import zlib, struct
    def crc32(data):
        return zlib.crc32(data) & 0xFFFFFFFF

    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0) # Filter
        raw.extend(canvas[y * WIDTH * 3 : (y + 1) * WIDTH * 3])
    
    compressed = zlib.compress(raw, 9)
    
    with open(file_path, "wb") as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        # IHDR
        ihdr = struct.pack('>IIBBBBB', WIDTH, HEIGHT, 8, 2, 0, 0, 0)
        f.write(struct.pack('>I', 13))
        f.write(b'IHDR')
        f.write(ihdr)
        f.write(struct.pack('>I', crc32(b'IHDR' + ihdr)))
        # IDAT
        f.write(struct.pack('>I', len(compressed)))
        f.write(b'IDAT')
        f.write(compressed)
        f.write(struct.pack('>I', crc32(b'IDAT' + compressed)))
        # IEND
        f.write(struct.pack('>I', 0))
        f.write(b'IEND')
        f.write(struct.pack('>I', crc32(b'IEND')))

def main():
    # 1. Water
    for y in range(HEIGHT):
        if y < 512:
            color = lerp_c(COLORS["WATER_TOP"], COLORS["WATER_MID"], y / 512)
        else:
            color = lerp_c(COLORS["WATER_MID"], COLORS["WATER_BOT"], (y - 512) / 512)
        fill_span(y, 0, WIDTH - 1, color)
    
    # 2. Light rays
    fill_polygon([(180,0), (300,0), (520,900), (380,900)], COLORS["RAY"])
    fill_polygon([(700,0), (790,0), (900,820), (800,820)], COLORS["RAY"])
    
    # 3. Sand
    fill_ellipse(512, 1180, 760, 300, COLORS["SAND"])
    fill_ellipse(512, 1150, 760, 290, COLORS["SAND_DARK"])
    fill_ellipse(512, 1185, 760, 295, COLORS["SAND"])
    fill_ellipse(205, 940, 52, 26, COLORS["PEBBLE1"])
    fill_ellipse(830, 955, 44, 22, COLORS["PEBBLE2"])
    
    # 4. Bubbles
    for bx, by, br in [(155,300,26), (205,210,17), (880,260,30), (835,160,18), (905,420,15), (120,470,13)]:
        fill_circle(bx, by, br, COLORS["BUBBLE"])
        fill_circle(int(bx - 0.35*br), int(by - 0.35*br), int(0.32*br), (255,255,255))
    
    # 5. Tentacles
    tentacle_data = [
        (-196,640,-58,46,175,37,0), (-148,668,-40,30,185,39,0),
        (-96,686,-20,14,195,41,0), (-38,694,-6,4,200,42,0),
        (38,694,6,-4,200,42,0), (96,686,20,-14,195,41,0),
        (148,668,55,25,150,39,95), (196,640,58,-46,175,37,0)
    ]
    
    # Draw outer (behind)
    for i in [0, 7]:
        base_x, base_y, drift, curl, length, r0, lift = tentacle_data[i]
        for step in range(17):
            u = step / 16
            cx = 512 + base_x + drift*u + curl*u**2
            cy = base_y + length*u - lift*u**2
            r = r0 * (1 - 0.55*u)
            fill_circle(int(cx), int(cy), int(r), COLORS["BODY_DARK"])
    
    # 6. Head
    fill_ellipse(512, 470, 242, 238, COLORS["BODY"])
    fill_ellipse(415, 350, 92, 58, COLORS["SHEEN"])
    fill_ellipse(512, 600, 150, 105, COLORS["BELLY"])
    
    # 5. Tentacles - Front
    suckers = []
    for i in range(1, 7):
        base_x, base_y, drift, curl, length, r0, lift = tentacle_data[i]
        for step in range(17):
            u = step / 16
            cx = 512 + base_x + drift*u + curl*u**2
            cy = base_y + length*u - lift*u**2
            r = r0 * (1 - 0.55*u)
            fill_circle(int(cx), int(cy), int(r), COLORS["BODY"])
            if step in [5, 8, 11, 14]:
                suckers.append((cx, cy + 0.35*r, 0.30*r))
    for sx, sy, sr in suckers:
        fill_circle(int(sx), int(sy), int(max(3.0, sr)), COLORS["SUCKER"])
        
    # 7. Face
    fill_ellipse(362, 522, 36, 21, COLORS["CHEEK"])
    fill_ellipse(662, 522, 36, 21, COLORS["CHEEK"])
    for ex in [425, 599]:
        fill_ellipse(ex, 448, 55, 65, COLORS["EYE_WHITE"])
        fill_circle(ex - 7, 456, 30, COLORS["PUPIL"])
        fill_circle(ex - 11, 442, 12, (255,255,255))
        fill_circle(ex + 4, 470, 6, (255,255,255))
    stamp_arc(512, 528, 36, math.radians(25), math.radians(155), 5, COLORS["MOUTH"])
    
    # 8. Starfish
    tilt = math.radians(30)
    points = []
    for i in range(10):
        ang = tilt + i * math.pi / 5 - math.pi / 2
        rad = 54 if i % 2 == 0 else 21
        points.append((648 + rad * math.cos(ang), 252 + rad * math.sin(ang)))
    fill_polygon(points, COLORS["STAR_OUT"])
    points_in = []
    for i in range(10):
        ang = tilt + i * math.pi / 5 - math.pi / 2
        rad = 54 * 0.62 if i % 2 == 0 else 21 * 0.62
        points_in.append((648 + rad * math.cos(ang), 252 + rad * math.sin(ang)))
    fill_polygon(points_in, COLORS["STAR_IN"])
    fill_circle(648, 252, 6, COLORS["STAR_IN"])
    
    # Save file
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    write_png(os.path.join(output_dir, "entry.png"))

if __name__ == "__main__":
    main()
