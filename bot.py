import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

import globals
import quote_to_image
from db_bridge import DBBridge
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
    if globals.db.is_new_quote_time():
        q_id = await quote_to_image.generate_image()
        globals.db.update_config_last_used_quote(q_id)

    await interactions.response.send_message(
        file=discord.File('text_image.png', 'Mądrość dnia.png')
    )



@bot.tree.command(name='explain', description='Dodatkowe informacje \"lore\" ostatniej wypowiedzi')
async def explain(interactions):
    res = globals.db.get_explanation()
    interactions.response.send_message(
        res if res else "No quote response to send",
        ephemeral=True
    )


@bot.tree.command(name='submit', description='Możliwość dodania własnego cytatu')
async def submit(interactions):
    interactions.response.send_message(
        f'Password: "{os.getenv('USER_PASS')}"\nFunctionality moved to here https://{os.getenv("SITE_URL")}', ephemeral=True,
        delete_after=60
    )

if __name__ == '__main__':
    load_dotenv()
    try:
       globals.db = DBBridge()
    except Exception as e:
        print(f"failed to start DB {e}")
        exit()
    bot.run(globals.db.get_config().bot_token)
