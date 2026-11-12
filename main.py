import struct
import zlib
import math
import os

# --- Configuration ---
WIDTH, HEIGHT = 1024, 1024
SCALE = 2
CANVAS_W, CANVAS_H = WIDTH * SCALE, HEIGHT * SCALE
CANVAS_SIZE = CANVAS_W * CANVAS_H * 3

# --- Palette ---
PALETTE = {
    'bg_top': (255, 247, 236),
    'bg_bot': (255, 228, 194),
    'halo': (255, 226, 178),
    'shadow': (214, 150, 100, 0.38),
    'mint': (121, 209, 166),
    'outline': (62, 143, 104),
    'wings': (92, 191, 146),
    'belly': (255, 243, 220),
    'horns': (255, 233, 184),
    'blush': (255, 128, 138, 0.8),
    'star_gold': (255, 197, 61),
    'star_outline': (217, 142, 4),
    'ink': (43, 43, 58),
    'mouth': (74, 122, 99),
    'heart': (255, 143, 163),
    'white': (255, 255, 255),
}

# --- Canvas ---
canvas = bytearray(CANVAS_SIZE)

def set_pixel(x, y, r, g, b, alpha=1.0):
    if not (0 <= x < CANVAS_W and 0 <= y < CANVAS_H):
        return
    idx = (y * CANVAS_W + x) * 3
    if alpha >= 1.0:
        canvas[idx:idx+3] = bytes([r, g, b])
    else:
        # Simple alpha blending
        canvas[idx] = int(canvas[idx] * (1 - alpha) + r * alpha)
        canvas[idx+1] = int(canvas[idx+1] * (1 - alpha) + g * alpha)
        canvas[idx+2] = int(canvas[idx+2] * (1 - alpha) + b * alpha)

def fill_row(y, x0, x1, rgb):
    if not (0 <= y < CANVAS_H): return
    x0 = max(0, min(CANVAS_W - 1, int(x0)))
    x1 = max(0, min(CANVAS_W - 1, int(x1)))
    if x0 > x1: x0, x1 = x1, x0
    r, g, b = rgb[:3]
    row_start = y * CANVAS_W * 3
    for x in range(x0, x1 + 1):
        idx = row_start + x * 3
        canvas[idx:idx+3] = bytes([r, g, b])

# --- Primitives ---
def fill_ellipse(cx, cy, rx, ry, rgb):
    cx, cy, rx, ry = int(cx * SCALE), int(cy * SCALE), int(rx * SCALE), int(ry * SCALE)
    for y in range(max(0, cy - ry), min(CANVAS_H, cy + ry)):
        dy = y - cy
        dx = int(rx * math.sqrt(max(0, 1 - (dy / ry) ** 2)))
        fill_row(y, cx - dx, cx + dx, rgb)

def fill_polygon(pts, rgb):
    pts = [(p[0] * SCALE, p[1] * SCALE) for p in pts]
    if not pts: return
    edges = []
    for i in range(len(pts)):
        p1, p2 = pts[i], pts[(i + 1) % len(pts)]
        if p1[1] != p2[1]:
            edges.append((min(p1[1], p2[1]), max(p1[1], p2[1]), p1, p2))
    min_y = int(min(p[1] for p in pts))
    max_y = int(max(p[1] for p in pts))
    for y in range(max(0, min_y), min(CANVAS_H, max_y + 1)):
        intersections = []
        for ymin, ymax, p1, p2 in edges:
            if ymin <= y < ymax:
                x = p1[0] + (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1])
                intersections.append(x)
        intersections.sort()
        for i in range(0, len(intersections), 2):
            fill_row(y, intersections[i], intersections[i+1], rgb)

def draw_circle(cx, cy, r, rgb):
    fill_ellipse(cx, cy, r, r, rgb)

def draw_bezier_filled(pts, ctrl, rgb):
    # Simplified Bezier fill: just connect the points
    fill_polygon(pts + ctrl, rgb)

def draw_capsule(p1, p2, r, rgb):
    d = math.hypot(p2[0]-p1[0], p2[1]-p1[1])
    steps = max(1, int(d / (r/2)))
    for i in range(steps + 1):
        t = i / steps
        x = p1[0] + (p2[0]-p1[0]) * t
        y = p1[1] + (p2[1]-p1[1]) * t
        draw_circle(x, y, r, rgb)

def draw_bezier_quad(p0, p1, p2, r, rgb):
    def B(t):
        return ((1-t)**2*p0[0] + 2*(1-t)*t*p1[0] + t**2*p2[0],
                (1-t)**2*p0[1] + 2*(1-t)*t*p1[1] + t**2*p2[1])
    pts = [B(i/24) for i in range(25)]
    for i in range(len(pts)-1):
        draw_capsule(pts[i], pts[i+1], r, rgb)

def draw_wings(cx, cy, mirror=False):
    pts = [(340, 545), (285, 530), (248, 565), (248, 565), (275, 590), (300, 605), (300, 605), (330, 615), (355, 635), (355, 635), (350, 590), (340, 545)]
    if mirror: pts = [(1024 - p[0], p[1]) for p in pts]
    fill_polygon(pts, PALETTE['wings'])

def draw_horns(cx, cy, mirror=False):
    pts = [(372, 235), (350, 180), (368, 152), (368, 152), (402, 190), (418, 230)]
    if mirror: pts = [(1024 - p[0], p[1]) for p in pts]
    fill_polygon(pts, PALETTE['horns'])

def draw_ears(cx, cy, mirror=False):
    draw_circle(cx, cy, 40, PALETTE['outline'])
    draw_circle(cx, cy, 33, PALETTE['mint'])
    draw_circle(cx, cy, 18, PALETTE['belly'])

def draw_lashes(ex, ey, mirror=False):
    for a in [195, 220, 245] if not mirror else [295, 320, 345]:
        rad = math.radians(a)
        p1 = (ex + 50*math.cos(rad), ey + 60*math.sin(rad))
        p2 = (ex + (50+18)*math.cos(rad), ey + (60+18)*math.sin(rad))
        draw_capsule(p1, p2, 4.5, PALETTE['ink'])

def draw_smile(sx, sy):
    draw_bezier_quad((482, 488), (512, 508), (543, 486), 3.5, PALETTE['mouth'])

def draw_heart(hx, hy):
    def get_heart_pts(scale_factor):
        pts = []
        for i in range(72):
            t = i / 72 * 2 * math.pi
            x = 16 * math.sin(t)**3
            y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
            rad = math.radians(15)
            rx = x * math.cos(rad) - y * math.sin(rad)
            ry = x * math.sin(rad) + y * math.cos(rad)
            pts.append((hx + rx * scale_factor / 16, hy - ry * scale_factor / 16))
        return pts
    fill_polygon(get_heart_pts(32.4), (214, 90, 110))
    fill_polygon(get_heart_pts(30), (255, 143, 163))

def draw_star(cx, cy):
    def get_star_pts(outer_r, inner_r):
        pts = []
        for i in range(10):
            angle = math.radians(12 + i * 36)
            r = outer_r if i % 2 == 0 else inner_r
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        return pts
    fill_polygon(get_star_pts(76.3, 33.9), PALETTE['star_outline'])
    fill_polygon(get_star_pts(72, 32), PALETTE['star_gold'])

    # Face
    draw_bezier_quad((493-9, 610), (493, 610-7), (493+9, 610), 3, PALETTE['ink'])
    draw_bezier_quad((533-9, 608), (533, 608-7), (533+9, 608), 3, PALETTE['ink'])
    draw_bezier_quad((512-15, 625), (512, 625-5), (512+15, 625), 3, PALETTE['ink'])

def draw_arms(cx, cy, mirror=False):
    if mirror:
        pts = [(640, 595), (600, 653), (570, 648)]
    else:
        pts = [(385, 600), (425, 655), (455, 650)]
    for i in range(len(pts)-1):
        draw_capsule(pts[i], pts[i+1], 39, PALETTE['outline'])
    for i in range(len(pts)-1):
        draw_capsule(pts[i], pts[i+1], 32, PALETTE['mint'])

def draw_pupil_highlights(ex, ey):
    fill_ellipse(ex-8, ey-11, 9, 9, PALETTE['white'])
    fill_ellipse(ex+10, ey+12, 5, 5, PALETTE['white'])

# --- Scene ---
def render():
    # 1. Gradient
    for y in range(CANVAS_H):
        t = y / CANVAS_H
        r = int(PALETTE['bg_top'][0] * (1 - t) + PALETTE['bg_bot'][0] * t)
        g = int(PALETTE['bg_top'][1] * (1 - t) + PALETTE['bg_bot'][1] * t)
        b = int(PALETTE['bg_top'][2] * (1 - t) + PALETTE['bg_bot'][2] * t)
        fill_row(y, 0, CANVAS_W - 1, (r, g, b))

# --- Scene ---
def rotate_point(pt, cx, cy, angle_deg):
    angle = math.radians(angle_deg)
    x, y = pt[0] - cx, pt[1] - cy
    new_x = x * math.cos(angle) - y * math.sin(angle)
    new_y = x * math.sin(angle) + y * math.cos(angle)
    return (new_x + cx, new_y + cy)

def render():
    # 1. Gradient
    for y in range(CANVAS_H):
        t = y / CANVAS_H
        r = int(PALETTE['bg_top'][0] * (1 - t) + PALETTE['bg_bot'][0] * t)
        g = int(PALETTE['bg_top'][1] * (1 - t) + PALETTE['bg_bot'][1] * t)
        b = int(PALETTE['bg_top'][2] * (1 - t) + PALETTE['bg_bot'][2] * t)
        fill_row(y, 0, CANVAS_W - 1, (r, g, b))

    # 2. Halo
    fill_ellipse(512, 500, 335, 335, PALETTE['halo'])
    
    # 3. Sparkles / Dots
    for (cx, cy, r) in [(170, 215, 16), (855, 175, 14), (872, 430, 12), (148, 470, 13), (835, 690, 11)]:
        # Simple sparkle as 4-point diamond
        pts = [(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)]
        fill_polygon(pts, PALETTE['star_gold'])
    for (cx, cy, r) in [(240, 300, 5), (790, 300, 5), (700, 160, 4)]:
        draw_circle(cx, cy, r, PALETTE['heart'])

    # 4. Shadow
    fill_ellipse(512, 852, 255, 34, (*PALETTE['shadow'][:3], 0.38))

    # 5. Wings
    draw_wings(512, 655)
    draw_wings(512, 655, mirror=True)

    # 6. Body
    fill_ellipse(512, 655, 242, 202, PALETTE['outline'])
    fill_ellipse(512, 655, 235, 195, PALETTE['mint'])
    
    # 6b. Belly
    fill_ellipse(512, 705, 148, 122, PALETTE['belly'])

    # 7. Feet
    for cx in [415, 610]:
        fill_ellipse(cx, 838, 62, 35, PALETTE['outline'])
        fill_ellipse(cx, 838, 55, 28, PALETTE['mint'])
        fill_ellipse(cx, 844, 36, 16, PALETTE['belly'])

    # 8. Ears
    draw_ears(332, 318)
    draw_ears(682, 308)

    # 9. Horns
    draw_horns(505, 372)
    draw_horns(505, 372, mirror=True)

    # 10. Head
    fill_ellipse(505, 372, 192, 192, PALETTE['outline'])
    fill_ellipse(505, 372, 185, 185, PALETTE['mint'])

    # 11. Head tilt (applying rotation to features)
    # The spec asks for a rotation, I will apply it to eyes, snout, mouth, nostrils.
    # Features need to be drawn now to be on top.
    
    # 12. Eyes
    eye_centers = [rotate_point((432, 362), 505, 372, 8), rotate_point((592, 348), 505, 372, 8)]
    for (ex, ey) in eye_centers:
        fill_ellipse(ex, ey, 55, 65, PALETTE['outline'])
        fill_ellipse(ex, ey, 50, 60, PALETTE['white'])
        # Pupils
        px, py = ex + (8 if ex < 505 else -8), ey + 8
        fill_ellipse(px, py, 26, 32, PALETTE['ink'])
        draw_pupil_highlights(px, py)

    # 13. Lashes
    draw_lashes(eye_centers[0][0], eye_centers[0][1])
    draw_lashes(eye_centers[1][0], eye_centers[1][1], mirror=True)

    # 13. Blush
    for (bx, by) in [rotate_point((388, 442), 505, 372, 8), rotate_point((632, 428), 505, 372, 8)]:
        fill_ellipse(bx, by, 32, 19, PALETTE['blush'])

    # 14. Snout / Nostrils / Smile
    sx, sy = rotate_point((510, 462), 505, 372, 8)
    fill_ellipse(sx, sy, 74, 48, PALETTE['belly'])
    draw_smile(512, 462)
    for (nx, ny) in [rotate_point((493, 452), 505, 372, 8), rotate_point((528, 450), 505, 372, 8)]:
        draw_circle(nx, ny, 4.5, PALETTE['ink'])

    # 15. Star
    draw_star(512, 625)

    # 16. Arms/Paws
    draw_arms(512, 655)
    for cx in [425, 600]:
        fill_ellipse(cx, 650, 39, 39, PALETTE['outline'])
        fill_ellipse(cx, 650, 32, 32, PALETTE['mint'])

    # 17. Heart
    draw_heart(692, 252)

# --- PNG Encoder ---
def write_png(filename):
    # Downsample 2048x2048 to 1024x1024
    out_canvas = bytearray(WIDTH * HEIGHT * 3)
    for y in range(HEIGHT):
        for x in range(WIDTH):
            # Simple 2x2 box average
            r, g, b = 0, 0, 0
            for sy in range(SCALE):
                for sx in range(SCALE):
                    idx = ((y * SCALE + sy) * CANVAS_W + (x * SCALE + sx)) * 3
                    r += canvas[idx]
                    g += canvas[idx+1]
                    b += canvas[idx+2]
            idx = (y * WIDTH + x) * 3
            out_canvas[idx] = r // 4
            out_canvas[idx+1] = g // 4
            out_canvas[idx+2] = b // 4
    
    # Compress
    compressed = bytearray()
    for y in range(HEIGHT):
        compressed.append(0) # Filter None
        row_start = y * WIDTH * 3
        compressed.extend(out_canvas[row_start : row_start + WIDTH * 3])
    idat_data = zlib.compress(compressed, 9)
    
    # Write file
    with open(filename, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
        
        def write_chunk(type, data):
            f.write(struct.pack('>I', len(data)))
            f.write(type)
            f.write(data)
            f.write(struct.pack('>I', zlib.crc32(type + data) & 0xFFFFFFFF))
        
        write_chunk(b'IHDR', struct.pack('>IIBBBBB', WIDTH, HEIGHT, 8, 2, 0, 0, 0))
        write_chunk(b'IDAT', idat_data)
        write_chunk(b'IEND', b'')

# --- Run ---
if __name__ == '__main__':
    render()
    output_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(output_dir, exist_ok=True)
    write_png(os.path.join(output_dir, 'entry.png'))
