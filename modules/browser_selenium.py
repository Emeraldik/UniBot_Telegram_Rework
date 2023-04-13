import asyncio
#import arsenic
from arsenic import start_session, stop_session
from arsenic import browsers
from arsenic import services
from webdriver_manager.chrome import ChromeDriverManager

#from bs4 import BeautifulSoup
#from email_parser import get_mail
#from fake_useragent import UserAgent

#from modules.logger import logger
import logging
import structlog

import os
from modules.exceptions import WebDriverException
from time import perf_counter
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

DRIVER = ChromeDriverManager().install()

#Reconfigure logs
def set_arsenic_log_level(level = logging.WARNING):
    logger = logging.getLogger('arsenic')

    def logger_factory():
        return logger

    structlog.configure(logger_factory=logger_factory)
    logger.setLevel(level)

async def async_browser_start():
	set_arsenic_log_level(level = logging.ERROR)
	service = services.Chromedriver(
		binary=DRIVER
	)
	browser = browsers.Chrome()
	browser.capabilities = {#'--headless',
		'goog:chromeOptions': {'args': ['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']}
	}
	session = await start_session(service, browser)

	# first block
	try:
		await session.get('https://lk.sut.ru')
		
		email = await session.wait_for_element(5, '#users')
		await email.send_keys(os.environ['EMAIL'])
		
		password = await session.wait_for_element(5, '#parole')
		await password.send_keys(os.environ['PASS_LK'])
		
		login = await session.wait_for_element(5, '#logButton')
		await login.click()
		
	except Exception as e:
		await stop_session(session)

		raise WebDriverException(e)
	else:
		return session

async def async_get_cookies():
	set_arsenic_log_level(level = logging.DEBUG)
	session = await async_browser_start()
	try:
		cookies = await session.get_all_cookies()
	except Exception as e:
		raise WebDriverException(e)
	else:
		return dict(reversed({i.get('name') : i.get('value') for i in cookies}.items()))
	finally:
		await stop_session(session)

async def async_button_interaction():
	set_arsenic_log_level(level = logging.DEBUG)
	session = await async_browser_start()
	# first block
	try:
		heading = await session.wait_for_element(5, '#heading1')
		
		first_block = await heading.get_element('.title_item')
		await first_block.click()
		
		collapse = await session.wait_for_element(5, '#collapse1')

		second_block = await collapse.get_element('#menu_li_6118')
		await second_block.click()

		third_block = await session.wait_for_element(5, '.simple-little-table')

		button_block = await third_block.get_elements('span')
		clicked=False
		for element in button_block:
			attr = await element.get_attribute('on_click')
			if attr.startswith('open_zan'):
				try:
					await element.click()
				except:
					pass
				else:
					clicked=True

	except Exception as e:
		raise WebDriverException(e)
	finally:
		await stop_session(session)
		return clicked

async def example():
	set_arsenic_log_level(level = logging.DEBUG)
	#print(await async_get_cookies())
	#await async_button_interaction()
	#await async_get_files()
	#print(await async_get_cookies())

async def main():
	await example()
	
if __name__ == '__main__':
	start = perf_counter()
	asyncio.run(main())
	print(f'{(perf_counter()-start):.4f}s')