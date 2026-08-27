from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("/home/ubuntu/upload/SelfPic.png")
OUTPUT = ROOT / "assets" / "mikael-lim-portrait.png"


def main():
    if not SOURCE.exists():
        raise FileNotFoundError(f"Portrait source not found: {SOURCE}")

    source = ImageOps.exif_transpose(Image.open(SOURCE).convert("RGB"))
    # Remove only the scanner footer; the portrait itself remains uncropped and proportional.
    source = source.crop((0, 0, source.width, source.height - 58))
    portrait = ImageOps.contain(source, (232, 330), method=Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (244, 344), (9, 18, 24, 255))
    left = (canvas.width - portrait.width) // 2
    top = (canvas.height - portrait.height) // 2
    canvas.paste(portrait.convert("RGBA"), (left, top))

    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, canvas.width, canvas.height), outline=(45, 212, 191, 160), width=2)
    draw.rectangle((4, 4, canvas.width - 5, canvas.height - 5), outline=(167, 139, 250, 70), width=1)
    draw.rectangle((0, 264, canvas.width, canvas.height), fill=(7, 14, 20, 34))
    canvas.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(0.4)))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(OUTPUT, "PNG", optimize=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
