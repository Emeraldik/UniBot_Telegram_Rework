from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import os
import logging
from dotenv import load_dotenv, find_dotenv

from modules.sqlite import SQLObj
from modules.schedule_parser import *

load_dotenv(find_dotenv())

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

database = SQLObj('database/uni.db')

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    database.add_user(user.id)
    await update.message.reply_text(
        f"Hi {user.name}, your user_id was appended to db : {user.id}!"
    )

async def pairs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    schedule = await get_schedule(autoweekday=True)
    result = " ".join([i[0] for i in schedule.values()])
    if not result:
        result = 'No pairs'
    await update.message.reply_text(f'Pairs today : {result}')

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    database.update_user(user.id, False)
    await update.message.reply_text(
        f"Hi {user.name}, your user_id was deleted from db : {user.id}!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        f"User exists in db : {database.get_user_status(update.effective_user.id)}"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

def main() -> None:
    application = Application.builder().token(os.environ['TOKEN']).build()

    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler('pairs', pairs))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()

if __name__ == "__main__":
    main()