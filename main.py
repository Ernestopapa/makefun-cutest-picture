import os
import zlib
import struct
import math

# Palette
COLORS = {
    "background": (255, 227, 200),
    "halo": (255, 240, 222),
    "fur_outline": (230, 199, 158),
    "kitten_fur": (255, 247, 230),
    "belly": (255, 254, 249),
    "pink": (255, 207, 192),
    "blush": (255, 188, 200),
    "eye_brown": (51, 38, 26),
    "white": (255, 255, 255),
    "nose": (255, 143, 163),
    "mouth": (156, 107, 74),
    "whisker": (217, 180, 143),
    "chick_yellow": (255, 217, 61),
    "chick_outline": (237, 185, 10),
    "chick_wing": (245, 197, 49),
    "beak": (255, 159, 28),
    "chick_blush": (255, 160, 122),
    "bow": (126, 200, 227),
    "bow_centre": (90, 169, 214)
}

WIDTH, HEIGHT = 1024, 1024
canvas = bytearray([255, 227, 200] * WIDTH * HEIGHT)

def get_pixel(x, y):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        idx = (y * WIDTH + x) * 3
        return canvas[idx:idx+3]
    return None

def set_pixel(x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        idx = (y * WIDTH + x) * 3
        canvas[idx:idx+3] = bytes(color)

def draw_filled_circle(cx, cy, r, color):
    r_sq = r * r
    y0 = max(0, int(math.floor(cy - r)))
    y1 = min(HEIGHT, int(math.ceil(cy + r)) + 1)
    for y in range(y0, y1):
        dy = y - cy
        if dy * dy > r_sq:
            continue
        dx = int(math.sqrt(r_sq - dy * dy))
        for x in range(max(0, cx - dx), min(WIDTH, cx + dx + 1)):
            set_pixel(x, y, color)

def draw_filled_ellipse(cx, cy, rx, ry, color):
    for y in range(max(0, cy - ry), min(HEIGHT, cy + ry + 1)):
        dy = y - cy
        # (x - cx)^2 / rx^2 + dy^2 / ry^2 <= 1
        # (x - cx)^2 <= rx^2 * (1 - dy^2 / ry^2)
        val = 1 - (dy * dy) / (ry * ry)
        if val < 0: continue
        dx = int(rx * math.sqrt(val))
        for x in range(max(0, cx - dx), min(WIDTH, cx + dx + 1)):
            set_pixel(x, y, color)

def draw_filled_rotated_ellipse(cx, cy, rx, ry, angle, color):
    # Rotate by -angle to align with axes
    theta = math.radians(-angle)
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    
    # Bounding box
    cos_t_abs = abs(cos_t)
    sin_t_abs = abs(sin_t)
    width = rx * cos_t_abs + ry * sin_t_abs
    height = rx * sin_t_abs + ry * cos_t_abs
    
    for y in range(max(0, int(cy - height)), min(HEIGHT, int(cy + height) + 1)):
        for x in range(max(0, int(cx - width)), min(WIDTH, int(cx + width) + 1)):
            dx = x - cx
            dy = y - cy
            # Rotate point back
            rx_p = dx * cos_t - dy * sin_t
            ry_p = dx * sin_t + dy * cos_t
            if (rx_p / rx)**2 + (ry_p / ry)**2 <= 1:
                set_pixel(x, y, color)

def draw_line(x1, y1, x2, y2, thickness, color):
    steps = int(math.sqrt((x2 - x1)**2 + (y2 - y1)**2) / 0.5)
    if steps == 0: steps = 1
    for i in range(steps + 1):
        t = i / steps
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        draw_filled_circle(int(x), int(y), thickness / 2, color)

def draw_arc(cx, cy, r, start_angle, end_angle, thickness, color):
    for a in range(start_angle, end_angle + 1):
        theta = math.radians(a)
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        draw_filled_circle(int(x), int(y), thickness / 2, color)

def draw_all():
    # S0: Background
    # Already done in canvas init
    
    # S1: Halo
    draw_filled_circle(512, 512, 440, COLORS["halo"])
    
    # S2: Kitten body
    draw_filled_ellipse(512, 720, 285, 235, COLORS["fur_outline"])
    draw_filled_ellipse(512, 720, 277, 227, COLORS["kitten_fur"])
    
    # S3: Belly
    draw_filled_ellipse(512, 760, 175, 150, COLORS["belly"])
    
    # S4: Feet
    draw_filled_ellipse(370, 890, 95, 60, COLORS["fur_outline"])
    draw_filled_ellipse(370, 890, 87, 52, COLORS["kitten_fur"])
    draw_filled_ellipse(370, 895, 30, 14, COLORS["pink"])
    draw_filled_ellipse(654, 890, 95, 60, COLORS["fur_outline"])
    draw_filled_ellipse(654, 890, 87, 52, COLORS["kitten_fur"])
    draw_filled_ellipse(654, 895, 30, 14, COLORS["pink"])
    
    # S5: Ears
    draw_filled_rotated_ellipse(355, 215, 85, 95, -15, COLORS["fur_outline"])
    draw_filled_rotated_ellipse(355, 215, 77, 87, -15, COLORS["kitten_fur"])
    draw_filled_rotated_ellipse(355, 225, 45, 55, -15, COLORS["pink"])
    draw_filled_rotated_ellipse(669, 215, 85, 95, 15, COLORS["fur_outline"])
    draw_filled_rotated_ellipse(669, 215, 77, 87, 15, COLORS["kitten_fur"])
    draw_filled_rotated_ellipse(669, 225, 45, 55, 15, COLORS["pink"])
    
    # S6: Head
    draw_filled_circle(512, 395, 215, COLORS["fur_outline"])
    draw_filled_circle(512, 395, 207, COLORS["kitten_fur"])
    
    # S7: Bow
    draw_filled_rotated_ellipse(640, 135, 32, 20, -25, COLORS["bow"])
    draw_filled_rotated_ellipse(700, 135, 32, 20, 25, COLORS["bow"])
    draw_filled_circle(670, 135, 16, COLORS["bow_centre"])
    
    # S8: Chick body
    draw_filled_ellipse(512, 635, 122, 112, COLORS["chick_outline"])
    draw_filled_ellipse(512, 635, 114, 104, COLORS["chick_yellow"])
    
    # S9: Chick tuft
    draw_filled_circle(482, 538, 20, COLORS["chick_yellow"])
    draw_filled_circle(512, 528, 22, COLORS["chick_yellow"])
    draw_filled_circle(542, 538, 20, COLORS["chick_yellow"])
    
    # S10: Chick wings
    draw_filled_rotated_ellipse(415, 650, 22, 38, -15, COLORS["chick_wing"])
    draw_filled_rotated_ellipse(609, 650, 22, 38, 15, COLORS["chick_wing"])
    
    # S11: Chick face
    draw_filled_circle(472, 615, 14, COLORS["eye_brown"])
    draw_filled_circle(477, 610, 5, COLORS["white"])
    draw_filled_circle(552, 615, 14, COLORS["eye_brown"])
    draw_filled_circle(557, 610, 5, COLORS["white"])
    draw_filled_ellipse(512, 650, 22, 15, COLORS["beak"])
    draw_filled_ellipse(448, 655, 18, 10, COLORS["chick_blush"])
    draw_filled_ellipse(576, 655, 18, 10, COLORS["chick_blush"])
    
    # S12: Kitten paws
    draw_filled_rotated_ellipse(418, 670, 58, 78, -12, COLORS["fur_outline"])
    draw_filled_rotated_ellipse(418, 670, 50, 70, -12, COLORS["kitten_fur"])
    draw_filled_ellipse(418, 700, 20, 12, COLORS["pink"])
    draw_filled_rotated_ellipse(606, 670, 58, 78, 12, COLORS["fur_outline"])
    draw_filled_rotated_ellipse(606, 670, 50, 70, 12, COLORS["kitten_fur"])
    draw_filled_ellipse(606, 700, 20, 12, COLORS["pink"])
    
    # S13: Kitten face
    draw_filled_ellipse(435, 385, 40, 50, COLORS["eye_brown"])
    draw_filled_circle(448, 368, 14, COLORS["white"])
    draw_filled_circle(425, 400, 6, COLORS["white"])
    draw_filled_ellipse(589, 385, 40, 50, COLORS["eye_brown"])
    draw_filled_circle(602, 368, 14, COLORS["white"])
    draw_filled_circle(579, 400, 6, COLORS["white"])
    draw_filled_ellipse(512, 462, 24, 17, COLORS["nose"])
    draw_arc(488, 478, 26, 15, 105, 5, COLORS["mouth"])
    draw_arc(536, 478, 26, 75, 165, 5, COLORS["mouth"])
    draw_filled_ellipse(378, 472, 38, 22, COLORS["blush"])
    draw_filled_ellipse(646, 472, 38, 22, COLORS["blush"])
    
    # S14: Whiskers
    draw_line(310, 430, 390, 445, 4, COLORS["whisker"])
    draw_line(312, 470, 392, 468, 4, COLORS["whisker"])
    draw_line(714, 430, 634, 445, 4, COLORS["whisker"])
    draw_line(712, 470, 632, 468, 4, COLORS["whisker"])

def create_png():
    draw_all()
    
    # PNG structure
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff)
    
    # IDAT
    raw_data = bytearray()
    for y in range(HEIGHT):
        raw_data.append(0) # Filter byte 0
        raw_data.extend(canvas[y * WIDTH * 3 : (y + 1) * WIDTH * 3])
        
    compressed_data = zlib.compress(raw_data, 9)
    idat = struct.pack('>I', len(compressed_data)) + b'IDAT' + compressed_data + struct.pack('>I', zlib.crc32(b'IDAT' + compressed_data) & 0xffffffff)
    
    # IEND
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', zlib.crc32(b'IEND') & 0xffffffff)
    
    return signature + ihdr + idat + iend

if __name__ == "__main__":
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    
    png_data = create_png()
    with open(os.path.join(output_dir, "entry.png"), "wb") as f:
        f.write(png_data)
