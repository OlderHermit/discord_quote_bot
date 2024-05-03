import json
import math
import random

from PIL import Image, ImageDraw, ImageFont


def check_size(text: str, check_font: ImageFont):
    if check_font is not None:
        return check_font.getlength(text)
    return 0


def split_to_size(text: str, maxsize: int, check_font: ImageFont):
    combined_size = 0
    longest_size = 0
    line = ''
    result = []
    space_width = check_size(' ', check_font)
    for c in text.split(' '):
        if combined_size + check_size(c, check_font) > maxsize:
            result.append(center(line, maxsize, check_font))
            if longest_size < combined_size: longest_size = combined_size
            combined_size = check_size(c, check_font) + space_width
            line = c + ' '
        else:
            combined_size += check_size(c, check_font) + space_width
            line += c + ' '
    if longest_size < combined_size: longest_size = combined_size
    result.append(center(line, maxsize, check_font))
    result.append(center(generate_separator(maxsize, longest_size, check_font), maxsize, check_font))
    return result


def center(text: str, maxsize: int, check_font: ImageFont, emoji_font: ImageFont = None):
    split = split_emoji(text)
    offset = maxsize - (check_size(split[0], check_font) + check_size(split[1], emoji_font))
    space_width = check_size(' ', check_font)
    spaces = math.ceil(offset / space_width)
    return ' ' * math.ceil(spaces / 2) + text + ' ' * math.ceil(spaces / 2)


def split_emoji(text: str):
    result = ['', '']
    for char in text:
        if ord(char) > 512:
            result[1] += char
        else:
            result[0] += char
    return result


def generate_separator(maxsize: int, longest_size: int, check_font: ImageFont):
    sep_width = check_size('-', check_font)
    seps = math.ceil(longest_size / sep_width)+2
    return '-'*seps


def generate_image(not_allowed: {int} = {}):
    width = 600
    text_position = (50, 50)
    text_color = (255, 255, 255)

    fonts = [
        ImageFont.truetype("Jaini-Regular.ttf", 36),
        ImageFont.truetype("SEGUIEMJ.ttf", 36),
    ]

    data = json.load(open("quotes.json", encoding='UTF-8'))

    picks = list(range(0, len(data['quotes']), 1))
    for e in sorted(not_allowed, reverse=True):
        del picks[e]
    if len(picks) == 0:
        raise IndexError("No more quotes allowed buffer too large or never cleared")

    index = random.choice(picks)
    quote = data['quotes'][index]
    author = data['authors'][quote['author']]

    centered = split_to_size(quote['quote'], width - text_position[0] * 2, fonts[0])
    centered.append(
        center(author['signature'], width - text_position[0] * 2, fonts[0], fonts[1]))

    image = Image.new("RGB", (width, 100 + 50 * len(centered)), (0x27, 0x29, 0x2E))
    draw = ImageDraw.Draw(image)

    for j, line in enumerate(centered):
        x = text_position[0]
        for i, char in enumerate(line):
            font = fonts[0]
            if ord(char) > 512:
                font = fonts[1]
            char_width = draw.textlength(char, font=font)
            draw.text((x, text_position[1] * (j + 1)), char, fill=text_color, font=font, embedded_color=True)
            x += char_width

    image.save("text_image.png")
    return index
