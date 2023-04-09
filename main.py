from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import os
import logging
from dotenv import load_dotenv, find_dotenv
from datetime import datetime

from modules.sqlite import SQLObj
from modules.schedule_parser import get_schedule
from modules.message_files_collector import start_parse as mfc_start_parse

load_dotenv(find_dotenv())

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

db = SQLObj('database/uni.db')

def is_owner(func):
    async def wrapper(update: Update, *args, **kwargs):
        if update.effective_user.id == os.environ['OWNER']:
            await func(update, *args, **kwargs)
        else:
            await update.message.reply_text(
                f"You don't have enough permissions!"
            )
    return wrapper

@is_owner
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.set_settings(_id=user.id, get_mail=True, get_files=True, get_schedule=True, auto_click_button=True)
    await update.message.reply_text(
        f"Hello {user.name}, your user_id was appended to db : {user.id}!"
    )

@is_owner
async def pairs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Wait a 5 seconds, start parsing')
    schedule = await get_schedule(autoweekday=True)
    result = " ".join([i[0] for i in schedule.values()])
    if not result:
        result = 'No pairs'
    await update.message.reply_text(f'Pairs today : {result}')

@is_owner
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Wait a 10 seconds, start parsing')
    result = await mfc_start_parse(update.effective_user.id)
    if not result:
        await update.message.reply_text('No messages')
        return

    result = sorted(result, key=lambda item: item.get('m_date'))

    # for k in result:
    #     print(k)
    for v in result:
        start_message = 'Файлы группы.' if v.get('m_type') else 'Сообщение студенту.'
        date = datetime.strptime(v.get('m_date'), '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S %d.%m.%Y')
        if v.get('links'):
            await update.message.reply_text(f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date} \nСсылки: {" ".join(v.get("links"))}')
        else:
            await update.message.reply_text(f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date}')

        db.delete_file(_id=update.effective_user.id, file_id=v.get('file_id', 0))
        #db.delete_message(_id=update.effective_user.id, message_id=v.get('message_id', 0))

    db.delete_message_by_user(_id=update.effective_user.id)

@is_owner
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    db.set_settings(_id=user.id, get_mail=False, get_files=False, get_schedule=False, auto_click_button=False)
    await update.message.reply_text(
        f"Hello {user.name}, your user_id was deleted from db : {user.id}!"
    )

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(
#         f"User exists in db : {db.get_settings(_id: int, get_mail: bool=False, get_files: bool=False, get_schedule: bool=False, auto_click_button: bool=False)}"
#     )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

def main() -> None:
    application = Application.builder().token(os.environ['TOKEN']).build()

    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))
    #application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler('pairs', pairs))
    application.add_handler(CommandHandler('messages', messages))


    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    application.run_polling()

if __name__ == "__main__":
    main()