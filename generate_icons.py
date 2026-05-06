from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

icons = [(192, 'static/icons/icon-192.png'), (512, 'static/icons/icon-512.png')]
Path('static/icons').mkdir(parents=True, exist_ok=True)
for size, path in icons:
    img = Image.new('RGBA', (size, size), (11, 16, 24, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype('arial.ttf', size // 2)
    except Exception:
        font = ImageFont.load_default()
    try:
        bbox = draw.textbbox((0, 0), 'MR', font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        w, h = draw.textsize('MR', font=font)
    draw.text(((size - w) / 2, (size - h) / 2), 'MR', font=font, fill=(44, 134, 255, 255))
    img.save(path)
print('Ícones gerados com sucesso.')
