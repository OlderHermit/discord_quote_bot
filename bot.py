import datetime
import json
import math
import os
import shutil
import sqlite3
import aiofiles
import discord

from cryptography.fernet import Fernet
from discord import Member
from discord.ext import commands, tasks
from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

import quote_to_image
import globals

from orm import Config, Base, Quote
from web import start_server

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=';', intents=discord.Intents.all())


@bot.event
async def on_ready():
    try:
        c = await bot.tree.sync()
        print(f'Synced {len(c)} commands')
    except Exception as e:
        print(f'got {e}')
    # ticker.start()
    await bot.loop.create_task(start_server())

    print(f'We have logged in as {bot.user.name}')


@bot.tree.command(name='quote', description='Najlepsze kwestie jakie na przestrzeni lat padły na niniejszym serwerze')
async def quote(interactions):
    load_config()
    last_quote_time = globals.config.last_used.timetuple()[0:3]
    today = datetime.now(timezone.utc).timetuple()[0:3]
    if today <= last_quote_time:
        await interactions.response.send_message(
            file=discord.File('text_image.png', 'Mądrość dnia.png')
            # "Today's message has been already sent", ephemeral=True
        )
        return

    q_id = await quote_to_image.generate_image(globals.engine)
    await interactions.response.send_message(
        file=discord.File('text_image.png', 'Mądrość dnia.png')
    )

    globals.config.last_used = datetime.now(timezone.utc)
    globals.config.last_quote_id = q_id
    globals.session.commit()


@bot.tree.command(name='explain', description='Dodatkowe informacje \"lore\" ostatniej wypowiedzi')
async def explain(interactions):
    res = globals.session.scalars(select(Quote).where(Quote.id.is_(globals.config.last_quote_id))).one_or_none()
    if res is None:
        await interactions.response.send_message(
            "No quote response to send", ephemeral=True
        )
        return
    await interactions.response.send_message(
        res.explanation,
        ephemeral=True
    )


@bot.tree.command(name='submit', description='Możliwość dodania własnego cytatu')
async def submit(interactions):
    await interactions.response.send_message(
        f"Password: \"{os.getenv('USER_PASS')}\"\nFunctionality moved to here {os.getenv('SITE_URL')}", ephemeral=True,
        delete_after=60
    )


@bot.event
async def on_member_update(before: Member, after: Member):
    role_id = 1225828166497730741  # 1236360986970161283
    channel_id_to_shame = 368439253794947084

    if before.get_role(role_id) is None:
        if after.get_role(role_id) is not None:
            async with aiofiles.open("jsons/punishments.json", mode='r+', encoding='UTF-8') as file:
                data = json.loads(await file.read())
                if data['sentenced'].get(f'{after.id}') is None:
                    data['sentenced'].update({
                        f'{after.id}': {
                            'name': f'{after.name}',
                            'time': f'{(datetime.now(timezone.utc) + timedelta(seconds=5)).timestamp()}'
                        }
                    })
                    await file.seek(0)
                    await file.writelines(json.dumps(data, indent=4))

    elif before.get_role(role_id) is not None:
        if after.get_role(role_id) is None:
            async with aiofiles.open("jsons/punishments.json", mode='w+', encoding='UTF-8') as file:
                data = json.loads(await file.read())
                if data['sentenced'].get(f'{after.id}') is not None and float(
                        data['sentenced'].get(f'{after.id}')['time']) < datetime.now(timezone.utc).timestamp():
                    data['sentenced'].pop(f'{after.id}')
                    await file.seek(0)
                    await file.writelines(json.dumps(data, indent=4, ensure_ascii=False))
                    await after.guild.get_channel(channel_id_to_shame).send(
                        f"```ansi\n"
                        f"Użytkownik [0;33m{before.name}[0m został oczyszczony z karnej roli [0;36m{before.get_role(role_id).name}\n"
                        f"```"
                    )
                else:
                    time_difference = (datetime.now() - datetime.now(timezone.utc)).total_seconds()
                    await after.add_roles(before.get_role(role_id))
                    await after.guild.get_channel(channel_id_to_shame).send(
                        f"```ansi\n"
                        f"Użytkownik [0;33m{after.name}[0m próbował usunąć karną rolę [0;36m{after.get_role(role_id).name} [1;36mSHAME ON HIM [0mpozostały czas kary: [1;32m{timedelta(seconds=math.ceil((float(data['sentenced'][f'{after.id}']['time'])) - datetime.now(timezone.utc).timestamp()))}\n"
                        f"```"
                        # <t:{math.ceil((float(data['sentenced'][f'{after.id}']['time'])) + time_difference)}:R>
                        # timedelta(seconds=math.ceil((float(data['sentenced'][f'{after.id}']['time'])) - datetime.utcnow().timestamp()))
                    )


def check_sqlite_integrity():
    try:
        db = os.path.join(os.path.curdir, globals.path_to_db)
        db_back = os.path.join(os.path.curdir, globals.path_to_db + '_backup')
        with sqlite3.connect(db) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            if result[0] == "ok":
                print("Database is intact.")
                shutil.copy(db, db_back)
                return True
            else:
                print("Database is corrupted:", result[0])
                return False

    except sqlite3.Error as e:
        print("Error accessing the database:", e)
        return False


def start_db():
    if not check_sqlite_integrity():
        print("db cound not be started")
        return
    globals.engine = create_engine(f"sqlite:///{globals.path_to_db}")
    Base.metadata.create_all(globals.engine)
    globals.session = Session(globals.engine)
    print("db is on")
    load_config()


def load_config():
    globals.config = globals.session.scalars(select(Config).where(Config.id.is_(0))).one()
    globals.cipher_suite = Fernet(os.getenv("SECRET_KEY"))
    print("config loaded")


@tasks.loop(seconds=2)
async def ticker():
    print("hello")


load_dotenv()
start_db()
if globals.config is None:
    print('Couldn\'t load bot token from db')
    exit()
bot.run(globals.config.bot_token)
