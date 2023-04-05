import sqlite3
from pprint import pprint # optional 

class SQLObj():
	def __init__(self, db_file: str):
		self.connection = sqlite3.connect(db_file, check_same_thread=False)
		self.cursor = self.connection.cursor()

	def table_exists(self, user_id: int):
		with self.connection:
			self.cursor.execute(f'''Create TABLE if not exists messages (
				_id INT,
				message_id INT UNIQUE,
				m_date TEXT,
				m_text TEXT,
				m_sender TEXT,
				m_file BOOLEAN,
				m_type INT
			);''')

			self.cursor.execute(f'''Create TABLE if not exists files (
				_id INT,
				file_id INT UNIQUE,
				m_date TEXT,
				m_text TEXT,
				m_sender TEXT,
				m_type INT,
				links TEXT
			);''')

			self.cursor.execute(f'''Create TABLE if not exists cookies (
				_id INT UNIQUE,
				__ddg1_ TEXT,
				cookie TEXT,
				miden TEXT,
				uid TEXT
			);''')

			self.cursor.execute(f'''Create TABLE if not exists settings (
				_id INT UNIQUE,
				get_mail BOOLEAN,
				get_files BOOLEAN,
				get_schedule BOOLEAN,
				auto_click_button BOOLEAN
			);''')

	def close(self):
		self.connection.close()

	def record_exists(self, _id: int, table: str, *, message_id: int=None, specific: bool=False):
		self.table_exists(_id)
		
		with self.connection:
			if specific:
				result = self.cursor.execute(f'SELECT * FROM `{table}` WHERE `_id` = ? AND `message_id` = ?', (_id, message_id)).fetchall()
			else:
				result = self.cursor.execute(f'SELECT * FROM `{table}` WHERE `_id` = ?', (_id,)).fetchall()
			return bool(len(result))

# Cookies TABLE interactions
	
	'''
		_id INT UNIQUE,
		__ddg1_ TEXT,
		cookie TEXT,
		miden TEXT,
		uid TEXT
	'''
	
	def get_cookies(self, _id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'cookies'):
				result = self.cursor.execute('SELECT `__ddg1_`, `cookie`, `miden`, `uid` FROM `cookies` WHERE `_id` = ?', (_id,)).fetchone()
				return {k : v for k, v in zip(('__ddg1_', 'cookie', 'miden', 'uid'), result)}
			else:
				return {}

	def update_cookies(self, _id: int, ddg1_: str=None, cookie: str=None, miden: str=None, uid: str=None):
		self.table_exists(_id)
		
		cookies = (ddg1_, cookie, miden, uid)
		if not all(cookies):
			cookies = tuple([i if i==j else j if j else i for i, j in zip(cookies, self.get_cookies(_id).values())])

		with self.connection:
			self.cursor.execute('INSERT OR REPLACE INTO `cookies` (`_id`, `__ddg1_`, `cookie`, `miden`, `uid`) VALUES (?, ?, ?, ?, ?)', (_id,) + cookies)
	
	def delete_cookies(self, _id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'cookies'):
				self.cursor.execute('DELETE FROM `cookies` WHERE `_id` = ?', (_id,))
	
# Messages TABLE interactions

	'''
		_id INT,
		message_id INT UNIQUE,
		m_date TEXT,
		m_text TEXT,
		m_sender TEXT,
		m_file BOOLEAN,
		m_type INT
	'''

	def get_messages(self, _id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'messages'):
				result = self.cursor.execute(f'SELECT * FROM `messages` WHERE `_id` = ?', (_id,)).fetchall()
				return tuple([{k : v for k, v in zip(('_id', 'message_id', 'm_date', 'm_text', 'm_sender', 'm_file', 'm_type'), res)} for res in result])
			else:
				return ()

	def add_message(self, _id: int, message_id: int, m_date: str, m_sender: str, m_type: int, *, m_text: str='', m_file: bool=False):
		self.table_exists(_id)

		with self.connection:
			self.cursor.execute('INSERT OR IGNORE INTO `messages` (`_id`, `message_id`, `m_date`, `m_text`, `m_sender`, `m_file`, `m_type`) VALUES (?, ?, ?, ?, ?, ?, ?)', (_id, message_id, m_date, m_text, m_sender, m_file, m_type))

	def delete_message(self, _id: int, message_id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'messages', message_id=message_id, specific=True):
				self.cursor.execute('DELETE FROM `messages` WHERE `_id` = ? AND `message_id` = ?', (_id, message_id))

	def delete_message_by_user(self, _id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'messages'):
				self.cursor.execute('DELETE FROM `messages` WHERE `_id` = ?', (_id,))

# Settings TABLE interactions

	'''
		_id INT UNIQUE,
		get_mail BOOLEAN,
		get_files BOOLEAN,
		get_shedule BOOLEAN,
		auto_click_button BOOLEAN
	'''

	def get_settings(self, _id: int, *, get_mail: bool=False, get_files: bool=False, get_schedule: bool=False, auto_click_button: bool=False):
		self.table_exists(_id)

		parameters = {
			'`get_mail`' : get_mail,
			'`get_files`' : get_files, 
			'`get_schedule`' : get_schedule,
			'`auto_click_button`' : auto_click_button
		}

		with self.connection:
			if any(parameters.values()):
				parameters = ','.join([k for k, v in parameters.items() if v])
				return self.cursor.execute(f'SELECT {parameters} FROM `settings` WHERE `_id` = ?', (_id,)).fetchall()
			else:
				return self.cursor.execute('SELECT * FROM `settings` WHERE `_id` = ?', (_id,)).fetchall()

	def set_settings(self, _id: int, *, get_mail: bool=None, get_files: bool=None, get_schedule: bool=None, auto_click_button: bool=None):
		self.table_exists(_id)

		get_mail = get_mail if not get_mail is None else bool(self.get_settings(_id, get_mail=True)[0][0])
		get_files = get_files if not get_files is None else bool(self.get_settings(_id, get_files=True)[0][0])
		get_schedule = get_schedule if not get_schedule is None else bool(self.get_settings(_id, get_schedule=True)[0][0])
		auto_click_button = auto_click_button if not auto_click_button is None else bool(self.get_settings(_id, auto_click_button=True)[0][0])

		with self.connection:
			self.cursor.execute('INSERT OR REPLACE INTO `settings` (`_id`, `get_mail`, `get_files`, `get_schedule`, `auto_click_button`) VALUES (?, ?, ?, ?, ?)', (_id, get_mail, get_files, get_schedule, auto_click_button))

# Files TABLE interactions

	'''
		_id INT,
		file_id INT UNIQUE,
		m_date TEXT,
		m_text TEXT,
		m_sender TEXT,
		m_file BOOLEAN,
		m_type INT
	'''

	def get_files(self, _id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'files'):
				result = self.cursor.execute(f'SELECT * FROM `files` WHERE `_id` = ?', (_id,)).fetchall()
				return tuple([{k : v.split() if k == 'links' else v for k, v in zip(('_id', 'file_id', 'm_date', 'm_text', 'm_sender', 'm_type', 'links'), res)} for res in result])
			else:
				return ()

	def add_file(self, _id: int, file_id: int, m_date: str, m_sender: str, m_type: int, *, m_text: str='', links :list[str]=[]):
		self.table_exists(_id)

		with self.connection:
			self.cursor.execute('INSERT OR IGNORE INTO `files` (`_id`, `file_id`, `m_date`, `m_text`, `m_sender`, `m_type`, `links`) VALUES (?, ?, ?, ?, ?, ?, ?)', (_id, file_id, m_date, m_text, m_sender, m_type, ' '.join(links)))

	def delete_file(self, _id: int, file_id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'files', file_id=file_id, specific=True):
				self.cursor.execute('DELETE FROM `files` WHERE `_id` = ? AND `file_id` = ?', (_id, file_id))

	def delete_file_by_user(self, _id: int):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'files'):
				self.cursor.execute('DELETE FROM `files` WHERE `_id` = ?', (_id,))

if __name__ == '__main__':
	db = SQLObj('../database/uni.db')

	# db.update_cookies(_id=123, ddg1_=2, cookie=4, miden=5, uid=6)
	# print(db.get_cookies(123))
	# db.update_cookies(_id=123,  cookie=4, miden=5, uid=6)
	# print(db.get_cookies(123))
	# db.delete_cookies(123)
	# print(db.get_cookies(123))
	#pprint(db.get_messages(123))
	# db.add_message(
	# 	_id = 123, 
	# 	message_id = 2525, 
	# 	m_date = '20.10.2023',
	# 	m_sender = 'Dagaev', 
	# 	m_type = 1, 
	# 	m_text = 'Hello World', 
	# 	m_file = True
	# )
	# db.add_message(
	# 	_id = 123, 
	# 	message_id = 2525, 
	# 	m_date = '20.10.2023',
	# 	m_sender = 'Dagaev', 
	# 	m_type = 1, 
	# 	m_text = 'Hello World', 
	# 	m_file = True
	# )
	#pprint(db.get_messages(123))
	# db.delete_message_by_user(123)
	# db.set_settings(
	# 	_id = 123, 
	# 	get_files = False,
	# )
	# print(db.get_settings(123))