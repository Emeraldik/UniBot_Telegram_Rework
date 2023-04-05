from sqlite import SQLObj
from files_parser import start_parse as fm_start_parse
from email_parser import get_mail as e_start_parse
from pprint import pprint # optional
from datetime import datetime
from datetime import timedelta

import asyncio

db = SQLObj('../database/uni.db')

async def main():
	await fm_start_parse(123)
	await e_start_parse(123)

	files = list(sorted(db.get_files(123), key=lambda item: item.get('m_date'), reverse=True))
	messages = list(filter(lambda item: item.get('m_file'), db.get_messages(_id=123)))
	
	dates = ()
	data = ()

	for message in messages:
		m_date = datetime.strptime(message.get('m_date'), '%Y-%m-%d %H:%M:%S')
		m_sender = message.get('m_sender')
		m_text = message.get('m_text')
		check_one = tuple(filter(lambda item: abs(datetime.strptime(item.get('m_date'), '%Y-%m-%d %H:%M:%S') - m_date) < timedelta(minutes=10), files))
		check_two = tuple(filter(lambda item: item.get('m_sender') == m_sender, check_one))
		check_three = tuple(filter(lambda item: item.get('m_text') == m_text, check_two))
		
		if not [item.get('m_date') for item in check_three if not item.get('m_date') in dates]:
			continue
		
		dates += tuple([item.get('m_date') for item in check_three if not item.get('m_date') in dates])
		data += (check_three, message)
	
	pprint(data)
	#print(dates)
	db.delete_message_by_user(123)
	db.delete_file_by_user(123)

	#result = [for k, v in zip(files, messages)]
	# await e_start_parse(_id=123)
	# pprint(data)

if __name__ == '__main__':
	asyncio.run(main())