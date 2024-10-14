import asyncio, aiohttp, aiofiles
#import aiofiles.os

async def get_file(url, session, limit, filenames: list=[]):
	file_name_with_ext = url.split('/')[-1]
	async with limit:
		async with session.get(url) as response:
			if response.status != 200:
				return
			content = await response.read()

	async with aiofiles.open(file_name_with_ext ,'wb') as file:
		await file.write(content)
		filenames.append(file_name_with_ext)

async def start_download(links: list[str]=[]):
	filenames = []
	limit = asyncio.Semaphore(10)
	async with aiohttp.ClientSession(trust_env=True) as session:
		tasks = []
		for url in links:
			task = asyncio.create_task(get_file(url, session, limit, filenames))
			tasks.append(task)

		await asyncio.gather(*tasks)

	return filenames

if __name__ == '__main__':
	
	links = input('Input links : ').split()
	print(links)
	print(asyncio.run(start_download(links)))
	#input()