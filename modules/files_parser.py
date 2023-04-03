import asyncio, aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
#import browser_selenium as b_s

import os, json
from time import perf_counter
from logger import logger
from exceptions import RequestException
from dotenv import find_dotenv, load_dotenv
from sqlite import SQLObj

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
				raise RequestException(f'lk.sut.ru got error code : {response.status}')
			else:
				logger.info('[!] <Got new cookies>')
				cookies = session.cookie_jar.filter_cookies('https://lk.sut.ru')
				return {cookie.key : cookie.value for key, cookie in cookies.items()}

async def get_messages(session, page_num=0, all_data=[], cookies={}):
	url = f'https://lk.sut.ru/cabinet/project/cabinet/forms/message.php?page={page_num}'

	async with session.get(url=url, headers = headers, cookies=cookies) as response:

		content = await response.text()
		soup = BeautifulSoup(content, 'lxml')
		new_data = [i.get('href') for i in soup.find_all('a', href=True)]
		if not new_data:
			return

		all_data += new_data

		print(f'[+][messages] {page_num} async page is ready! Founded {len(new_data)} links')

async def get_files(session, page_num=0, all_data=[], cookies={}):
	url = f'https://lk.sut.ru/cabinet/project/cabinet/forms/files_group_pr.php?page={page_num}'

	async with session.get(url=url, headers = headers, cookies=cookies) as response:
		content = await response.text()
		soup = BeautifulSoup(content, 'lxml')
		new_data = [i.get('href') for i in soup.find_all('a', href=True)]
		if not new_data:
			return

		all_data += new_data

		print(f'[+][files] {page_num} async page is ready! Founded {len(new_data)} links')

async def start_parse(all_data, *, n=1, files=False, messages=False, cookies={}):
	async with aiohttp.ClientSession(trust_env=True) as session:
		async with session.post('https://lk.sut.ru/cabinet/lib/autentificationok.php', cookies=cookies, headers=headers, data=data) as response:
			if response.status != 200:
				raise RequestException('bad cookies')
		
		response_auth = await session.get('https://lk.sut.ru', headers=headers, cookies=cookies)

		tasks = []
		for i in range(1, 1+n): # 2 pages
			message_task = asyncio.create_task(get_messages(session, i, all_data, cookies)) if messages else None
			file_task = asyncio.create_task(get_files(session, i, all_data, cookies)) if files else None
			
			tasks += [message_task, file_task]

		await asyncio.gather(*tasks)


async def main():
	_id = 123
	cookies = db.get_cookies(_id)

	all_data = []
	n = 2
	try:
		await start_parse(all_data, n=n, messages=True, files=True, cookies=cookies)
	except RequestException as e:
		logger.error(e)
	except aiohttp.client_exceptions.TooManyRedirects as e:
		logger.warning('[!] <Request was excepted (bad cookies)>')
		cookies = await async_get_cookies()
		db.update_cookies(_id, *tuple(cookies.values()))

		await start_parse(all_data, n=n, messages=True, files=True, cookies=cookies)
	
	print(len(all_data))

if __name__ == '__main__':
	start = perf_counter()
	asyncio.run(main())
	print(f'{(perf_counter() - start):.4f}s')