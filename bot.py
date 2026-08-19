import asyncio
import logging
import os

import discord
from aiohttp.web_runner import AppRunner
from discord.ext import commands
from dotenv import load_dotenv

import context
from db_bridge import DBBridge
from quote_to_image import render_quote_image, generate_daily_image, IMAGE_PATH
from web import start_server

log = logging.getLogger(__name__)


class QuoteBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=';', intents=intents)
        self.runner: AppRunner | None = None

    async def setup_hook(self) -> None:
        self.runner = await start_server()
        synced = await self.tree.sync()
        log.info(f"synced {len(synced)} commands")

    async def close(self) -> None:
        if self.runner is not None:
            await self.runner.cleanup()
        await super().close()


bot = QuoteBot()


@bot.event
async def on_ready() -> None:
    log.info("logged in as %s", bot.user)


@bot.tree.command(name='quote', description='Najlepsze kwestie jakie na przestrzeni lat padły na niniejszym serwerze')
async def quote(interaction: discord.Interaction) -> None:
    await interaction.response.defer()
    if context.db.is_new_quote_time():
        q_id = await asyncio.to_thread(generate_daily_image)
        context.db.update_config_last_used_quote(q_id)

    elif not IMAGE_PATH.exists():
        last = context.db.get_specific_quote_with_joins(context.db.get_config().last_quote_id)
        if last is None:
            q_id = await asyncio.to_thread(generate_daily_image)
            context.db.update_config_last_used_quote(q_id)
        else:
            await asyncio.to_thread(render_quote_image, last)

    await interaction.followup.send(
        file=discord.File(IMAGE_PATH, 'Mądrość dnia.png')
    )




@bot.tree.command(name='explain', description='Dodatkowe informacje \"lore\" ostatniej wypowiedzi')
async def explain(interactions):
    res = globals.db.get_explanation()
    await interactions.response.send_message(
        res if res else "No quote response to send",
        ephemeral=True
    )


@bot.tree.command(name='submit', description='Możliwość dodania własnego cytatu')
async def submit(interactions):
    await interactions.response.send_message(
        f'Password: "{os.getenv('USER_PASS')}"\nFunctionality moved to here https://{os.getenv("SITE_URL")}', ephemeral=True,
        delete_after=60
    )


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    missing = [k for k in ("SECRET_KEY", "USER_PASS", "MASTER_PASS", "LOCAL_ADDRESS", "LOCAL_PORT", "SITE_URL")
               if not os.getenv(k)]
    if missing:
        raise SystemExit(f"missing env vars: {', '.join(missing)}")

    try:
        context.db = DBBridge(os.getenv("DB_PATH", "quotes.db"))
    except Exception:
        logging.exception("failed to start DB")
        raise SystemExit(1)

    bot.run(context.db.get_config().bot_token)


if __name__ == '__main__':
    main()