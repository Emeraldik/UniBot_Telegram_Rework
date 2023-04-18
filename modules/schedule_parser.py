import asyncio, aiohttp
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

from datetime import datetime as dt
from dateutil.tz import gettz
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())

async def getDate(zone = 'UTC'):
	start_date = dt.strptime(os.environ['START_DATE'], '%d-%m-%Y')
	today_date = dt.strptime(dt.now(gettz(zone)).strftime('%Y-%m-%d'), '%Y-%m-%d')
	timedelta = today_date - start_date
	return {'week' : timedelta.days // 7 + 1, 'day': timedelta.days % 7 + 1}

async def get_schedule(autoweekday = False, day = 1, week = 1):
	url = 'https://cabinet.sut.ru/raspisanie_all_new'
	
	headers = {
		'User-Agent': UserAgent().chrome
	}

	payload = {
		'schet': '205.2223/2',
		'type_z': 1,
		'faculty': 50029,
		'group': 54865,
	}

	weekday = await getDate(zone='Europe/Moscow') if autoweekday else {'week' : week, 'day' : day}

	async with aiohttp.ClientSession() as session:
		async with session.get(url, headers=headers, params = payload) as response:
			soup = BeautifulSoup(await response.text(), 'lxml')
			pairs = {}
			for pair in soup.find_all(weekday = str(weekday.get('day'))):
				week_list = [int(i) for i in pair.find('span', class_= 'weeks').text.strip('*()н').replace(',', '').split()]
				if weekday.get('week') in week_list:
					pair_name = pair.find('strong').text
					pairs.update({int(pair.get('pair')) - 1 : (pair_name, week_list)})

		return pairs

if __name__ == '__main__':
	print(asyncio.run(get_schedule(autoweekday=True)))