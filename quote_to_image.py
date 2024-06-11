import json
import math
import os.path
import random
import aiofiles
import regex
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFont import FreeTypeFont


def check_size(text: str, check_font: ImageFont):
    if check_font is not None:
        return check_font.getlength(text)
    return 0


def split_to_size(text: str, maxsize: int, check_font: ImageFont):
    combined_size = 0
    longest_size = 0
    line = ''
    result = []
    color = (255, 255, 255)
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


def split_to_size_dialogue(dialogue: list[str], maxsize: int, check_font: ImageFont, authors):
    author_offset = 5
    longest_size = 0
    result = []
    space_width = check_size(' ', check_font)
    spaces_equal_longest_author = math.ceil(max([check_size(author['author']+':', check_font) for author in authors])/space_width)
    dialogue = [e.replace('[', '') for e in dialogue]
    dialogue = [e.replace(']', ': ') for e in dialogue]

    for text in dialogue:
        combined_size = 0
        line = ''
        color = (255, 255, 255)
        for i, word in enumerate(text.split(' ')):
            if i == 0:
                color = [x['color'] for x in authors if x['author'] == word[:-1]]
                if len(color) == 0:
                    color = (255, 255, 255)
                else:
                    color = tuple([int(s) for s in color[0].split(' ')])
                spaces_equal_author = math.ceil(check_size(word, check_font)/space_width)
                combined_size = check_size(word, check_font) + (spaces_equal_longest_author - spaces_equal_author + author_offset) * space_width
                line = word + (spaces_equal_longest_author - spaces_equal_author + author_offset) * ' '
            elif combined_size + check_size(word, check_font) > maxsize:
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

    color = (255, 255, 255)
    result.append((center(generate_separator(longest_size, check_font), maxsize, check_font), color))
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


def roll_quote(data, used):
    picks = list(range(0, len(data['quotes']), 1))
    for e in sorted(used['used_quotes'].keys()):
        picks.remove(int(e))
    if len(picks) == 0:
        used['used_quotes'].clear()
        picks = list(range(0, len(data['quotes']), 1))

    return random.choice(picks), used


def prepare_quote(data, quote, width: int, text_position: tuple[int, int], fonts: dict[str, FreeTypeFont]):
    authors = [data['authors'][author] for author in quote['author'].split(';')]

    centered = split_to_size(quote['quote'], width - text_position[0] * 2, fonts['base'])
    centered.extend([
        (center(author['signature'], width - text_position[0] * 2, fonts['base'], fonts['icon']), (255, 255, 255)) for author in authors
    ])
    return centered


def prepare_dialogue(data, quote, width: int, text_position: tuple[int, int], fonts: dict[str, FreeTypeFont]):
    authors = [data['authors'][author] for author in quote['author'].split(';')]

    centered = split_to_size_dialogue(quote['quote'], width - text_position[0] * 2, fonts['base'], authors)
    centered.extend([
        (center(author['signature'], width - text_position[0] * 2, fonts['base'], fonts['icon']), tuple([int(s) for s in author['color'].split(' ')])) for author in authors
    ])
    return centered


async def generate_image():
    width = 600
    text_position = (50, 50)
    text_color = (255, 255, 255)

    fonts = {
        "base": ImageFont.truetype("assets/Jaini-Regular.ttf", 36),
        "icon": ImageFont.truetype("assets/SEGUIEMJ.ttf", 36),
    }

    quotes_file = await aiofiles.open("jsons/quotes.json", encoding='UTF-8')
    data = json.loads(await quotes_file.read())
    if not os.path.exists('jsons/used.json'):
        async with aiofiles.open("jsons/used.json", mode='w+', encoding='UTF-8') as used_file:
            await used_file.write('{"used_quotes" : {}}')
    used_file = await aiofiles.open("jsons/used.json", mode='r+', encoding='UTF-8')
    used = json.loads(await used_file.read())

    index, used = roll_quote(data, used)
    quote = data['quotes'][index]
    authors = [data['authors'][author] for author in quote['author'].split(';')]

    if isinstance(quote, str):
        centered = prepare_quote(data, quote, width, text_position, fonts)
    else:
        centered = prepare_dialogue(data, quote, width, text_position, fonts)

    image = Image.new("RGB", (width, 100 + 50 * len(centered)), (0x27, 0x29, 0x2E))
    draw = ImageDraw.Draw(image)

    for j, pair in enumerate(centered):
        line, color = pair
        color_copy = color
        begin_color = False
        x = text_position[0]
        y = text_position[1] * (j + 1)
        if j >= len(centered) - len(authors):
            y -= 10
        if re.search(regex, line) or any([x for x in line if ord(x) > 512]):
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
    used['used_quotes'].update({f"{index}": {"quote": f"{quote['quote']}"}})
    await used_file.seek(0)
    await used_file.writelines(json.dumps(used, indent=4, ensure_ascii=False))
    await used_file.close()
    await quotes_file.close()
