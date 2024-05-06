import asyncio
import datetime as datetime
import json
import math
from datetime import datetime, timedelta

import discord
from discord import Member
from discord.ext import commands

import quote_to_image

bot_token = 'MTIyNjA5NzEzNDY3NjM0ODk1OQ.GCxcgb.EHZgupFdoiqxKf-AZzIbO7nwvYZWrsdHWwKBOc'
#bot_token = 'Nzc0NTczMDc0MTEyNzA4NjQ4.Gryj_9.sW0-C0WQ5AapulAEC0HM1HU__KlVNgdM9W41es'  # test one
allowed_text_channels = ['tests', 'uwu']
last_quote_time = datetime.utcnow() - timedelta(days=2)
used_quotes_buffer = []
default_volume = 0.2
default_length_time = 5

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

    print(f'We have logged in as {bot.user.name}')


@bot.tree.command(name='quote', description='Najlepsze kwestie jakie na przestrzeni lat padły na niniejszym serwerze')
async def quote(interactions):
    global last_quote_time
    if last_quote_time.day == datetime.today().day:
        await interactions.response.send_message(
            file=discord.File('text_image.png', 'Mądrość dnia.png')
            # "Today's message has been already sent", ephemeral=True
        )
        return

    quote_to_image.generate_image()
    await interactions.response.send_message(
        file=discord.File('text_image.png', 'Mądrość dnia.png')
    )
    last_quote_time = datetime.utcnow()


@bot.tree.command(name='explain', description='Dodatkowe informacje \"lore\" ostatniej wypowiedzi')
async def explain(interactions):
    if len(used_quotes_buffer) == 0:
        await interactions.response.send_message(
            "No quote response to send", ephemeral=True
        )
        return
    data = json.load(open("jsons/quotes.json", encoding='UTF-8'))
    await interactions.response.send_message(
        data['quotes'][used_quotes_buffer[-1]]['explanation'], ephemeral=True
    )


@bot.event
async def on_member_update(before: Member, after: Member):
    role_id = 1236360986970161283  # 1225828166497730741
    channel_id_to_shame = 1226101153129955382

    if before.get_role(role_id) is None:
        if after.get_role(role_id) is not None:
            with open("jsons/punishments.json", mode='r+', encoding='UTF-8') as file:
                data = json.load(file)
                if data['sentenced'].get(f'{after.id}') is None:
                    data['sentenced'].update({
                        f'{after.id}': {
                            'name': f'{after.name}',
                            'time': f'{(datetime.utcnow() + timedelta(seconds=5)).timestamp()}'
                        }
                    })
                    file.seek(0)
                    json.dump(data, file, indent=4)

    elif before.get_role(role_id) is not None:
        if after.get_role(role_id) is None:
            with open("jsons/punishments.json", mode='r+', encoding='UTF-8') as file:
                data = json.load(file)
                if data['sentenced'].get(f'{after.id}') is not None and float(data['sentenced'].get(f'{after.id}')['time']) < datetime.utcnow().timestamp():
                    data['sentenced'].pop(f'{after.id}')
                    file.seek(0)
                    file.truncate()
                    json.dump(data, file, indent=4)
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


bot.run(bot_token)
"""
async def start_count_to_dc(vc):
    await sleep(10)
    await lock_playing_state.acquire()
    if is_playing:
        lock_playing_state.release()
        return
    else:
        await vc.disconnect()
        lock_playing_state.release()


@client.event
async def on_ready():
    with open('Quotes.txt', encoding='UTF-8') as f:
        for line in f:
            quotes_buffer.append(line)
    print(f'We have logged in as {client.user}')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.channel.name not in allowed_text_channels:
        return

    if message.content.startswith('$hello'):
        await message.channel.send('' + check_volume('./Data/phoenix.mp3'))
    elif message.content.startswith('/quote'):
        await message.channel.send(quotes_buffer[random.Random.randint(random.Random(), 0, len(quotes_buffer) - 1)])


@client.event
async def on_voice_state_update(member, before, after):
    global is_playing

    await sleep(0.2)
    # check if now members are 1 - just bot then dc
    if before.channel is not None or after.channel is None or member.bot:
        return
    # if any(e.id == client.user.id for e in after.channel.members):
    #    return
    vc = None
    # accessing volitile value "client.voice_clients"
    try:
        if len(client.voice_clients) > 0:
            if client.voice_clients[0].channel != after.channel:
                await client.voice_clients[0].disconnect()
                vc = await after.channel.connect()
        else:
            vc = await after.channel.connect()
    except discord.ClientException:
        print("i got bobo with connect with multiple requests")
        vc = await after.channel.connect()

    # check if playing already
    await lock_playing_state.acquire()
    if is_playing:
        lock_playing_state.release()
        return
    else:
        is_playing = True
        lock_playing_state.release()

    # check if user in db to play
    path_to_file = './Data/phoenix.mp3'
    # standardize volume
    check_volume(path_to_file)
    # play the background sound
    # change to load file as correct base with use of 'ffmpeg -i sample.avi -ss 00:03:05 -t 00:00:45.0 -q:a 0 -map a sample.mp3' from min 3.05 take 45 sec and convert to mp3
    test = str(
        subprocess.run(
            './ffmpeg/bin/ffmpeg.exe -hide_banner -i \'.\Data\phoenix.mp3\' -filter:a volumedetect -f null /dev/null',
            capture_output=True, stdin=subprocess.DEVNULL).stdout, "utf-8"
    )
    print(test)
    vc.play(
        discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(executable='ffmpeg/bin/ffmpeg.exe',
                                   source=path_to_file),
            # add check volume    '.\yt1s.com - there is no need to be upset.mp3'
            default_volume
        )
    )
    # stop after default length
    await asyncio.sleep(default_length_time)
    if vc.is_playing():
        vc.stop()

    # return lock to allow only one play
    await lock_playing_state.acquire()
    is_playing = False
    lock_playing_state.release()
    # start disconnect countdown
    await start_count_to_dc(vc)
    # await vc.disconnect()


client.run(bot_token)"""
