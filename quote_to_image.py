import json
import math
import os.path
import random
import re

import aiofiles
import regex
import sqlalchemy
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, joinedload

from orm import Quote, Color, Author

default_font_color = (255, 255, 255)


def check_size(text: str, check_font: ImageFont):
    if check_font is not None:
        return check_font.getlength(text)
    return 0


def split_to_size(text: str, maxsize: int, check_font: ImageFont):
    combined_size = 0
    longest_size = 0
    line = ''
    result = []
    color = default_font_color
    space_width = check_size(' ', check_font)
    for c in text.split(' '):
        if combined_size + check_size(c, check_font) > maxsize:
            result.append((center(line, maxsize, check_font), color))
            if longest_size < combined_size:
                longest_size = combined_size
            combined_size = check_size(c, check_font) + space_width
            line = c + ' '
        else:
            combined_size += check_size(c, check_font) + space_width
            line += c + ' '
    if longest_size < combined_size:
        longest_size = combined_size
    result.append((center(line, maxsize, check_font), color))
    result.append((center(generate_separator(longest_size, check_font), maxsize, check_font), color))
    return result


def split_to_size_dialogue(dialogue: list[str], maxsize: int, check_font: ImageFont, authors: list[Author]):
    author_offset = 5
    longest_size = 0
    result = []
    space_width = check_size(' ', check_font)
    spaces_equal_longest_author = math.ceil(max([check_size(author.id+':', check_font) for author in authors])/space_width)
    dialogue = [e.replace('[', '') for e in dialogue]
    dialogue = [e.replace(']', ': ') for e in dialogue]

    for text in dialogue:
        combined_size = 0
        line = ''

        author = text[:text.find(':')+1]
        text = text[len(author):]
        color = [(x.color.red, x.color.green, x.color.blue) for x in authors if x.id == author[:-1]][0]

        spaces_equal_author = math.ceil(check_size(author, check_font) / space_width)
        combined_size = (check_size(author, check_font) + (spaces_equal_longest_author - spaces_equal_author + author_offset) * space_width)
        line = author + (spaces_equal_longest_author - spaces_equal_author + author_offset) * ' '

        for i, word in enumerate(text.split(' ')):
            if combined_size + check_size(word, check_font) > maxsize:
                if longest_size < combined_size:
                    longest_size = combined_size
                result.append((line, color))
                combined_size = (spaces_equal_longest_author + author_offset) * space_width + check_size(word, check_font) + space_width
                line = (spaces_equal_longest_author + author_offset) * ' ' + word + ' '
            else:
                combined_size += check_size(word, check_font) + space_width
                line += word + ' '

        if longest_size < combined_size:
            longest_size = combined_size
        result.append((line, color))

    result.append((center(generate_separator(longest_size, check_font), maxsize, check_font), default_font_color))
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
        result[ord(char) > 512] += char
    return result


def generate_separator(longest_size: int, check_font: ImageFont):
    sep_width = check_size('-', check_font)
    seps = math.ceil(longest_size / sep_width)+2
    return '-'*seps


def prepare_quote(quote: str, author: Author, width: int, text_position: tuple[int, int], fonts: dict[str, FreeTypeFont]):
    centered = split_to_size(quote, width - text_position[0] * 2, fonts['base'])
    centered.append(
        (center(author.signature, width - text_position[0] * 2, fonts['base'], fonts['icon']), (author.color.red, author.color.green, author.color.blue))
    )
    return centered


def prepare_dialogue(quote: str, authors: list[Author], width: int, text_position: tuple[int, int], fonts: dict[str, FreeTypeFont]):
    centered = split_to_size_dialogue(quote.split('[NEW_SENTENCE]'), width - text_position[0] * 2, fonts['base'], authors)
    for author in authors:
        centered.append(
            (center(author.signature, width - text_position[0] * 2, fonts['base'], fonts['icon']), (author.color.red, author.color.green, author.color.blue))
        )
    return centered


async def generate_image(engine: Engine):
    width = 600
    text_position = (50, 50)
    text_color = (255, 255, 255)

    fonts = {
        "base": ImageFont.truetype("assets/Jaini-Regular.ttf", 36),
        "icon": ImageFont.truetype("assets/SEGUIEMJ.ttf", 36),
    }

    session = Session(engine)
    data = session.query(Quote).options(joinedload(Quote.authors)).filter(Quote.used.is_(False)).all()

    if len(data) == 0:
        # TODO restart data
        pass

    quote = random.choice([e for e in data])
    authors = [e for e in quote.authors]

    if len(authors) == 1:
        centered = prepare_quote(quote.quote, authors[0], width, text_position, fonts)
    else:
        centered = prepare_dialogue(quote.quote, authors, width, text_position, fonts)

    image = Image.new("RGB", (width, 100 + 50 * len(centered)), (0x27, 0x29, 0x2E))
    draw = ImageDraw.Draw(image)

    for j, pair in enumerate(centered):
        print(pair)
        line, color = pair
        begin_color = False
        x = text_position[0]
        y = text_position[1] * (j + 1)
        if j >= len(centered) - len(authors):
            y -= 10
        if re.search("^\\w+( \\w+)*:", line) or any([x for x in line if ord(x) > 512]):
            begin_color = True
        else:
            color = (255, 255, 255)

        for i, char in enumerate(line):
            font = fonts['base']
            if ord(char) > 512:
                font = fonts['icon']
            char_width = draw.textlength(char, font=font)
            if font == fonts['icon']:
                draw.text((x, y + 10), char, fill=text_color, font=font, embedded_color=True)
            else:
                draw.text((x, y), char, fill=color, font=font, embedded_color=True)
            x += char_width
            if begin_color and char == ':':
                color = (255, 255, 255)
                begin_color = False

    image.save("text_image.png")
    quote.used = True
    session.commit()
    return quote.id
