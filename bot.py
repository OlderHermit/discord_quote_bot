import asyncio
import datetime
import json
import math
import os
import time

import aiofiles
import aiohttp_cors
import discord
from aiohttp import web

import quote_to_image

from datetime import datetime, timedelta
from discord import Member
from discord.ext import commands, tasks

# "bot_token": "redacted",
# "bot_token_test": "redacted"
bot_address = '172.27.27.2'
bot_port = 8000
validating_user = 321297277773938690

intents = discord.Intents.default()
intents.message_content = True

#client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix=';', intents=discord.Intents.all())

lock_playing_state = asyncio.Lock()
is_playing = False


@bot.event
async def on_ready():
    try:
        c = await bot.tree.sync()
        print(f'Synced {len(c)} commands')
    except Exception as e:
        print(f'got {e}')
    # ticker.start()
    #await bot.loop.create_task(start_server())

    print(f'We have logged in as {bot.user.name}')


@bot.tree.command(name='quote', description='Najlepsze kwestie jakie na przestrzeni lat padły na niniejszym serwerze')
async def quote(interactions):
    conf_file = await aiofiles.open("jsons/config.json", mode='r+', encoding='UTF-8')
    config = json.loads(await conf_file.read())
    last_quote_time = tuple(map(int, config['last_quote_generated'].split(', ')))
    today = datetime.utcnow().timetuple()[0:3]
    if today <= last_quote_time:
        await interactions.response.send_message(
            file=discord.File('text_image.png', 'Mądrość dnia.png')
            # "Today's message has been already sent", ephemeral=True
        )
        return

    await quote_to_image.generate_image()
    await interactions.response.send_message(
        file=discord.File('text_image.png', 'Mądrość dnia.png')
    )
    config['last_quote_generated'] = str(today)[1:-1]
    await conf_file.seek(0)
    await conf_file.writelines(json.dumps(config, indent=4, ensure_ascii=False))
    await conf_file.close()


@bot.tree.command(name='explain', description='Dodatkowe informacje \"lore\" ostatniej wypowiedzi')
async def explain(interactions):
    data = json.load(open("jsons/quotes.json", encoding='UTF-8'))
    used = json.load(open("jsons/used.json", encoding='UTF-8'))
    if len(used['used_quotes']) == 0:
        await interactions.response.send_message(
            "No quote response to send", ephemeral=True
        )
        return
    await interactions.response.send_message(
        data['quotes'][int(list(used['used_quotes'].keys())[-1])]['explanation'], ephemeral=True
    )


@bot.tree.command(name='submit', description='Możliwość dodania własnego cytatu')
async def submit(interactions):
    await interactions.response.send_message(
        f"Functionality moved to here http://{bot_address}:{bot_port}", ephemeral=True, delete_after=60
    )


@bot.event
async def on_member_update(before: Member, after: Member):
    role_id = 1236360986970161283  # 1225828166497730741
    channel_id_to_shame = 1226101153129955382

    if before.get_role(role_id) is None:
        if after.get_role(role_id) is not None:
            async with aiofiles.open("jsons/punishments.json", mode='r+', encoding='UTF-8') as file:
                data = json.loads(await file.read())
                if data['sentenced'].get(f'{after.id}') is None:
                    data['sentenced'].update({
                        f'{after.id}': {
                            'name': f'{after.name}',
                            'time': f'{(datetime.utcnow() + timedelta(seconds=5)).timestamp()}'
                        }
                    })
                    await file.seek(0)
                    await file.writelines(json.dumps(data, indent=4))

    elif before.get_role(role_id) is not None:
        if after.get_role(role_id) is None:
            async with aiofiles.open("jsons/punishments.json", mode='w+', encoding='UTF-8') as file:
                data = json.loads(await file.read())
                if data['sentenced'].get(f'{after.id}') is not None and float(
                        data['sentenced'].get(f'{after.id}')['time']) < datetime.utcnow().timestamp():
                    data['sentenced'].pop(f'{after.id}')
                    await file.seek(0)
                    await file.writelines(json.dumps(data, indent=4, ensure_ascii=False))
                    await after.guild.get_channel(channel_id_to_shame).send(
                        f"```ansi\n"
                        f"Użytkownik [0;33m{before.name}[0m został oczyszczony z karnej roli [0;36m{before.get_role(role_id).name}\n"
                        f"```"
                    )
                else:
                    time_difference = (datetime.now() - datetime.utcnow()).total_seconds()
                    await after.add_roles(before.get_role(role_id))
                    await after.guild.get_channel(channel_id_to_shame).send(
                        f"```ansi\n"
                        f"Użytkownik [0;33m{after.name}[0m próbował usunąć karną rolę [0;36m{after.get_role(role_id).name} [1;36mSHAME ON HIM [0mpozostały czas kary: [1;32m{timedelta(seconds=math.ceil((float(data['sentenced'][f'{after.id}']['time'])) - datetime.utcnow().timestamp()))}\n"
                        f"```"
                        #<t:{math.ceil((float(data['sentenced'][f'{after.id}']['time'])) + time_difference)}:R>
                        #timedelta(seconds=math.ceil((float(data['sentenced'][f'{after.id}']['time'])) - datetime.utcnow().timestamp()))
                    )


async def start_server():
    # prepare authors to load
    quotes_file = await aiofiles.open("jsons/quotes.json", mode='r+', encoding='UTF-8')
    quotes = json.loads(await quotes_file.read())
    await quotes_file.close()

    authors_file = await aiofiles.open("quote_web_ui/static/authors.json", mode='w+', encoding='UTF-8')
    await authors_file.writelines(json.dumps(quotes['authors'], indent=4, ensure_ascii=False))
    await authors_file.close()

    # start web server
    app = web.Application()
    app.add_routes([web.post('/', submit_through_web)])
    app.add_routes([web.get('/', return_web_page)])
    app.router.add_static('/static/', path='quote_web_ui/static', name='static', follow_symlinks=True)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, bot_address, bot_port)
    await site.start()


async def return_web_page(request):
    return web.FileResponse(path=os.path.abspath('quote_web_ui/index.html'))


async def submit_through_web(request):
    try:
        data = json.loads((await request.json()))

        validating_member: Member = next((m for m in bot.guilds[0].members if m.id == validating_user), None)
        if validating_member is None:
            return web.json_response({'status': 'error', 'message': 'invalid validating pipeline'}, status=500)

        res = (str(data)
               .replace(',', ',\n')
               .replace('{', '{\n')
               .replace('}', '\n}')
               .replace('\n', '\n\t')
               .replace('\'', '\"'))
        await validating_member.send(res)

        return web.json_response({'status': 'success', 'message': 'Command executed'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)


@tasks.loop(seconds=2)
async def ticker():
    print("hello")


def check_config():
    if not os.path.exists('jsons/config.json'):
        with open("jsons/config.json", mode='w+', encoding='UTF-8') as file:
            file.write('{'
                       '"last_quote_generated" : "1900, 1, 1",'
                       '"bot_token": ""'
                       '}')
        return False
    return True


if not check_config():
    raise Exception("Config error")
time.sleep(1)
config_file = open("jsons/config.json", mode='r', encoding='UTF-8')
config = json.load(config_file)
config_file.close()

bot.run(config['bot_token'])
