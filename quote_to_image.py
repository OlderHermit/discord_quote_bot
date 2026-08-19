import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont

import context
from orm import Quote

IMAGE_PATH = Path(__file__).parent / "text_image.png"
default_font_color = (255, 255, 255)
default_background_color = (0x27, 0x29, 0x2E)

def get_size(text: str, font: FreeTypeFont):
    if font:
        return font.getlength(text)
    return 0


def format_author_line(author, space_width, max_author_width, author_offset, check_font):
    author_width = get_size(author.id + ':', check_font)
    spaces_needed = math.floor((max_author_width - author_width) / space_width) + author_offset
    return author.id + ':' + ' ' * spaces_needed


def split_to_size(dialogue: Quote, maxsize: int, font: FreeTypeFont):
    author_offset = 5
    result = []

    space_width = get_size(' ', font)
    max_author_width = max(get_size(a.id + ':', font) for a in dialogue.get_authors())
    spaces_equal_max_author_width = math.ceil(max_author_width / space_width) + author_offset
    single_sentence = len(dialogue.sentences) == 1

    if single_sentence:
        text = dialogue.sentences[0].sentence
        for line in wrap_words(
                text,
                '',
                '',
                maxsize,
                font
        ):
            result.append((center(line, maxsize, font), default_font_color))

        longest_size = max((get_size(line, font) for line, _ in result), default=0)
        result.append((center(generate_separator(longest_size, font), maxsize, font), default_font_color))
        return result

    for sentence in dialogue.sentences:
        author = sentence.author
        text = sentence.sentence

        author_prefix = format_author_line(author, space_width, max_author_width, author_offset, font)
        empty_prefix = spaces_equal_max_author_width * ' '

        for i, line in enumerate(wrap_words(
            text,
            author_prefix,
            empty_prefix,
            maxsize,
            font
        )):
            color = author.get_tuple_color() if i == 0 else default_font_color
            result.append((line, color))

    result.append((center(generate_separator(maxsize, font), maxsize, font), default_font_color))
    return result

def wrap_words(words: str, first_prefix: str, cont_prefix: str, maxsize: int, font: FreeTypeFont):
    line = first_prefix
    width = get_size(line, font)
    for word in words.split(' '):
        chunk = get_size(word + ' ', font)
        if width + chunk > maxsize and line not in (first_prefix, cont_prefix):
            yield line
            line, width = cont_prefix, get_size(cont_prefix, font)
        line += word + ' '
        width += chunk
    yield line


def center(text: str, maxsize: int, font: FreeTypeFont, emoji_font: FreeTypeFont = None):
    split = split_emoji(text)
    offset = maxsize - (get_size(split[0], font) + get_size(split[1], emoji_font))
    space_width = get_size(' ', font)
    spaces = math.ceil(offset / space_width)
    return ' ' * math.ceil(spaces / 2) + text + ' ' * math.ceil(spaces / 2)


def split_emoji(text: str):
    result = ['', '']
    for char in text:
        result[ord(char) > 512] += char
    return result


def generate_separator(longest_size: int, check_font: FreeTypeFont):
    sep_width = get_size('-', check_font)
    seps = math.ceil(longest_size / sep_width)
    return '-' * seps


def prepare_dialogue(quote: Quote, max_width: int, fonts: dict[str, FreeTypeFont]):
    centered = split_to_size(quote, max_width, fonts['base'])

    centered.extend(
        (center(a.signature, max_width, fonts['base'], fonts['icon']), a.get_tuple_color())
        for a in quote.get_authors()
    )

    return centered


def _generate_image_for_quote(quote: Quote, save=True):
    width = 600
    text_position = (50, 50)
    text_color = (255, 255, 255)

    fonts = {
        "base": ImageFont.truetype("assets/Jaini-Regular.ttf", 36),
        "icon": ImageFont.truetype("assets/SEGUIEMJ.ttf", 36),
    }

    centered = prepare_dialogue(quote, width - text_position[0] * 2, fonts)

    image = Image.new("RGB", (width, 100 + 50 * len(centered)), default_background_color)
    draw = ImageDraw.Draw(image)

    for j, pair in enumerate(centered):
        line, color = pair
        x = text_position[0]
        y = text_position[1] * (j + 1)
        if j >= len(centered) - len(quote.get_authors()):
            y -= 10

        for i, char in enumerate(line):
            font = fonts['icon'] if ord(char) > 512 else fonts['base']
            if char == ':':
                color = default_font_color

            if font == fonts['icon']:
                draw.text((x, y + 10), char, fill=text_color, font=font, embedded_color=True)
            else:
                draw.text((x, y), char, fill=color, font=font, embedded_color=True)
            x += draw.textlength(char, font=font)

    if save:
        image.save("text_image.png")
    return image

def render_quote_image(quote: Quote, path: Path = IMAGE_PATH) -> None:
    _generate_image_for_quote(quote).save(path)

def generate_daily_image() -> int:
    quote = context.db.get_random_valid_quote()
    render_quote_image(quote)
    context.db.mark_quote_as_used(quote.id)
    return quote.id
