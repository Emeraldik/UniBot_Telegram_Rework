import asyncio
import arsenic
from arsenic import get_session
from arsenic import browsers
from arsenic import services
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
#from email_parser import get_mail
#from fake_useragent import UserAgent

from logger import logger
import logging
import structlog

from time import perf_counter

DRIVER = ChromeDriverManager().install()

#Reconfigure logs
def set_arsenic_log_level(level = logging.WARNING):
    logger = logging.getLogger('arsenic')

    def logger_factory():
        return logger

    structlog.configure(logger_factory=logger_factory)
    logger.setLevel(level)

async def async_get_text(link : str, *, limit: asyncio.Semaphore = asyncio.Semaphore(5)):
	service = services.Chromedriver(
		binary=DRIVER
	)
	browser = browsers.Chrome()
	browser.capabilities = {#'--headless',
		'goog:chromeOptions': {'args': ['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']}
	}
	async with limit:
		async with get_session(service, browser) as session:
			await session.get(link)

			try: # WORKS
				email = await session.wait_for_element(5, '#users')
				email_send = await email.send_keys(os.environ['EMAIL'])
				password = await session.wait_for_element(5, '#parole')
				password_send = await password.send_keys(os.environ['PASS_LK'])
				login = await session.wait_for_element(5, '#logButton')
				login_send = await login.click()
				await asyncio.sleep(10)
			except Exception as e:
				print(e)

			logger.info(f'[+] {link} card async')


async def example():
	set_arsenic_log_level(level = logging.DEBUG)
	links = ['https://lk.sut.ru/cabinet' for _ in range(1)]
	limit = asyncio.Semaphore(6)

	for link in links:
		await async_get_text(link=link, limit=limit)
		#await get_mail()

async def main():
	await example()
	
if __name__ == '__main__':
	start = perf_counter()
	asyncio.run(main())
	print(f'{(perf_counter()-start):.4f}s')