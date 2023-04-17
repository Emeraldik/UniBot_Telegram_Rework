import os
import asyncio
from pytz import timezone
from dotenv import load_dotenv, find_dotenv

import imaplib as ilib

import smtplib as slib
import ssl

import email
from email.header import decode_header

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urlextract import URLExtract

from modules.sqlite import SQLObj

#15 minutes limit
load_dotenv(find_dotenv())

tz_info = timezone('Europe/Moscow')

extractor = URLExtract()
db = SQLObj('database/uni.db')

def check_status(url: str) -> bool:
	headers = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
		'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
		'Cache-Control': 'no-cache',
		'Connection': 'keep-alive',
		'Pragma': 'no-cache',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': UserAgent().chrome
	}

	try:
		response = requests.get(f'http://{url}', headers=headers, verify=False)
	except:
		return 403
	return response.status_code

def check_mailbox(host, user, password):
	with ilib.IMAP4_SSL(host=host) as imap_client:
		try:
			imap_client.login(user, password)
		except:
			logger.debug('[-] <Email Error> Email connection error')
			return

		imap_client.select('HDREZKA')

		_, messages = imap_client.uid('search', 'UNSEEN')

		for msg in messages[0].split()[::-1]:
			_, data = imap_client.uid('fetch', msg, '(RFC822)')
			
			converted_msg = email.message_from_bytes(data[0][1])
			raw_msg_content = converted_msg.get_payload()
			
			if converted_msg.is_multipart():
				raw_msg_content = ''.join([part.get_payload() for part in raw_msg_content if part.get_content_type() == 'text/plain'])

			soup = BeautifulSoup(raw_msg_content, 'lxml')
			msg_content = soup.get_text()
			
			url = tuple(filter(lambda item: 'hdrezka' in item, extractor.find_urls(msg_content)))[0]
			if url and check_status(url) == 200:
				return url

def send_message(host, user, password):
	with slib.SMTP(host=host, port=587) as slib_client:
		slib_client.ehlo()
		slib_client.starttls()
		try:
			slib_client.login(user, password)
			slib_client.sendmail(user, 'mirror@hdrezka.org', '')

			return True
		except Exception as e:
			print(e)
			return

async def async_get_new_hdrezka():
	loop = asyncio.get_event_loop()
	status = await asyncio.wrap_future(loop.run_in_executor(None, send_message, 'smtp.yandex.ru', os.environ['EMAIL'], os.environ['PASS_MAIL']))
	if not status:
		return

	await asyncio.sleep(10)

	link = await asyncio.wrap_future(loop.run_in_executor(None, check_mailbox, 'imap.yandex.ru', os.environ['EMAIL'], os.environ['PASS_MAIL']))

	if link:
		db.set_links(link, l_type='hdrezka')

if __name__ == '__main__':
	from time import perf_counter
	start = perf_counter()
	asyncio.run(async_get_new_hdrezka())	
	end = perf_counter() - start
	print(f'{end:.3f}s')