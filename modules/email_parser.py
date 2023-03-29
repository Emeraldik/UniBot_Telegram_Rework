import os
import email
import asyncio
import imaplib as ilib
from pytz import timezone
from pprint import pprint # optional 
from bs4 import BeautifulSoup
from datetime import datetime
from email.header import decode_header
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

utc = timezone('UTC')

def check_mailbox(host, user, password):
	imap_client = ilib.IMAP4_SSL(host=host)

	imap_client.login(user, password)
	imap_client.select('inbox')
	_, messages = imap_client.uid('search', 'UNSEEN', 'ALL', 'FROM "anketa@sut.ru"')

	info = {}
	
	for msg in messages[0].split()[::-1]:
		_, data = imap_client.uid('fetch', msg, '(RFC822)')
		
		converted_msg = email.message_from_bytes(data[0][1])
		msg_date = email.utils.parsedate_to_datetime(converted_msg.get('Date')).astimezone(utc)
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
		msg_sender = msg_content[end_content + len('Отправитель') : msg_content.find('Отвечать необходимо в личном кабинете,')].strip()

		info.update({
			msg_id : {
				'header' : msg_header,
				'content' : msg_content[start_content : end_content],
				'sender' : msg_sender,
				'file' : file_in_msg,
				'type' : 1 if msg_header == 'Загружены файлы в личном кабинете' else 0, # 1 - Файлы группы / 0 - Сообщения
				'date': msg_date,
			}
		})
		
	imap_client.logout()

	pprint(info)


async def get_mail():
	loop = asyncio.get_event_loop()
	await loop.run_in_executor(None, check_mailbox, 'imap.yandex.ru', os.environ['EMAIL'], os.environ['PASS_MAIL'])
	#await check_mailbox('imap.yandex.ru', os.environ['EMAIL'], os.environ['PASS_MAIL'])

if __name__ == '__main__':
	#print(find_dotenv())
	asyncio.run(get_mail())
