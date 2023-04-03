import asyncio, aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import os, json, re
from exceptions import RequestException
from logger import logger
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
			
			logger.info('[!] <Got new cookies>')
			cookies = session.cookie_jar.filter_cookies('https://lk.sut.ru')
			return {cookie.key : cookie.value for key, cookie in cookies.items()}

async def async_button_interaction(cookies={}):
	async with aiohttp.ClientSession(trust_env=True, cookie_jar=aiohttp.CookieJar()) as session:
		async with session.post('https://lk.sut.ru/cabinet/lib/autentificationok.php', cookies=cookies, headers=headers, data=data) as response:
			if response.status != 200:
				raise RequestException('bad cookies')
		
		response_auth = await session.get('https://lk.sut.ru', headers=headers, cookies=cookies)

		async with session.get('https://lk.sut.ru/cabinet/project/cabinet/forms/raspisanie.php', cookies=cookies, headers=headers) as response:
			soup = BeautifulSoup(await response.text(), 'lxml')
			raw_buttons = soup.find_all('a', attrs={'onclick' : re.compile("^open_zan")})
			buttons = [tuple(bt.get('onclick').strip('open_zan();').split(',')) for bt in raw_buttons if len(tuple(bt.get('onclick').strip('open_zan();').split(','))) == 2]

		for tupl in buttons:
			await session.post('https://lk.sut.ru/cabinet/project/cabinet/forms/raspisanie.php', headers=headers, cookies=cookies, data={
				'open': 1,
				'rasp': tupl[0],
				'week': tupl[1]
			})
			logger.info(f'[+] <{tupl} was pressed>')

async def main():
	_id = 123
	cookies = db.get_cookies(_id)

	try:
		await async_button_interaction(cookies)
	except RequestException as e:
		logger.error(e)
	except aiohttp.client_exceptions.TooManyRedirects as e:
		logger.warning('[!] <Request was excepted (bad cookies)>')

		cookies = await async_get_cookies()
		db.update_cookies(_id, *tuple(cookies.values()))

		await async_button_interaction(cookies)

if __name__ == '__main__':
	asyncio.run(main())