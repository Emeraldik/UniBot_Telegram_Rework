from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, CallbackContext, ContextTypes, MessageHandler, filters, JobQueue, Job

import os
import logging
import asyncio
from dotenv import load_dotenv, find_dotenv
import datetime
from datetime import datetime as dt
from pytz import timezone

from modules.sqlite import SQLObj
from modules.schedule_parser import get_schedule
from modules.message_files_collector import start_parse as mfc_start_parse

load_dotenv(find_dotenv())

OWNER_ID = int(os.environ['OWNER'])

# Enable logging
logging.basicConfig(
	format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

db = SQLObj('database/uni.db')

# def is_owner(func):
#     async def wrapper(update: Update, *args, **kwargs):
#         if update.effective_user.id == os.environ['OWNER']:
#             await func(update, *args, **kwargs)
#         else:
#             await update.message.reply_text(
#                 f"You don't have enough permissions!"
#             )
#     return wrapper

#@is_owner
async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	user = update.effective_user
	chat_id = update.effective_message.chat_id
	db.set_settings(_id=user.id, _chat_id=chat_id, get_mail=True, get_files=True, get_schedule=True, auto_click_button=True)
	await update.message.reply_text(
		f"Hello {user.name}, your user_id was appended to db : {user.id}!"
	)

#@is_owner
async def pairs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(f'Wait a 5 seconds, start parsing')
	schedule = await get_schedule(autoweekday=True)
	result = "\n".join([(f'{k}: {v[0]}') for k, v in schedule.items()])
	if not result:
		result = 'No pairs'
	await update.message.reply_text(f'Pairs today : \n{result}')

#@is_owner
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(f'Wait a 10 seconds, start parsing')
	result = await mfc_start_parse(update.effective_user.id)
	if not result:
		await update.message.reply_text('No messages')
		return

	result = sorted(result, key=lambda item: item.get('m_date'))

	for v in result:
		start_message = 'Файлы группы.' if v.get('m_type') else 'Сообщение студенту.'
		date = dt.strptime(v.get('m_date'), '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S %d.%m.%Y')
		if v.get('links'):
			await update.message.reply_text(f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date} \nСсылки: {" ".join(v.get("links"))}')
		else:
			await update.message.reply_text(f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date}')

	db.delete_file_by_user(_id=update.effective_user.id)
	db.delete_message_by_user(_id=update.effective_user.id)

#@is_owner
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	user = update.effective_user
	chat_id = update.effective_message.chat_id
	db.set_settings(_id=user.id, _chat_id=chat_id, get_mail=False, get_files=False, get_schedule=False, auto_click_button=False)
	await update.message.reply_text(
		f"Hello {user.name}, your user_id was deleted from db : {user.id}!"
	)

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(
#         f"User exists in db : {db.get_settings(_id: int, get_mail: bool=False, get_files: bool=False, get_schedule: bool=False, auto_click_button: bool=False)}"
#     )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(update.message.text)

# def callback_30(context: CallbackContext):
# 	context.bot.send_message(text='A single message with 30s delay')

async def create_schedule_checker(context: CallbackContext):
	# await update.message.reply_text(f'Wait a 5 seconds, start parsing')
	job = context.job
	if job.chat_id:
		schedule = await get_schedule(autoweekday=True)
		db.clear_pairs(job.user_id)
		db.add_pairs(job.user_id, [i for i in schedule.keys()])
		result = "\n".join([(f'{k}: {v[0]}') for k, v in schedule.items()])
		if not result:
			result = 'No pairs'

		await context.bot.send_message(job.chat_id, text=f'Pairs today : \n{result}')

def create_jobs(application):
	time = datetime.time(hour=8, tzinfo=timezone('Europe/Moscow'))
	
	job_queue = application.job_queue
	job_queue.run_daily(create_schedule_checker, time, user_id=OWNER_ID, chat_id=OWNER_ID)


def main() -> None:
	application = Application.builder().token(os.environ['TOKEN']).build()

	create_jobs(application)

	application.add_handler(CommandHandler("subscribe", subscribe, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler("unsubscribe", unsubscribe, filters=filters.User(user_id=OWNER_ID)))
	#application.add_handler(CommandHandler("help", help_command))
	application.add_handler(CommandHandler('pairs', pairs, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler('messages', messages, filters=filters.User(user_id=OWNER_ID)))


	application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

	application.run_polling()

if __name__ == "__main__":
	main()