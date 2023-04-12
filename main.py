from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, CallbackContext, ContextTypes, MessageHandler, filters, JobQueue, Job

import os
import logging
import asyncio

import datetime
from pytz import timezone
from datetime import timedelta
from datetime import datetime as dt

from dotenv import load_dotenv, find_dotenv

from modules.sqlite import SQLObj
from modules.schedule_parser import get_schedule
from modules.button_click import async_click_start
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
	
	settings = db.get_settings(user.id)
	if settings:
		usid, chid, *settings = settings[0]

		#print(settings)
		if all(settings):
			await update.message.reply_text(
				f"Ваш ID {user.id}, уже был зарегистрирован в базе данных бота!"
			)
		else:
			chat_id = update.effective_message.chat_id
			db_result = bool(db.set_settings(_id=user.id, _chat_id=chat_id, get_mail=True, get_files=True, get_schedule=True, auto_click_button=True))
			
			jobs_result = bool(create_jobs(context, _id=user.id))
			await update.message.reply_text(
				f"Готово! Ваш ID {user.id}, был зарегистрирован в боте (Проверка записи в базу данных : {db_result}) (Проверка записи данных в расписание бота : {jobs_result})!"
			)
	else:
		chat_id = update.effective_message.chat_id
		db_result = bool(db.set_settings(_id=user.id, _chat_id=chat_id, get_mail=True, get_files=True, get_schedule=True, auto_click_button=True))

		jobs_result = bool(create_jobs(context, _id=user.id))
		await update.message.reply_text(
			f"Готово! Ваш ID {user.id}, был зарегистрирован в боте (Проверка записи в базу данных : {db_result}) (Проверка записи данных в расписание бота : {jobs_result})!"
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
	
	settings = db.get_settings(user.id)
	if settings:
		usid, chid, *settings = settings[0]

		#print(settings)

		if any(settings):
		
			jobs_result = delete_jobs(context, _id=user.id)

			chat_id = update.effective_message.chat_id
			db_result = bool(db.set_settings(_id=user.id, _chat_id=chat_id, get_mail=False, get_files=False, get_schedule=False, auto_click_button=False))
			await update.message.reply_text(
				f"Готово! Ваш ID {user.id}, был убран из базы данных бота (Проверка вывода из базы данных : {db_result}) (Проверка вывода данных из расписания бота : {bool(jobs_result)} (Удалены расписания бота с кодовыми названиями {jobs_result}))!"
			)
		else:
			await update.message.reply_text(
				f"Ваш ID {user.id}, не находился в базе данных бота!"
			)
	else:
		await update.message.reply_text(
			f"Ваш ID {user.id}, не находился в базе данных бота!"
		)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(f'Wait a 5 seconds, start operation')
	button_result = await async_click_start(update.effective_user.id)
	if not button_result:
		result = 'Button wasn\'t clicked'
	await update.message.reply_text(f'Готово! \n{result}')


# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(
#         f"User exists in db : {db.get_settings(_id: int, get_mail: bool=False, get_files: bool=False, get_schedule: bool=False, auto_click_button: bool=False)}"
#     )

# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# 	await update.message.reply_text('I don\'t know this command')

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

async def create_button_click(context: CallbackContext):
	# await update.message.reply_text(f'Wait a 5 seconds, start parsing')
	job = context.job
	#print(job.data, ' start ')
	result = await async_click_start(_id = job.user_id)
	
	
	if job.chat_id and result:
		current_job = context.job_queue.get_jobs_by_name(job.data)
		if current_job:
			for job in current_job:
				job.schedule_removal()

		db.delete_pairs(job.user_id, [job.data])
		await context.bot.send_message(job.chat_id, text=f'Пара №{job.data}: \n{result}')

async def create_email_parser(context: CallbackContext):
	job = context.job
	result = await mfc_start_parse(job.user_id)
	if not result:
		return

	result = sorted(result, key=lambda item: item.get('m_date'))

	if job.chat_id:
		for v in result:
			start_message = 'Файлы группы.' if v.get('m_type') else 'Сообщение студенту.'
			date = dt.strptime(v.get('m_date'), '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S %d.%m.%Y')
			if v.get('links'):
				await context.bot.send_message(job.chat_id, f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date} \nСсылки: {" ".join(v.get("links"))}')
			else:
				await context.bot.send_message(job.chat_id, f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date}')

		db.delete_file_by_user(_id=job.user_id)
		db.delete_message_by_user(_id=job.user_id)


def delete_jobs(application, _id: int):
	jobs = []
	for k in [1, 2, 3, 4, 5, 6, 86]:
		current_jobs = application.job_queue.get_jobs_by_name(f'{_id}_{k}')
		for job in current_jobs:
			job.schedule_removal()
			jobs.append(job.name)
	
	current_jobs = application.job_queue.get_jobs_by_name(f'email_{_id}')
	for job in current_jobs:
		job.schedule_removal()
		jobs.append(job.name)

	current_jobs = application.job_queue.get_jobs_by_name(f'schedule_{_id}')
	for job in current_jobs:
		job.schedule_removal()
		jobs.append(job.name)

	return jobs

def create_jobs(application, *, _id: int=None):
	moscow = timezone('Europe/Moscow')
	time = datetime.time(hour=8, tzinfo=moscow)
	
	job_queue = application.job_queue

	_id = _id or OWNER_ID

	mail, files, schedule, auto_click = (False, False, False, False)
	
	settings = db.get_settings(_id)
	if settings:
		*ids, mail, files, schedule, auto_click = settings[0]

	if mail:
		job_queue.run_repeating(create_email_parser, interval=60*1, name=f'email_{_id}', user_id=_id, chat_id=_id)
	
	if schedule or auto_click:
		job_queue.run_daily(create_schedule_checker, time, name=f'schedule_{_id}', user_id=_id, chat_id=_id)

		if auto_click:
			dict_pairs = {
				1: datetime.time(hour=8, minute=50),
				2: datetime.time(hour=10, minute=35),
				3: datetime.time(hour=12, minute=50),
				4: datetime.time(hour=14, minute=35),
				5: datetime.time(hour=16, minute=20),
				6: datetime.time(hour=18, minute=5),
				86: datetime.time(hour=13, minute=20),
			} 

			db_pairsdb = db.get_pairs(OWNER_ID)

			for k in db_pairsdb:
				start_time = dt.combine(dt.today(), dict_pairs.get(k, datetime.time(hour=8, minute=50)))
				end_time = start_time + timedelta(minutes=100)
				
				start_time = moscow.localize(start_time)
				end_time = moscow.localize(end_time)

				#print(start_time, end_time, start_time.tzinfo)

				job_queue.run_repeating(
					create_button_click, 
					name=f'{_id}_{k}',
					first=start_time, 
					interval=60*5, 
					last=end_time, 
					user_id=_id, 
					chat_id=_id, 
					data=k
				)

	return True


def main() -> None:
	application = Application.builder().token(os.environ['TOKEN']).build()

	create_jobs(application)

	application.add_handler(CommandHandler("subscribe", subscribe, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler("unsubscribe", unsubscribe, filters=filters.User(user_id=OWNER_ID)))
	#application.add_handler(CommandHandler("help", help_command))
	application.add_handler(CommandHandler('pairs', pairs, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler('messages', messages, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler('button', button_click, filters=filters.User(user_id=OWNER_ID)))

	#application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

	application.run_polling()

if __name__ == "__main__":
	main()