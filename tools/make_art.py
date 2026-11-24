#!/usr/bin/env python3
"""Second Glance - all art drawn in code with PIL. No AI images, no downloads.
Original styling-atelier-above-a-night-market theme at dusk: indigo walls,
warm amber stall light, smoke wisps, a clothing rack and a mirror frame
where the model stands. Flat bright garments with strong dark outlines so
each item reads at 96x96 in the wardrobe grid.

Canvas notes: PIL y is down. A 200x420 garment canvas maps onto the GUI
model node (200 wide x 420 tall, feet at the bottom), so PIL y=0 is the
top of the head and PIL y=420 is the feet. Body regions (PIL coords):
head y 10-90, neck y 85-100, torso y 95-235 (x 55-145, arms x 30-170),
legs y 235-375 (x 70-130), feet y 370-415.
"""
import glob
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.join(os.path.dirname(HERE), "art")
os.makedirs(ART, exist_ok=True)

rng = random.Random(20261123)

OUT = (45, 35, 30, 255)      # dark outline
SKIN = (245, 205, 170, 255)
SKIN_D = (225, 180, 145, 255)
HAIR = (62, 42, 36, 255)

# garment palette
RED = (220, 60, 60, 255)
RED_D = (170, 35, 35, 255)
BLUE = (60, 110, 220, 255)
BLUE_D = (35, 75, 175, 255)
GREEN = (70, 170, 90, 255)
GREEN_D = (45, 125, 60, 255)
YELLOW = (250, 205, 60, 255)
YELLOW_D = (205, 155, 25, 255)
PURPLE = (150, 90, 200, 255)
PURPLE_D = (110, 60, 160, 255)
BLACK = (48, 48, 58, 255)
WHITE = (245, 245, 240, 255)
BROWN = (150, 100, 55, 255)
BROWN_D = (110, 70, 35, 255)
GOLD = (230, 180, 60, 255)
PINK = (245, 140, 180, 255)
GREY = (200, 200, 205, 255)
GREY_D = (160, 160, 168, 255)


def save(img, name):
    p = os.path.join(ART, name)
    img.save(p, "PNG")
    print("wrote", p, img.size)


def circle(d, cx, cy, r, fill, outline=None, width=1):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill,
              outline=outline, width=width)


def find_font(size):
    for pat in ("/usr/share/fonts/**/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/**/LiberationSans-Bold.ttf"):
        for p in sorted(glob.glob(pat, recursive=True)):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def blank(w=200, h=420):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


# -------------------------------------------------------------------- body --
# Base model: friendly face, dark hair, plain light-grey tee + grey
# trousers as underclothes (empty slots read as undressed, never naked).

def make_body():
    img = blank()
    d = ImageDraw.Draw(img)
    # legs (trousers) first, then torso, then arms, then head
    # trousers: two legs with a centre gap
    d.rounded_rectangle([70, 230, 99, 378], radius=8, fill=GREY_D, outline=OUT, width=3)
    d.rounded_rectangle([101, 230, 130, 378], radius=8, fill=GREY_D, outline=OUT, width=3)
    d.rectangle([70, 230, 130, 246], fill=GREY_D, outline=OUT, width=3)
    d.line([(84, 250), (84, 370)], fill=(130, 130, 140, 255), width=2)
    d.line([(116, 250), (116, 370)], fill=(130, 130, 140, 255), width=2)
    # bare feet
    d.ellipse([70, 372, 98, 398], fill=SKIN, outline=OUT, width=3)
    d.ellipse([102, 372, 130, 398], fill=SKIN, outline=OUT, width=3)
    # arms (skin, at the sides)
    d.rounded_rectangle([38, 100, 58, 228], radius=9, fill=SKIN, outline=OUT, width=3)
    d.rounded_rectangle([142, 100, 162, 228], radius=9, fill=SKIN, outline=OUT, width=3)
    circle(d, 48, 232, 9, SKIN, OUT, 3)
    circle(d, 152, 232, 9, SKIN, OUT, 3)
    # tee torso + short sleeves
    d.rounded_rectangle([58, 95, 142, 238], radius=12, fill=GREY, outline=OUT, width=3)
    d.rounded_rectangle([40, 98, 62, 142], radius=8, fill=GREY, outline=OUT, width=3)
    d.rounded_rectangle([138, 98, 160, 142], radius=8, fill=GREY, outline=OUT, width=3)
    # crew neckline
    d.arc([86, 92, 114, 112], 0, 180, fill=OUT, width=3)
    # neck
    d.rectangle([92, 82, 108, 100], fill=SKIN, outline=OUT, width=3)
    # ears
    circle(d, 70, 56, 7, SKIN, OUT, 3)
    circle(d, 130, 56, 7, SKIN, OUT, 3)
    # head
    d.ellipse([70, 12, 130, 92], fill=SKIN, outline=OUT, width=3)
    # hair: cap over the top + side locks
    d.pieslice([66, 4, 134, 62], 180, 360, fill=HAIR)
    d.rounded_rectangle([66, 8, 80, 74], radius=6, fill=HAIR)
    d.rounded_rectangle([120, 8, 134, 74], radius=6, fill=HAIR)
    d.arc([70, 10, 130, 60], 180, 360, fill=OUT, width=3)
    # face
    circle(d, 88, 54, 4, OUT)
    circle(d, 112, 54, 4, OUT)
    d.arc([88, 62, 112, 78], 15, 165, fill=OUT, width=3)
    circle(d, 80, 66, 4, (245, 150, 140, 255))
    circle(d, 120, 66, 4, (245, 150, 140, 255))
    save(img, "body.png")


make_body()

# ---------------------------------------------------------------- garments --
# Every garment is a full 200x420 transparent canvas, drawn in its body
# region, so layering = same position/size over body.png.

def garment(name, fn):
    img = blank()
    d = ImageDraw.Draw(img)
    fn(d)
    save(img, name)


def torso_base(d, fill, outline=OUT, w=3, x0=55, x1=145, y0=95, y1=238):
    d.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=fill,
                        outline=outline, width=w)


def sleeve_short(d, fill, side):
    # side: -1 left, +1 right
    x0 = 38 if side < 0 else 140
    x1 = 62 if side < 0 else 162
    d.rounded_rectangle([x0, 98, x1, 142], radius=8, fill=fill,
                        outline=OUT, width=3)


def sleeve_long(d, fill, side):
    x0 = 36 if side < 0 else 142
    x1 = 58 if side < 0 else 164
    d.rounded_rectangle([x0, 98, x1, 228], radius=9, fill=fill,
                        outline=OUT, width=3)
    d.line([(x0 + 4, 200), (x1 - 4, 200)], fill=OUT, width=2)


# ---- tops ----

def top_red_tee(d):
    torso_base(d, RED)
    sleeve_short(d, RED, -1)
    sleeve_short(d, RED, 1)
    d.arc([86, 92, 114, 112], 0, 180, fill=OUT, width=3)
    d.line([(60, 228), (140, 228)], fill=RED_D, width=3)


def top_blue_blouse(d):
    torso_base(d, BLUE)
    sleeve_long(d, BLUE, -1)
    sleeve_long(d, BLUE, 1)
    # V collar
    d.polygon([(84, 96), (100, 122), (116, 96)], fill=WHITE, outline=OUT)
    # buttons down the centre
    for y in (140, 165, 190, 215):
        circle(d, 100, y, 4, WHITE, OUT, 2)
    d.line([(100, 122), (100, 235)], fill=BLUE_D, width=2)
    # flared hem
    d.polygon([(55, 225), (145, 225), (150, 240), (50, 240)], fill=BLUE,
              outline=OUT)


def top_green_sweater(d):
    # chunky: wider body, turtleneck, ribbed hem
    d.rounded_rectangle([50, 95, 150, 240], radius=14, fill=GREEN,
                        outline=OUT, width=3)
    sleeve_long(d, GREEN, -1)
    sleeve_long(d, GREEN, 1)
    d.rounded_rectangle([84, 84, 116, 106], radius=8, fill=GREEN_D,
                        outline=OUT, width=3)
    d.line([(56, 224), (144, 224)], fill=GREEN_D, width=4)
    d.line([(56, 232), (144, 232)], fill=GREEN_D, width=4)
    # knit dots
    for (x, y) in [(70, 130), (100, 150), (130, 130), (85, 180), (115, 180)]:
        circle(d, x, y, 3, GREEN_D)


def top_black_jacket(d):
    # open jacket: two panels + lapels over a white shirt strip
    d.rounded_rectangle([78, 96, 122, 238], radius=8, fill=WHITE,
                        outline=OUT, width=3)
    d.polygon([(55, 95), (92, 95), (86, 238), (52, 238)], fill=BLACK,
              outline=OUT)
    d.polygon([(108, 95), (145, 95), (148, 238), (114, 238)], fill=BLACK,
              outline=OUT)
    sleeve_long(d, BLACK, -1)
    sleeve_long(d, BLACK, 1)
    # lapels
    d.polygon([(84, 96), (96, 96), (88, 140), (78, 118)], fill=(70, 70, 82, 255), outline=OUT)
    d.polygon([(116, 96), (104, 96), (112, 140), (122, 118)], fill=(70, 70, 82, 255), outline=OUT)
    # zipper teeth
    for y in range(100, 236, 12):
        d.line([(96, y), (104, y)], fill=GOLD, width=2)


def top_yellow_shirt(d):
    torso_base(d, YELLOW)
    sleeve_short(d, YELLOW, -1)
    sleeve_short(d, YELLOW, 1)
    # collar
    d.polygon([(84, 96), (100, 114), (116, 96)], fill=YELLOW_D, outline=OUT)
    for y in (130, 158, 186, 214):
        circle(d, 100, y, 4, WHITE, OUT, 2)
    # chest pocket
    d.rectangle([112, 140, 132, 162], fill=YELLOW_D, outline=OUT, width=2)


def top_purple_hoodie(d):
    # hood bump behind the neck
    d.ellipse([72, 72, 128, 112], fill=PURPLE_D, outline=OUT, width=3)
    d.ellipse([82, 82, 118, 106], fill=(90, 45, 130, 255))
    torso_base(d, PURPLE)
    sleeve_long(d, PURPLE, -1)
    sleeve_long(d, PURPLE, 1)
    # kangaroo pocket
    d.polygon([(72, 195), (128, 195), (136, 236), (64, 236)], fill=PURPLE_D,
              outline=OUT)
    # drawstrings
    d.line([(92, 108), (90, 138)], fill=WHITE, width=3)
    d.line([(108, 108), (110, 138)], fill=WHITE, width=3)
    circle(d, 90, 140, 3, WHITE, OUT, 2)
    circle(d, 110, 140, 3, WHITE, OUT, 2)


TOPS = [
    ("g_top_1.png", top_red_tee),
    ("g_top_2.png", top_blue_blouse),
    ("g_top_3.png", top_green_sweater),
    ("g_top_4.png", top_black_jacket),
    ("g_top_5.png", top_yellow_shirt),
    ("g_top_6.png", top_purple_hoodie),
]

# ---- bottoms ----

def bottom_blue_jeans(d):
    d.rounded_rectangle([70, 222, 99, 378], radius=8, fill=BLUE, outline=OUT, width=3)
    d.rounded_rectangle([101, 222, 130, 378], radius=8, fill=BLUE, outline=OUT, width=3)
    d.rectangle([70, 222, 130, 240], fill=BLUE_D, outline=OUT, width=3)
    # pockets + seams
    d.polygon([(72, 242), (88, 242), (88, 258), (72, 250)], fill=BLUE_D, outline=OUT)
    d.polygon([(128, 242), (112, 242), (112, 258), (128, 250)], fill=BLUE_D, outline=OUT)
    d.line([(84, 260), (84, 370)], fill=BLUE_D, width=2)
    d.line([(116, 260), (116, 370)], fill=BLUE_D, width=2)


def bottom_red_skirt(d):
    # A-line flare with pleats
    d.polygon([(68, 222), (132, 222), (146, 322), (54, 322)], fill=RED,
              outline=OUT)
    d.line([(70, 222), (70, 320)], fill=RED_D, width=2)
    d.line([(100, 222), (100, 322)], fill=RED_D, width=2)
    d.line([(130, 222), (130, 320)], fill=RED_D, width=2)
    d.rectangle([68, 222, 132, 238], fill=RED_D, outline=OUT, width=3)
    # legs below the hem (skin) so the skirt does not float
    d.rounded_rectangle([76, 322, 96, 378], radius=7, fill=SKIN, outline=OUT, width=3)
    d.rounded_rectangle([104, 322, 124, 378], radius=7, fill=SKIN, outline=OUT, width=3)


def bottom_black_trousers(d):
    d.rounded_rectangle([72, 222, 99, 378], radius=6, fill=BLACK, outline=OUT, width=3)
    d.rounded_rectangle([101, 222, 128, 378], radius=6, fill=BLACK, outline=OUT, width=3)
    d.rectangle([72, 222, 128, 238], fill=(70, 70, 82, 255), outline=OUT, width=3)
    # creases
    d.line([(85, 246), (85, 372)], fill=(90, 90, 105, 255), width=2)
    d.line([(115, 246), (115, 372)], fill=(90, 90, 105, 255), width=2)


def bottom_yellow_shorts(d):
    d.rounded_rectangle([66, 222, 99, 302], radius=10, fill=YELLOW, outline=OUT, width=3)
    d.rounded_rectangle([101, 222, 134, 302], radius=10, fill=YELLOW, outline=OUT, width=3)
    d.rectangle([66, 222, 134, 238], fill=YELLOW_D, outline=OUT, width=3)
    d.rectangle([66, 288, 99, 302], fill=YELLOW_D, outline=OUT, width=2)
    d.rectangle([101, 288, 134, 302], fill=YELLOW_D, outline=OUT, width=2)
    # legs below
    d.rounded_rectangle([74, 302, 94, 378], radius=7, fill=SKIN, outline=OUT, width=3)
    d.rounded_rectangle([106, 302, 126, 378], radius=7, fill=SKIN, outline=OUT, width=3)


def bottom_green_skirt(d):
    # straight pencil skirt with a slit
    d.polygon([(70, 222), (130, 222), (128, 332), (72, 332)], fill=GREEN,
              outline=OUT)
    d.rectangle([70, 222, 130, 238], fill=GREEN_D, outline=OUT, width=3)
    d.polygon([(96, 332), (106, 332), (104, 300), (98, 300)], fill=SKIN,
              outline=OUT)
    d.rounded_rectangle([76, 332, 96, 378], radius=7, fill=SKIN, outline=OUT, width=3)
    d.rounded_rectangle([104, 332, 124, 378], radius=7, fill=SKIN, outline=OUT, width=3)


def bottom_brown_cargo(d):
    d.rounded_rectangle([68, 222, 99, 378], radius=8, fill=BROWN, outline=OUT, width=3)
    d.rounded_rectangle([101, 222, 132, 378], radius=8, fill=BROWN, outline=OUT, width=3)
    d.rectangle([68, 222, 132, 240], fill=BROWN_D, outline=OUT, width=3)
    # cargo pockets on the outer thighs
    d.rectangle([62, 285, 82, 312], fill=BROWN_D, outline=OUT, width=2)
    d.rectangle([118, 285, 138, 312], fill=BROWN_D, outline=OUT, width=2)
    d.line([(62, 292), (82, 292)], fill=OUT, width=2)
    d.line([(118, 292), (138, 292)], fill=OUT, width=2)


BOTTOMS = [
    ("g_bottom_1.png", bottom_blue_jeans),
    ("g_bottom_2.png", bottom_red_skirt),
    ("g_bottom_3.png", bottom_black_trousers),
    ("g_bottom_4.png", bottom_yellow_shorts),
    ("g_bottom_5.png", bottom_green_skirt),
    ("g_bottom_6.png", bottom_brown_cargo),
]

# ---- shoes (feet y 365-415) ----

def shoe_pair(d, draw_one):
    draw_one(d, 68, 98)
    draw_one(d, 102, 132)


def shoes_white_sneakers(d):
    def one(d, x0, x1):
        d.rounded_rectangle([x0, 380, x1, 404], radius=10, fill=WHITE,
                            outline=OUT, width=3)
        d.rectangle([x0, 398, x1, 408], fill=(200, 200, 205, 255), outline=OUT, width=2)
        d.line([(x0 + 6, 388), (x1 - 6, 388)], fill=RED, width=3)
        for y in (382, 388, 394):
            pass
        d.line([(x0 + 10, 380), (x1 - 10, 380)], fill=(180, 180, 185, 255), width=2)
    shoe_pair(d, one)


def shoes_brown_boots(d):
    def one(d, x0, x1):
        d.rounded_rectangle([x0, 348, x1, 406], radius=8, fill=BROWN,
                            outline=OUT, width=3)
        d.rectangle([x0 - 2, 348, x1 + 2, 362], fill=BROWN_D, outline=OUT, width=2)
        d.rectangle([x0, 398, x1, 410], fill=BROWN_D, outline=OUT, width=2)
    shoe_pair(d, one)


def shoes_red_heels(d):
    def one(d, x0, x1):
        # pointed toe + stiletto heel
        d.polygon([(x0, 392), (x1, 392), (x1 + 2, 406), (x0 - 2, 406)],
                  fill=RED, outline=OUT)
        d.polygon([(x0 + 2, 392), (x1 - 2, 392), (x1 - 8, 380), (x0 + 8, 380)],
                  fill=RED, outline=OUT)
        d.rectangle([x0 + 4, 406, x0 + 10, 416], fill=RED_D, outline=OUT, width=2)
    shoe_pair(d, one)


def shoes_yellow_sandals(d):
    def one(d, x0, x1):
        # flat sole + straps over bare toes
        d.rounded_rectangle([x0 - 2, 398, x1 + 2, 410], radius=5,
                            fill=BROWN_D, outline=OUT, width=3)
        d.ellipse([x0, 388, x1, 402], fill=SKIN, outline=OUT, width=3)
        d.line([(x0 + 4, 394), (x1 - 4, 394)], fill=YELLOW, width=5)
        d.line([(x0 + 15, 390), (x0 + 15, 400)], fill=YELLOW, width=4)
    shoe_pair(d, one)


def shoes_blue_trainers(d):
    def one(d, x0, x1):
        d.rounded_rectangle([x0, 378, x1 + 4, 402], radius=10, fill=BLUE,
                            outline=OUT, width=3)
        d.rectangle([x0, 396, x1 + 4, 408], fill=WHITE, outline=OUT, width=2)
        d.line([(x0 + 8, 386), (x1 - 2, 386)], fill=WHITE, width=3)
        d.line([(x0 + 8, 392), (x1 - 2, 392)], fill=WHITE, width=3)
    shoe_pair(d, one)


SHOES = [
    ("g_shoes_1.png", shoes_white_sneakers),
    ("g_shoes_2.png", shoes_brown_boots),
    ("g_shoes_3.png", shoes_red_heels),
    ("g_shoes_4.png", shoes_yellow_sandals),
    ("g_shoes_5.png", shoes_blue_trainers),
]

# ---- hats (head y 0-60) ----

def hat_red_cap(d):
    d.pieslice([64, 8, 136, 66], 180, 360, fill=RED, outline=OUT, width=3)
    d.ellipse([58, 46, 142, 60], fill=RED, outline=OUT, width=3)
    circle(d, 100, 10, 4, RED_D, OUT, 2)
    d.line([(100, 14), (100, 46)], fill=RED_D, width=2)


def hat_green_beanie(d):
    d.pieslice([66, 4, 134, 56], 180, 360, fill=GREEN, outline=OUT, width=3)
    d.rounded_rectangle([64, 34, 136, 50], radius=6, fill=GREEN_D,
                        outline=OUT, width=3)
    for x in range(72, 132, 10):
        d.line([(x, 36), (x, 48)], fill=(30, 90, 45, 255), width=2)
    circle(d, 100, 8, 7, WHITE, OUT, 2)


def hat_yellow_sunhat(d):
    d.pieslice([74, 10, 126, 56], 180, 360, fill=YELLOW, outline=OUT, width=3)
    d.ellipse([44, 44, 156, 62], fill=YELLOW, outline=OUT, width=3)
    d.arc([74, 10, 126, 56], 180, 360, fill=YELLOW_D, width=3)
    d.line([(76, 42), (124, 42)], fill=RED, width=4)


def hat_purple_beret(d):
    # tilted flat disc
    d.ellipse([58, 12, 146, 44], fill=PURPLE, outline=OUT, width=3)
    d.line([(100, 10), (100, 4)], fill=OUT, width=3)
    circle(d, 100, 6, 4, PURPLE_D, OUT, 2)
    d.arc([62, 16, 142, 44], 200, 340, fill=PURPLE_D, width=3)


def hat_black_fedora(d):
    d.pieslice([76, 6, 124, 52], 180, 360, fill=BLACK, outline=OUT, width=3)
    d.ellipse([52, 40, 148, 58], fill=BLACK, outline=OUT, width=3)
    d.rectangle([76, 34, 124, 44], fill=GOLD, outline=OUT, width=2)


HATS = [
    ("g_hat_1.png", hat_red_cap),
    ("g_hat_2.png", hat_green_beanie),
    ("g_hat_3.png", hat_yellow_sunhat),
    ("g_hat_4.png", hat_purple_beret),
    ("g_hat_5.png", hat_black_fedora),
]

# ---- extras ----

def extra_red_scarf(d):
    # band around the neck + two tails down the front
    d.rounded_rectangle([76, 92, 124, 116], radius=10, fill=RED, outline=OUT, width=3)
    d.rounded_rectangle([84, 112, 100, 186], radius=6, fill=RED, outline=OUT, width=3)
    d.rounded_rectangle([104, 112, 120, 168], radius=6, fill=RED_D, outline=OUT, width=3)
    for x in range(86, 100, 5):
        d.line([(x, 186), (x, 194)], fill=RED, width=3)
    for x in range(106, 120, 5):
        d.line([(x, 168), (x, 176)], fill=RED_D, width=3)


def extra_gold_necklace(d):
    d.arc([78, 92, 122, 132], 0, 180, fill=GOLD, width=4)
    d.arc([82, 96, 118, 128], 0, 180, fill=(180, 130, 30, 255), width=2)
    d.polygon([(94, 128), (106, 128), (100, 142)], fill=(120, 200, 220, 255),
              outline=OUT)


def extra_black_glasses(d):
    circle(d, 88, 54, 12, (255, 255, 255, 60), OUT, 3)
    circle(d, 112, 54, 12, (255, 255, 255, 60), OUT, 3)
    d.line([(100, 54), (100, 54)], fill=OUT, width=3)
    d.line([(76, 54), (70, 52)], fill=OUT, width=3)
    d.line([(124, 54), (130, 52)], fill=OUT, width=3)
    d.line([(98, 54), (102, 54)], fill=OUT, width=3)


def extra_blue_bag(d):
    # strap diagonal across the torso, bag at the side
    d.line([(62, 100), (150, 210)], fill=BLUE_D, width=5)
    d.rounded_rectangle([138, 190, 186, 262], radius=10, fill=BLUE,
                        outline=OUT, width=3)
    d.arc([148, 178, 176, 200], 180, 360, fill=BLUE_D, width=4)
    circle(d, 162, 226, 6, GOLD, OUT, 2)


def extra_brown_belt(d):
    d.rectangle([58, 222, 142, 240], fill=BROWN, outline=OUT, width=3)
    d.rectangle([90, 222, 110, 240], fill=GOLD, outline=OUT, width=3)
    d.rectangle([96, 228, 104, 234], fill=BROWN, outline=OUT, width=2)


def extra_pink_earrings(d):
    circle(d, 70, 66, 6, PINK, OUT, 2)
    circle(d, 130, 66, 6, PINK, OUT, 2)
    circle(d, 70, 78, 4, PINK, OUT, 2)
    circle(d, 130, 78, 4, PINK, OUT, 2)


EXTRAS = [
    ("g_extra_1.png", extra_red_scarf),
    ("g_extra_2.png", extra_gold_necklace),
    ("g_extra_3.png", extra_black_glasses),
    ("g_extra_4.png", extra_blue_bag),
    ("g_extra_5.png", extra_brown_belt),
    ("g_extra_6.png", extra_pink_earrings),
]

for _name, _fn in TOPS + BOTTOMS + SHOES + HATS + EXTRAS:
    garment(_name, _fn)

# ---------------------------------------------------------------- critics --
# 96x96 portraits, flat bright style matching the garments.

def critic(name, fn):
    img = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fn(d)
    save(img, name)


def crit_gran(d):
    # grey bun, glasses, warm smile, shawl
    d.ellipse([22, 26, 74, 84], fill=SKIN, outline=OUT, width=3)
    circle(d, 48, 12, 14, (200, 200, 205, 255), OUT, 3)  # bun
    d.pieslice([20, 16, 76, 58], 180, 360, fill=(200, 200, 205, 255))
    d.arc([20, 16, 76, 58], 180, 360, fill=OUT, width=3)
    # glasses
    circle(d, 38, 52, 9, (255, 255, 255, 60), OUT, 3)
    circle(d, 58, 52, 9, (255, 255, 255, 60), OUT, 3)
    d.line([(47, 52), (49, 52)], fill=OUT, width=3)
    # warm smile + rosy cheeks
    d.arc([40, 62, 56, 74], 15, 165, fill=OUT, width=3)
    circle(d, 30, 62, 4, (245, 150, 140, 255))
    circle(d, 66, 62, 4, (245, 150, 140, 255))
    # shawl
    d.polygon([(14, 96), (30, 78), (66, 78), (82, 96)], fill=PURPLE,
              outline=OUT)


def crit_friend(d):
    # young, bob hair, big smile, earrings
    d.ellipse([24, 24, 72, 80], fill=SKIN, outline=OUT, width=3)
    d.pieslice([18, 10, 78, 56], 180, 360, fill=(40, 30, 35, 255))
    d.rounded_rectangle([18, 12, 30, 66], radius=6, fill=(40, 30, 35, 255))
    d.rounded_rectangle([66, 12, 78, 66], radius=6, fill=(40, 30, 35, 255))
    d.arc([18, 10, 78, 56], 180, 360, fill=OUT, width=3)
    circle(d, 38, 50, 4, OUT)
    circle(d, 58, 50, 4, OUT)
    d.arc([38, 58, 58, 74], 10, 170, fill=OUT, width=3)
    circle(d, 31, 60, 4, (245, 150, 140, 255))
    circle(d, 65, 60, 4, (245, 150, 140, 255))
    circle(d, 24, 66, 3, PINK, OUT, 2)
    circle(d, 72, 66, 3, PINK, OUT, 2)
    d.polygon([(20, 96), (34, 80), (62, 80), (76, 96)], fill=RED,
              outline=OUT)


def crit_photographer(d):
    # cap + camera strap, beard
    d.ellipse([24, 26, 72, 82], fill=SKIN, outline=OUT, width=3)
    d.pieslice([22, 12, 74, 52], 180, 360, fill=BLUE, outline=OUT, width=3)
    d.ellipse([18, 40, 78, 50], fill=BLUE, outline=OUT, width=3)
    # beard
    d.pieslice([26, 58, 70, 84], 0, 180, fill=(70, 50, 35, 255))
    d.arc([26, 58, 70, 84], 0, 180, fill=OUT, width=3)
    circle(d, 38, 50, 4, OUT)
    circle(d, 58, 50, 4, OUT)
    d.arc([42, 60, 54, 68], 15, 165, fill=OUT, width=2)
    # camera strap + camera body
    d.line([(28, 84), (40, 96)], fill=BLACK, width=4)
    d.line([(68, 84), (56, 96)], fill=BLACK, width=4)
    d.rounded_rectangle([36, 88, 60, 96], radius=3, fill=BLACK, outline=OUT, width=2)
    circle(d, 48, 92, 4, (120, 200, 220, 255), OUT, 2)


critic("crit_1.png", crit_gran)
critic("crit_2.png", crit_friend)
critic("crit_3.png", crit_photographer)

# ------------------------------------------------------------------- bits --

def make_dot(name, size, color):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    circle(d, size // 2, size // 2, size // 2 - 1, color)
    save(img, name)


make_dot("particle.png", 32, (255, 255, 255, 255))


def make_star():
    S2 = 96
    img = Image.new("RGBA", (S2, S2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = cy = S2 // 2
    pts = []
    for k in range(10):
        r = 42 if k % 2 == 0 else 18
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=(255, 200, 60, 255), outline=(220, 150, 20, 255))
    save(img, "star.png")


def make_lock():
    W2, H2 = 64, 80
    img = Image.new("RGBA", (W2, H2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([10, 34, 54, 72], radius=8,
                        fill=(90, 100, 120, 255), outline=(50, 60, 80, 255), width=3)
    d.arc([18, 10, 46, 44], 180, 360, fill=(50, 60, 80, 255), width=7)
    circle(d, 32, 50, 7, (255, 220, 90, 255))
    d.rectangle([29, 50, 35, 62], fill=(255, 220, 90, 255))
    save(img, "lock.png")


make_star()
make_lock()

# -------------------------------------------------------------- background --
# PIL y is down; GUI y is up (GUI y = 640 - PIL y).
# Dusk indigo walls, warm amber window + stall light on the right, smoke
# wisps drifting up, clothing rack silhouette right, mirror frame on the
# left around the model spot (GUI x 200-400, y 110-530 -> PIL x 200-400,
# y 110-530). No text anywhere.

def make_bg():
    W, H = 1136, 640
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    # indigo wall, slightly lighter toward the top
    for y in range(H):
        t = y / H
        r = int(38 + 14 * t)
        g = int(40 + 12 * t)
        b = int(84 + 20 * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    # floor band (warm wood, bottom of the room)
    d.rectangle([0, 560, W, 640], fill=(96, 62, 40))
    d.rectangle([0, 560, W, 566], fill=(70, 44, 28))
    for x in range(0, W, 140):
        d.line([(x, 566), (x, 640)], fill=(70, 44, 28), width=2)
    # warm amber glow: window on the right (PIL x 820-1090, y 60-330)
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([760, 20, 1130, 400], fill=(255, 170, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.blend(img, Image.blend(img, glow, 0.6), 0.55)
    d = ImageDraw.Draw(img)
    # window frame
    d.rounded_rectangle([820, 60, 1090, 330], radius=12,
                        fill=(255, 190, 90), outline=(60, 35, 20), width=6)
    d.line([(955, 60), (955, 330)], fill=(60, 35, 20), width=6)
    d.line([(820, 195), (1090, 195)], fill=(60, 35, 20), width=6)
    # market rooftops + stall awnings seen through the window
    d.polygon([(830, 330), (880, 260), (930, 330)], fill=(120, 60, 70))
    d.polygon([(940, 330), (1000, 250), (1060, 330)], fill=(90, 70, 110))
    for i, x0 in enumerate(range(830, 1080, 42)):
        d.rectangle([x0, 300, x0 + 42, 330],
                    fill=(220, 80, 60) if i % 2 == 0 else (250, 230, 180))
    # string lights across the top of the window
    for i, x in enumerate(range(840, 1080, 40)):
        y = 90 + 18 * math.sin(i * 0.9)
        d.line([(x - 20, y - 6), (x, y)], fill=(60, 35, 20), width=2)
        circle(d, x, y + 8, 5, (255, 220, 120, 255), (200, 140, 40, 255), 2)
    # smoke wisps drifting past the window (soft, blurred)
    smoke = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(smoke)
    for k in range(5):
        x = 800 + k * 55 + rng.randint(-10, 10)
        pts = [(x + 14 * math.sin((y - 330) / 45.0), y)
               for y in range(330, 560, 8)]
        sd.line(pts, fill=(220, 220, 235, 60), width=16, joint="curve")
    smoke = smoke.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img.convert("RGBA"), smoke)
    d = ImageDraw.Draw(img)
    # mirror frame on the left around the model spot
    d.rounded_rectangle([180, 90, 420, 550], radius=18,
                        fill=(235, 220, 200), outline=(200, 150, 60), width=10)
    d.rounded_rectangle([196, 106, 404, 534], radius=12,
                        fill=(250, 240, 225), outline=(160, 110, 40), width=3)
    # small gold finials on the mirror corners
    for (x, y) in [(180, 90), (420, 90), (180, 550), (420, 550)]:
        circle(d, x, y, 9, GOLD, (160, 110, 40, 255), 2)
    # clothing rack silhouette, right of the mirror (mostly behind the
    # wardrobe panel in-game, visible at the edges)
    d.line([(640, 180), (640, 520)], fill=(40, 30, 40), width=8)
    d.line([(760, 180), (760, 520)], fill=(40, 30, 40), width=8)
    d.line([(620, 180), (780, 180)], fill=(40, 30, 40), width=8)
    for i, x in enumerate((655, 690, 725)):
        col = (RED, BLUE, GREEN)[i % 3]
        d.polygon([(x - 18, 190), (x + 18, 190), (x + 24, 300), (x - 24, 300)],
                  fill=col, outline=(40, 30, 40))
        d.line([(x, 180), (x, 192)], fill=(40, 30, 40), width=4)
    # warm lamp glow bottom-left + a small rug under the model
    lamp = Image.new("RGB", (W, H), (0, 0, 0))
    ld = ImageDraw.Draw(lamp)
    ld.ellipse([60, 380, 340, 640], fill=(255, 180, 80))
    lamp = lamp.filter(ImageFilter.GaussianBlur(50))
    img = Image.blend(img.convert("RGB"), Image.blend(img.convert("RGB"), lamp, 0.5), 0.4)
    d = ImageDraw.Draw(img)
    d.ellipse([210, 545, 390, 585], fill=(150, 60, 70), outline=(110, 40, 50), width=3)
    d.ellipse([230, 552, 370, 578], fill=(190, 90, 80))
    save(img.convert("RGBA"), "background.png")


make_bg()
print("art done")
