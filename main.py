from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, CallbackContext, ContextTypes, MessageHandler, filters, JobQueue, Job

import os
import logging
#import asyncio
#import aiofiles.os

import datetime
from datetime import timedelta
from datetime import datetime as dt

from dateutil.utils import today
from dateutil.tz import gettz

from dotenv import load_dotenv, find_dotenv
from keep_alive import keep_alive

from modules.sqlite import SQLObj
from modules.schedule_parser import get_schedule
from modules.file_downloader import start_download
from modules.button_click import async_click_start
from modules.message_files_collector import start_parse as mfc_start_parse
from modules.hdrezka import async_get_new_hdrezka

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
	await update.message.reply_text(f'Ожидайте примерно 5 сек.')
	user_id = update.effective_user.id
	schedule = await get_schedule(autoweekday=True)
	db.clear_pairs(user_id)
	db.add_pairs(user_id, [i for i in schedule.keys()])
	
	result = "\n".join([(f'{k}: {v[0]}') for k, v in schedule.items()])
	if not result:
		result = 'Пар нет'
	await update.message.reply_text(f'Пары: \n{result}')

#@is_owner
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	await update.message.reply_text(f'Ожидайте примерно 10 сек.')
	try:
		result = await mfc_start_parse(update.effective_user.id)
	except:
		await update.message.reply_text(f'Что-то пошло не так.')
	else:
		if not result:
			await update.message.reply_text('Нет сообщений')
			return

		result = sorted(result, key=lambda item: item.get('m_date'))

		for v in result:
			start_message = 'Файлы группы.' if v.get('m_type') else 'Сообщение студенту.'
			date = dt.strptime(v.get('m_date'), '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S %d.%m.%Y')
			await update.message.reply_text(f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date}')
			if v.get('links'):
				files_names = await start_download(v.get('links'))
				for file in files_names:
					await update.message.reply_document(document=open(file, 'rb'))
					os.remove(file)

		db.delete_file_by_user(_id=update.effective_user.id)
		db.delete_message_by_user(_id=update.effective_user.id)

#@is_owner
async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	user = update.effective_user
	
	settings = db.get_settings(user.id)
	if settings:
		usid, chid, *settings = settings[0]

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
	await update.message.reply_text(f'Ожидайте 5 сек.')
	try:
		button_result = await async_click_start(update.effective_user.id, with_print=True)
	except:
		await update.message.reply_text(f'Что-то пошло не так.')
	else:
		if not button_result:
			result = 'Кнопка не нажата'
		await update.message.reply_text(f'Готово! \n{result}')


async def hdrezka(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	link = db.get_links(l_type='hdrezka')
	await update.message.reply_text(f'Рабочая? Ссылка на сайт HDRezka: {link}')

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(
#         f"User exists in db : {db.get_settings(_id: int, get_mail: bool=False, get_files: bool=False, get_schedule: bool=False, auto_click_button: bool=False)}"
#     )

# async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
# 	await update.message.reply_text('I don\'t know this command')

# def callback_30(context: CallbackContext):
# 	context.bot.send_message(text='A single message with 30s delay')

async def create_schedule_checker(context: CallbackContext):
	job = context.job
	schedule = await get_schedule(autoweekday=True)
	db.clear_pairs(job.user_id)
	db.add_pairs(job.user_id, [i for i in schedule.keys()])
		
	# if job.chat_id:
	# 	result = "\n".join([(f'{k}: {v[0]}') for k, v in schedule.items()])
	# 	if not result:
	# 		result = 'No pairs'
		
	# 	await context.bot.send_message(job.chat_id, text=f'Pairs today : \n{result}')

	create_jobs(context, _id=job.user_id)

	current_job = context.job_queue.get_jobs_by_name(f'schedule_{job.user_id}')
	if current_job:
		for job in current_job:
			job.schedule_removal()


async def create_button_click(context: CallbackContext):
	job = context.job

	result = None
	try:
		result = await async_click_start(_id = job.user_id)
	except Exception as e:
		logger.error(e)	
	
	if job.chat_id and result:
		current_job = context.job_queue.get_jobs_by_name(f'{job.user_id}_{job.data}')
		if current_job:
			for job in current_job:
				job.schedule_removal()

		db.delete_pairs(job.user_id, [job.data])
		await context.bot.send_message(job.chat_id, text=f'Пара №{job.data}: \n{result}')

async def create_email_parser(context: CallbackContext):
	job = context.job
	
	result = None
	try:
		result = await mfc_start_parse(job.user_id)
	except Exception as e:
		logger.error(e)

	if not result:
		return

	result = sorted(result, key=lambda item: item.get('m_date'))

	if job.chat_id:
		for v in result:
			start_message = 'Файлы группы.' if v.get('m_type') else 'Сообщение студенту.'
			date = dt.strptime(v.get('m_date'), '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S %d.%m.%Y')
			await context.bot.send_message(job.chat_id, f'{start_message} \n\nТекст сообщения: {v.get("m_text")} \n\nОтправитель: {v.get("m_sender")} \nДата: {date}')
			if v.get('links'):
				files_names = await start_download(v.get('links'))
				for file in files_names:
					await context.bot.send_document(job.chat_id, document=open(file, 'rb'))
					os.remove(file)

		db.delete_file_by_user(_id=job.user_id)
		db.delete_message_by_user(_id=job.user_id)

async def create_hdrezka(context: CallbackContext):
	await async_get_new_hdrezka()

def delete_jobs(application, _id: int):
	jobs = []
	for k in [1, 2, 3, 4, 5, 6, 85]:
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

	current_jobs = application.job_queue.get_jobs_by_name(f'schedule_days_{_id}')
	for job in current_jobs:
		job.schedule_removal()
		jobs.append(job.name)

	return jobs

def create_jobs(application, *, _id: int=None):
	_id = _id or OWNER_ID
	delete_jobs(application, _id)

	moscow = gettz('Europe/Moscow')

	job_queue = application.job_queue

	mail, files, schedule, auto_click = (False, False, False, False)
	
	settings = db.get_settings(_id)
	if settings:
		*ids, mail, files, schedule, auto_click = settings[0]

	if mail:
		job_queue.run_repeating(create_email_parser, interval=60*2, name=f'email_{_id}', user_id=_id, chat_id=_id)
	
	if schedule:
		start_time = dt.combine(today(tzinfo=moscow), datetime.time(hour=2, tzinfo=moscow))
		end_time = start_time + timedelta(hours=6)
		
		# start_time = moscow.localize(start_time)
		# end_time = moscow.localize(end_time)

		job_queue.run_repeating(
			create_schedule_checker, 
			name=f'schedule_{_id}',
			first=start_time, 
			interval=30, 
			last=end_time, 
			user_id=_id, 
			chat_id=_id
		)

		job_queue.run_daily(
			create_schedule_checker, 
			name=f'schedule_days_{_id}',
			time=start_time,
			days = (1,2,4,5,6), 
			user_id=_id, 
			chat_id=_id
		)

	if auto_click:
		dict_pairs = {
			1: datetime.time(hour=8, minute=50, tzinfo=moscow),
			2: datetime.time(hour=10, minute=35, tzinfo=moscow),
			3: datetime.time(hour=12, minute=50, tzinfo=moscow),
			4: datetime.time(hour=14, minute=35, tzinfo=moscow),
			5: datetime.time(hour=16, minute=20, tzinfo=moscow),
			6: datetime.time(hour=18, minute=5, tzinfo=moscow),
			85: datetime.time(hour=13, minute=20, tzinfo=moscow),
		} 

		db_pairsdb = db.get_pairs(_id)

		for k in db_pairsdb:
			start_time = dt.combine(today(tzinfo=moscow), dict_pairs.get(k, datetime.time(hour=13, minute=20, tzinfo=moscow)))
			end_time = start_time + timedelta(minutes=100)
			
			# start_time = moscow.localize(start_time)
			# end_time = moscow.localize(end_time)

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
	
	job_queue = application.job_queue
	job_queue.run_repeating(create_hdrezka, interval=60*60*4, name='hdrezka')
	
	create_jobs(application)

	application.add_handler(CommandHandler("hdrezka", hdrezka))
	application.add_handler(CommandHandler("subscribe", subscribe, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler("unsubscribe", unsubscribe, filters=filters.User(user_id=OWNER_ID)))
	#application.add_handler(CommandHandler("help", help_command))
	application.add_handler(CommandHandler('pairs', pairs, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler('messages', messages, filters=filters.User(user_id=OWNER_ID)))
	application.add_handler(CommandHandler('button', button_click, filters=filters.User(user_id=OWNER_ID)))

	#application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

	keep_alive()
	application.run_polling()

if __name__ == "__main__":
	main()