import os
import email
import asyncio
import imaplib as ilib
from pytz import timezone
#from pprint import pprint # optional 
from bs4 import BeautifulSoup
#from datetime import datetime
from email.header import decode_header
from dotenv import load_dotenv, find_dotenv
from modules.sqlite import SQLObj
from modules.logger import logger

load_dotenv(find_dotenv())

db = SQLObj('database/uni.db')

tz_info = timezone('Europe/Moscow')

def check_mailbox(host, user, password, _id :int=123):
	try:
		imap_client = ilib.IMAP4_SSL(host=host)

		imap_client.login(user, password)
		imap_client.select('inbox')
	except:
		logger.debug('[-] <Email Error> Email connection error')
		return

	_, messages = imap_client.uid('search', 'UNSEEN', 'ALL', 'FROM "anketa@sut.ru"')
	
	for msg in messages[0].split()[::-1]:
		_, data = imap_client.uid('fetch', msg, '(RFC822)')
		
		converted_msg = email.message_from_bytes(data[0][1])
		msg_date = email.utils.parsedate_to_datetime(converted_msg.get('Date')).astimezone(tz_info).strftime("%Y-%m-%d %H:%M:%S")
		msg_id = converted_msg.get('Message-ID').split('.')[0].strip('<')
		msg_header = decode_header(converted_msg.get('Subject'))[0][0].decode('cp1251')
		
		raw_msg_content = converted_msg.get_payload()
		
		if converted_msg.is_multipart():
			raw_msg_content = ''.join([part.get_payload() for part in raw_msg_content if part.get_content_type() == 'text/plain'])

		soup = BeautifulSoup(raw_msg_content, 'lxml')
		msg_content = soup.get_text()

		file_in_msg = 'Прикрепленные файлы: смотрите в личном кабинете СПбГУТ.' in msg_content
		msg_content = msg_content.replace('Прикрепленные файлы: смотрите в личном кабинете СПбГУТ.', '') if file_in_msg else msg_content
		start_content = msg_content.find('Сообщение')
		end_content = msg_content.find('Отправитель')
		msg_sender = msg_content[end_content + len('Отправитель ') : msg_content.find('Отвечать необходимо в личном кабинете,')].strip()

		db.add_message(
			_id = _id, 
			message_id = msg_id, 
			m_date = msg_date, 
			m_sender = msg_sender, 
			m_type = 1 if msg_header == 'Загружены файлы в личном кабинете' else 0, 
			m_text = msg_content[start_content : end_content].replace('Сообщение: ', '', 1), 
			m_file = file_in_msg
		)

	imap_client.logout()

async def get_mail(_id: int):
	loop = asyncio.get_event_loop()
	await loop.run_in_executor(None, check_mailbox, 'imap.yandex.ru', os.environ['EMAIL'], os.environ['PASS_MAIL'], _id)

if __name__ == '__main__':
	asyncio.run(get_mail())
