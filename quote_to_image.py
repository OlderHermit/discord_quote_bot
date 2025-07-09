import math
import random
import re

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, joinedload

from orm import Quote, Author, Sentence

default_font_color = (255, 255, 255)


def check_size(text: str, check_font: ImageFont):
    if check_font is not None:
        return check_font.getlength(text)
    return 0

def calculate_basic_widths(dialogue: Quote, author_offset, check_font):
    space_width = check_size(' ', check_font)
    author_widths = {
        author: check_size(author.id + ':', check_font)
        for author in dialogue.get_authors()
    }
    max_author_width = max(author_widths.values())
    spaces_equal_max_author_width = math.ceil(max_author_width / space_width) + author_offset
    return space_width, max_author_width, spaces_equal_max_author_width


def format_author_line(author, space_width, max_author_width, author_offset, check_font):
    author_width = check_size(author.id + ':', check_font)
    spaces_needed = math.ceil((max_author_width - author_width) / space_width) + author_offset
    return author.id + ':' + ' ' * spaces_needed


def split_to_size(quote: Quote, maxsize: int, check_font: ImageFont):
    longest_size = 0
    combined_size = 0
    line = ''
    result = []

    space_width = check_size(' ', check_font)
    text = quote.sentences[0].sentence
    color = default_font_color

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


def split_to_size_dialogue(dialogue: Quote, maxsize: int, check_font: ImageFont):
    author_offset = 5
    space_width, max_author_width, spaces_equal_max_author_width = calculate_basic_widths(dialogue, author_offset, check_font)

    longest_size = 0
    result = []

    for sentence in dialogue.sentences:
        author = sentence.author
        text = sentence.sentence
        color = author.get_tuple_color()

        line = format_author_line(author, space_width, max_author_width, author_offset, check_font)
        empty_line = spaces_equal_max_author_width * ' '
        combined_size = check_size(line, check_font)

        for i, word in enumerate(text.split(' ')):
            if combined_size + check_size(word, check_font) > maxsize:
                if longest_size < combined_size:
                    longest_size = combined_size
                result.append((line, color))
                color = default_font_color
                combined_size = max_author_width + check_size(word, check_font) + space_width
                line = empty_line + word + ' '
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


def prepare_quote(quote: Quote, width: int, text_position: tuple[int, int], fonts: dict[str, FreeTypeFont]):
    author: Author = quote.get_authors()[0]
    centered = split_to_size(quote, width - text_position[0] * 2, fonts['base'])
    centered.append(
        (center(author.signature, width - text_position[0] * 2, fonts['base'], fonts['icon']), author.get_tuple_color())
    )
    return centered


def prepare_dialogue(quote: Quote, width: int, text_position: tuple[int, int], fonts: dict[str, FreeTypeFont]):
    centered = split_to_size_dialogue(quote, width - text_position[0] * 2, fonts['base'])

    for author in quote.get_authors():
        centered.append(
            (center(author.signature, width - text_position[0] * 2, fonts['base'], fonts['icon']), author.get_tuple_color())
        )
    return centered


def get_random_quote(session: Session):
    data = session.execute(select(Quote)
        .join(Sentence)
        .join(Author)
        .where(Quote.used.is_(False))
        .where(Quote.deleted.is_(False))
    ).scalars().all()

    if len(data) == 0:
        reset_used_quotes(session)
        return get_random_quote(session)

    quote: Quote = random.choice(data)
    return quote


def reset_used_quotes(session: Session):
    quotes = session.execute(select(Quote)).scalars().all()
    for q in quotes:
        q.used = False
    session.commit()
    session.close()


async def generate_image(engine: Engine):
    session = Session(engine)
    try:
        width = 600
        text_position = (50, 50)
        text_color = (255, 255, 255)

        fonts = {
            "base": ImageFont.truetype("assets/Jaini-Regular.ttf", 36),
            "icon": ImageFont.truetype("assets/SEGUIEMJ.ttf", 36),
        }

        quote = get_random_quote(session)

        if len(quote.get_authors()) == 1:
            centered = prepare_quote(quote, width, text_position, fonts)
        else:
            centered = prepare_dialogue(quote, width, text_position, fonts)

        image = Image.new("RGB", (width, 100 + 50 * len(centered)), (0x27, 0x29, 0x2E))
        draw = ImageDraw.Draw(image)

        for j, pair in enumerate(centered):
            line, color = pair
            x = text_position[0]
            y = text_position[1] * (j + 1)
            if j >= len(centered) - len(quote.get_authors()):
                y -= 10

            for i, char in enumerate(line):
                font = fonts['icon'] if ord(char) > 512 else fonts['base']
                char_width = draw.textlength(char, font=font)
                if font == fonts['icon']:
                    draw.text((x, y + 10), char, fill=text_color, font=font, embedded_color=True)
                else:
                    draw.text((x, y), char, fill=color, font=font, embedded_color=True)
                x += char_width
                if char == ':':
                    color = default_font_color

        image.save("text_image.png")

        quote.used = True
        session.commit()
        return quote.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
