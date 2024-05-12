import asyncio
import datetime
import json
import math
import aiofiles
import discord

import quote_to_image

from datetime import datetime, timedelta
from discord import Member
from discord.ext import commands, tasks

bot_token = 'redacted' # reik
validating_user = 321297277773938690

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
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
async def submit(interactions, quote: str, author: str, date: str, additional_info: str = '-----'):
    validating_member: Member = next((m for m in interactions.guild.members if m.id == validating_user), None)
    if validating_member is None:
        return
    msg = {
      'quote': quote,
      'author': author,
      'date': date,
      'explanation': additional_info
    }
    res = str(msg).replace(',', ',\n').replace('{', '{\n').replace('}', '\n}').replace('\n', '\n\t').replace('\'', '\"')
    res += f'\nsubmitted by {interactions.user.name}\n'
    await validating_member.send(res)
    await interactions.response.send_message(
        "Request submitted", ephemeral=True, delete_after=60
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
                if data['sentenced'].get(f'{after.id}') is not None and float(data['sentenced'].get(f'{after.id}')['time']) < datetime.utcnow().timestamp():
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


@tasks.loop(seconds=2)
async def ticker():
    print("hello")


bot.run(bot_token)
