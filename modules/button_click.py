import asyncio, aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

import os, json, re
from exceptions import RequestException, RequestExceptionCritical, WebDriverException
from logger import logger
from dotenv import find_dotenv, load_dotenv
from sqlite import SQLObj
import browser_selenium as b_s

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

async def async_button_interaction(cookies={}):
	async with aiohttp.ClientSession(trust_env=True) as session:
		async with session.post('https://lk.sut.ru/cabinet/lib/autentificationok.php', cookies=cookies, headers=headers, data=data) as response:
			if response.status != 200:
				raise RequestException('bad cookies')
		
		response_auth = await session.get('https://lk.sut.ru', headers=headers, cookies=cookies)

		async with session.get('https://lk.sut.ru/cabinet/project/cabinet/forms/raspisanie.php', cookies=cookies, headers=headers) as response:
			soup = BeautifulSoup(await response.text(), 'lxml')
			raw_buttons = soup.find_all('a', attrs={'onclick' : re.compile("^open_zan")})
			buttons = [tuple(bt.get('onclick').strip('open_zan();').split(',')) for bt in raw_buttons if len(tuple(bt.get('onclick').strip('open_zan();').split(','))) == 2]

		# if not buttons:
		# 	logger.info(f'[-] <Zero button was founded>')

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
	print(cookies)

	all_data = []
	try:
		await async_button_interaction(cookies=cookies)
	except (aiohttp.client_exceptions.TooManyRedirects, RequestException):
		logger.warning('[!] <Request was excepted (bad cookies)>')

		try:
			new_cookies = await async_get_cookies()

			db.update_cookies(_id, *tuple(new_cookies.values()))
			cookies.update(new_cookies)
			print(cookies)

			await async_button_interaction(cookies=cookies)
		except (aiohttp.client_exceptions.TooManyRedirects, RequestExceptionCritical, RequestException) as e_f:
			logger.error(f'[!] <First(requests) try> : {e_f}')
			try:
				new_cookies = await b_s.async_get_cookies()
				
				db.update_cookies(_id, *tuple(new_cookies.values()))
				cookies.update(new_cookies)
				print(cookies)

				await async_button_interaction(cookies=cookies)
			except (aiohttp.client_exceptions.TooManyRedirects, RequestExceptionCritical, RequestException) as e_s:
				logger.error(f'[!] <Second(webdriver) try> : {e_s}')

				try:
					result = await b_s.async_button_interaction()
				except WebDriverException as e_w:
					logger.error(f'[!] <Third(last)(webdriver) try> : {e_w}')
				else:
					if result:
						logger.debug(f'[+] <Third(last)(webdriver) try> : Button was clicked!')
					else:
						logger.debug(f'[-] <Third(last)(webdriver) try> : Button wasn\'t clicked')
if __name__ == '__main__':
	asyncio.run(main())