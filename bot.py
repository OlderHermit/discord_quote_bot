import asyncio
import datetime
import json
import math
import os
import shutil
import sqlite3
from datetime import datetime, timedelta

import aiofiles
import aiohttp_cors
import discord
from aiohttp import web
from discord import Member
from discord.ext import commands, tasks
from sqlalchemy import create_engine, select, Engine, func
from sqlalchemy.orm import Session

import quote_to_image
from orm import Config, Base, Quote, Author

# "bot_token": "MTIyNjA5NzEzNDY3NjM0ODk1OQ.GCxcgb.EHZgupFdoiqxKf-AZzIbO7nwvYZWrsdHWwKBOc",
# "bot_token_test": "Nzc0NTczMDc0MTEyNzA4NjQ4.Gryj_9.sW0-C0WQ5AapulAEC0HM1HU__KlVNgdM9W41es"
validating_user = 321297277773938690

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=';', intents=discord.Intents.all())

lock_playing_state = asyncio.Lock()
path_to_db = 'quotes.db'
session: Session = None
engine: Engine = None
config: Config = None


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
    last_quote_time = config.last_used.timetuple()[0:3]
    today = datetime.utcnow().timetuple()[0:3]
    if today <= last_quote_time:
        await interactions.response.send_message(
            file=discord.File('text_image.png', 'Mądrość dnia.png')
            # "Today's message has been already sent", ephemeral=True
        )
        return

    q_id = await quote_to_image.generate_image(engine)
    await interactions.response.send_message(
        file=discord.File('text_image.png', 'Mądrość dnia.png')
    )

    config.last_used = datetime.utcnow()
    config.last_quote_id = q_id
    session.commit()


@bot.tree.command(name='explain', description='Dodatkowe informacje \"lore\" ostatniej wypowiedzi')
async def explain(interactions):
    res = session.scalars(select(Quote).where(Quote.id.is_(config.last_quote_id))).one_or_none()
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
        f"Functionality moved to here http://{config.address}:{config.port}", ephemeral=True, delete_after=60
    )


@bot.event
async def on_member_update(before: Member, after: Member):
    role_id = 1225828166497730741 # 1236360986970161283
    channel_id_to_shame = 368439253794947084

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
                        # <t:{math.ceil((float(data['sentenced'][f'{after.id}']['time'])) + time_difference)}:R>
                        # timedelta(seconds=math.ceil((float(data['sentenced'][f'{after.id}']['time'])) - datetime.utcnow().timestamp()))
                    )


async def start_server():
    # start web server
    app = web.Application()
    app.add_routes([web.post('/', submit_through_web)])
    app.add_routes([web.get('/', return_web_page_main)])
    app.add_routes([web.get('/approve', return_web_page_approve)])
    app.add_routes([web.post('/approve', approve_through_web)])
    app.add_routes([web.delete('/approve', delete_through_web)])
    app.add_routes([web.get('/authors', return_authors_data)])
    app.add_routes([web.get('/quotes/nomination', return_nominations_data)])
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
    site = web.TCPSite(runner, config.address, int(config.port))
    await site.start()
    print("website is on")


def check_sqlite_integrity():
    try:
        db = os.path.join(os.path.curdir, path_to_db)
        db_back = os.path.join(os.path.curdir, path_to_db + '_backup')
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
    global session, engine
    engine = create_engine(f"sqlite:///{path_to_db}")
    Base.metadata.create_all(engine)
    session = Session(engine)
    print("db is on")
    load_config()


def load_config():
    global config
    config = None
    config = session.scalars(select(Config).where(Config.id.is_(0))).one()
    print("config loaded")


async def return_web_page_main(request):
    return web.FileResponse(path=os.path.abspath('quote_web_ui/index.html'))


async def return_web_page_approve(request):
    return web.FileResponse(path=os.path.abspath('quote_web_ui/approve.html'))


async def return_authors_data(request):
    authors = list(map(lambda a: a.id, session.scalars(select(Author)).all()))
    return web.json_response(
        json.dumps(authors, indent=4, ensure_ascii=False)
    )


async def return_nominations_data(request):
    quotes_to_accept = list(map(lambda q: (q[0].as_dict(), q[1]),
        session.execute(
            select(Quote, func.group_concat(Author.id, ', ').label("authors"))
            .join(Quote.authors)
            .where(Quote.confirmed.is_(False))
            .where(Quote.deleted.is_(False))
            .group_by(Quote.id)
        ).all()))
    return web.json_response(
        quotes_to_accept
    )


async def submit_through_web(request):
    try:
        data = json.loads((await request.json()))

        if type(data['quote']) is not str:
            new_quote = Quote(
                quote='[NEW_SENTENCE]'.join(data['quote']),
                date=data['date'],
                explanation=data['explanation'],
                confirmed=False
            )
            for a in session.scalars(select(Author).where(Author.id.in_(data['author'].split(';')))).all():
                new_quote.authors.append(a)
        else:
            new_quote = Quote(
                quote=data['quote'],
                date=data['date'],
                explanation=data['explanation'],
                confirmed=False
            )
            new_quote.authors.append(
                session.scalars(select(Author).where(Author.id.in_(data['author'].split(';')))).one()
            )

        session.add(new_quote)
        session.commit()

        return web.json_response({'status': 'success', 'message': 'Quote added to DB'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)


async def approve_through_web(request):
    try:
        quote_id = json.loads((await request.json()))['id']
        if quote_id is None:
            raise ValueError('quote_id colundn\'t be read from request')

        candidate = session.execute(select(Quote).where(Quote.id.is_(quote_id))).scalar_one_or_none()
        if candidate is None:
            raise IndexError('There was no quote for given id')

        candidate.confirmed = True
        session.commit()
        return web.json_response({'status': 'success', 'message': 'Quote approved'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)


async def delete_through_web(request):
    try:
        quote_id = json.loads((await request.json()))['id']
        if quote_id is None:
            raise ValueError('quote_id colundn\'t be read from request')

        candidate = session.execute(select(Quote).where(Quote.id.is_(quote_id))).scalar_one_or_none()
        if candidate is None:
            raise IndexError('There was no quote for given id')

        candidate.deleted = True
        session.commit()
        return web.json_response({'status': 'success', 'message': 'Quote discarded'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)


@tasks.loop(seconds=2)
async def ticker():
    print("hello")


start_db()
if config is None:
    print('Couldn\'t load bot token from db')
    exit()
bot.run(config.bot_token)
