"""Draw the share card image (1200x630) that X, Slack and others show for links to the site.
    python make_og.py
Writes assets/og.png. build.py copies it into docs/. Run again only when the wording changes.
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

from traps import TRAPS

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "assets" / "og.png"
BOLD = "C:/Windows/Fonts/meiryob.ttc"
REG = "C:/Windows/Fonts/meiryo.ttc"

BG = (18, 32, 44)
INK = (240, 244, 246)
SUB = (170, 190, 200)
ACC = (0, 170, 160)


def main():
    im = Image.new("RGB", (1200, 630), BG)
    d = ImageDraw.Draw(im)
    x = 72
    tag = "Claude Code x Windows"
    f_tag = ImageFont.truetype(BOLD, 30)
    d.rounded_rectangle((x, 70, x + d.textlength(tag, font=f_tag) + 40, 122), radius=26, fill=ACC)
    d.text((x + 20, 75), tag, font=f_tag, fill=BG)
    f_big = ImageFont.truetype(BOLD, 64)
    d.text((x, 170), "No error.", font=f_big, fill=INK)
    d.text((x, 250), "Just a wrong result.", font=f_big, fill=INK)
    d.line((x, 362, x + 140, 362), fill=ACC, width=6)
    f_sub = ImageFont.truetype(REG, 32)
    d.text((x, 392), f"{len(TRAPS)} silent traps, each with a 30-second check and the fix", font=f_sub, fill=SUB)
    d.text((x, 444), "エラーなしで壊れる場所と、30秒の確かめ方・直し方", font=f_sub, fill=SUB)
    f_url = ImageFont.truetype(REG, 26)
    d.text((x, 548), "cart231-ffly-b.github.io/cc-win-symptoms", font=f_url, fill=ACC)
    OUT.parent.mkdir(exist_ok=True)
    im.save(OUT, optimize=True)
    print(OUT, im.size)


if __name__ == "__main__":
    main()
