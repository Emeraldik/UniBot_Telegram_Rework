from modules.sqlite import SQLObj
from modules.files_parser import start_parse as fm_start_parse
from modules.email_parser import get_mail as e_start_parse
#from pprint import pprint # optional
from datetime import datetime, timedelta

import asyncio

db = SQLObj('database/uni.db')

async def start_parse(_id):
	await e_start_parse(_id)
	messages = db.get_messages(_id=_id)
	messages_with_files = list(filter(lambda item: item.get('m_file'), messages))
	messages_without_files = list(filter(lambda item: not item.get('m_file'), messages))

	if messages_with_files:
		await fm_start_parse(_id, n=len(messages)//27 + 1)
		files = list(sorted(db.get_files(_id), key=lambda item: item.get('m_date'), reverse=True))

	dates = ()
	result = messages_without_files

	for message in messages_with_files:
		m_date = datetime.strptime(message.get('m_date'), '%Y-%m-%d %H:%M:%S')
		m_sender = message.get('m_sender')
		m_text = message.get('m_text')
		check_one = tuple(filter(lambda item: abs(datetime.strptime(item.get('m_date'), '%Y-%m-%d %H:%M:%S') - m_date) < timedelta(minutes=10), files))
		check_two = tuple(filter(lambda item: item.get('m_sender') == m_sender, check_one))
		check_three = tuple(filter(lambda item: item.get('m_text') == m_text, check_two))
		
		if not [item.get('m_date') for item in check_three if not item.get('m_date') in dates]:
			continue
		
		dates += tuple([item.get('m_date') for item in check_three if not item.get('m_date') in dates])
		
		check_three[0].update({'message_id' : message.get('message_id')})
		result.append(check_three[0])
	
	# for message in messages_with_files:
	# 	result.append(message)

	#pprint(data)
	return result
	#db.delete_message_by_user(123)
	#db.delete_file_by_user(123)

	#result = [for k, v in zip(files, messages)]
	# await e_start_parse(_id=123)
	# pprint(data)

if __name__ == '__main__':
	asyncio.run(start_parse(_id=123))