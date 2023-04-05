import os, json, re
from pprint import pprint # optional
from datetime import datetime
from time import perf_counter # optional
from dotenv import find_dotenv, load_dotenv

import asyncio, aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from logger import logger
from sqlite import SQLObj
import browser_selenium as b_s
from exceptions import RequestException, RequestExceptionCritical

load_dotenv(find_dotenv())

db = SQLObj('../database/uni.db')

headers = {
	'authority': 'lk.sut.ru',
	'accept': 'text/plain, */*; q=0.01',
	'accept-language': 'ru,en-US;q=0.9,en;q=0.8,ru-RU;q=0.7',
	'cache-control': 'no-cache',
	'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
	'origin': 'https://lk.sut.ru',
	'pragma': 'no-cache',
	'referer': 'https://lk.sut.ru/cabinet/?login=no',
	'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "Google Chrome";v="110"',
	'sec-ch-ua-mobile': '?0',
	'sec-ch-ua-platform': '"Windows"',
	'sec-fetch-dest': 'empty',
	'sec-fetch-mode': 'cors',
	'sec-fetch-site': 'same-origin',
	'sec-gpc': '1',
	'user-agent': UserAgent().chrome,
	'x-requested-with': 'XMLHttpRequest'
}

data = {
	'users': os.environ['EMAIL'],
	'parole': os.environ['PASS_LK']
}

async def async_get_cookies():
	async with aiohttp.ClientSession(trust_env=True, cookie_jar=aiohttp.CookieJar()) as session:
		async with session.get('https://lk.sut.ru', headers=headers) as response:
			if response.status != 200:  
				raise RequestExceptionCritical(f'lk.sut.ru got error code : {response.status}')
			else:
				logger.info('[!] <Got new cookies>')
				cookies = session.cookie_jar.filter_cookies('https://lk.sut.ru')
				return {cookie.key : cookie.value for key, cookie in cookies.items()}

async def get_messages(_id, session, page_num=0, all_data=[], cookies={}):
	url = f'https://lk.sut.ru/cabinet/project/cabinet/forms/message.php?page={page_num}'

	async with session.get(url=url, headers = headers, cookies=cookies) as response:

		content = await response.text()
		soup = BeautifulSoup(content, 'lxml')
		new_data = []
		for message in soup.find_all('tr', id=re.compile('^tr')):
			links = [link.get('href') for link in message.find_all(href=True)]
			if not links:
				continue
			
			file_id = message.get('id').strip('tr_')
			
			raw_data = [i.strip() for i in message.text.split('\n') if i]
			m_date = datetime.strptime(raw_data[0], '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
			m_text = raw_data[1]
			m_sender = raw_data[-1].replace('(сотрудник/преподаватель)', '').strip()
			num_of_links = len(links)
			db.add_file(
				_id = _id, 
				file_id = file_id, 
				m_date = m_date, 
				m_sender = m_sender, 
				m_type = 0, 
				m_text = m_text, 
				links = links
			)

		#print(f'[+][messages] {page_num} async page is ready! Founded {len(new_data)} links')

async def get_files(_id, session, page_num=0, all_data=[], cookies={}):
	url = f'https://lk.sut.ru/cabinet/project/cabinet/forms/files_group_pr.php?page={page_num}'

	async with session.get(url=url, headers = headers, cookies=cookies) as response:
		content = await response.text()
		soup = BeautifulSoup(content, 'lxml')
		new_data = []
		for message in soup.find_all('tr', id=re.compile('^tr')):
			links = [link.get('href') for link in message.find_all(href=True)]
			if not links:
				continue
			
			file_id = message.get('id').strip('tr_')
			
			raw_data = message.text.strip().split('\n')
			m_sender = raw_data[1]
			m_date = datetime.strptime(raw_data[2], '%d-%m-%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
			m_text = raw_data[4].strip('-')
			num_of_links = len(links)

			db.add_file(
				_id = _id, 
				file_id = file_id, 
				m_date = m_date, 
				m_sender = m_sender, 
				m_type = 1, 
				m_text = m_text, 
				links = links
			)

		#print(f'[+][files] {page_num} async page is ready! Founded {len(new_data)} links')

async def task_creator(_id, all_data, *, n=1, files=False, messages=False, cookies={}):
	async with aiohttp.ClientSession(trust_env=True) as session:
		async with session.post('https://lk.sut.ru/cabinet/lib/autentificationok.php', cookies=cookies, headers=headers, data=data) as response:
			if response.status != 200:
				raise RequestException(f'bad cookies')
		
		response_auth = await session.get('https://lk.sut.ru', headers=headers, cookies=cookies)

		tasks = []
		for i in range(1, 1+n): # 2 pages
			message_task = asyncio.create_task(get_messages(_id, session, i, all_data, cookies)) if messages else None
			file_task = asyncio.create_task(get_files(_id, session, i, all_data, cookies)) if files else None
			
			tasks += [message_task, file_task]

		await asyncio.gather(*tasks)


async def start_parse(_id: int , *, n: int = 1, messages :bool=True, files: bool=True):
	_id = _id
	n = n
	messages = messages
	files = files
	
	cookies = db.get_cookies(_id)

	all_data = []
	try:
		await task_creator(_id, all_data, n=n, messages=messages, files=files, cookies=cookies)
	except (aiohttp.client_exceptions.TooManyRedirects, RequestException):
		logger.warning('[!] <Request was excepted (bad cookies)>')

		try:
			new_cookies = (await async_get_cookies())
			
			db.update_cookies(_id, *tuple(new_cookies.values()))
			cookies.update(new_cookies)

			await task_creator(_id, all_data, n=n, messages=messages, files=files, cookies=cookies)
		except (aiohttp.client_exceptions.TooManyRedirects, RequestExceptionCritical, RequestException) as e_f:
			logger.error(f'First(requests) try : {e_f}')
			try:
				new_cookies = await b_s.async_get_cookies()
				db.update_cookies(_id, *tuple(new_cookies.values()))
				cookies.update(new_cookies)

				await task_creator(_id, all_data, n=n, messages=messages, files=files, cookies=cookies)
			except (aiohttp.client_exceptions.TooManyRedirects, RequestExceptionCritical, RequestException) as e_s:
				logger.error(f'Second(webdriver) try : {e_s}')
	
	#return all_data

if __name__ == '__main__':
	start = perf_counter()
	asyncio.run(start_parse(_id=123))
	print(f'{(perf_counter() - start):.4f}s')