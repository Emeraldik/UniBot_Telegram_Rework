import sqlite3
from pprint import pprint # optional 

class SQLObj():
	def __init__(self, db_file):
		self.connection = sqlite3.connect(db_file)
		self.cursor = self.connection.cursor()

	def table_exists(self, user_id):
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
				get_shedule BOOLEAN,
				auto_click_button BOOLEAN
			);''')

	def close(self):
		self.connection.close()

	def record_exists(self, _id, table, *, message_id = None, specific=False):
		self.table_exists(_id)
		
		with self.connection:
			if specific:
				result = self.cursor.execute(f'SELECT * FROM `{table}` WHERE `_id` = ? AND `message_id` = ?', (_id, message_id)).fetchall()
			else:
				result = self.cursor.execute(f'SELECT * FROM `{table}` WHERE `_id` = ?', (_id,)).fetchall()
			return bool(len(result))

	def get_cookies(self, _id):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'cookies'):
				result = self.cursor.execute('SELECT `__ddg1_`, `cookie`, `miden`, `uid` FROM `cookies` WHERE `_id` = ?', (_id,)).fetchone()
				return {k : v for k, v in zip(('__ddg1_', 'cookie', 'miden', 'uid'), result)}
			else:
				return {}

	def update_cookies(self, _id, ddg1_=None, cookie=None, miden=None, uid=None):
		self.table_exists(_id)
		
		cookies = (ddg1_, cookie, miden, uid)
		if not all(cookies):
			cookies = tuple([i if i==j else j if j else i for i, j in zip(cookies, self.get_cookies(_id).values())])

		with self.connection:
			self.cursor.execute('INSERT OR REPLACE INTO `cookies` (`_id`, `__ddg1_`, `cookie`, `miden`, `uid`) VALUES (?, ?, ?, ?, ?)', (_id,) + cookies)
	
	def delete_cookies(self, _id):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'cookies'):
				self.cursor.execute('DELETE FROM `cookies` WHERE `_id` = ?', (_id,))
	
	def get_messages(self, _id):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'messages'):
				result = self.cursor.execute(f'SELECT * FROM `messages` WHERE `_id` = ?', (_id,)).fetchall()
				return tuple([{k : v for k, v in zip(('_id', 'message_id', 'm_date', 'm_text', 'm_sender', 'm_file', 'm_type'), res)} for res in result])
			else:
				return ()

	def delete_message(self, _id, message_id):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'messages', message_id=message_id, specific=True):
				self.cursor.execute('DELETE FROM `messages` WHERE `_id` = ? AND `message_id` = ?', (_id, message_id))

	def delete_message_by_user(self, _id):
		self.table_exists(_id)

		with self.connection:
			if self.record_exists(_id, 'messages'):
				self.cursor.execute('DELETE FROM `messages` WHERE `_id` = ?', (_id,))

	# def get_all_users(self, status = True):
	# 	with self.connection:
	# 		return self.cursor.execute("SELECT * FROM `users` WHERE `status` = ?", (status,)).fetchall()

	# def get_user(self, user_id):
	# 	with self.connection:
	# 		return self.cursor.execute('SELECT * FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()

	# def user_exists(self, user_id):
	# 	with self.connection:
	# 		result = self.cursor.execute('SELECT * FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()
	# 		return bool(len(result))

	# def get_user_status(self, user_id):
	# 	with self.connection:
	# 		result = self.cursor.execute('SELECT `status` FROM `users` WHERE `user_id` = ?', (user_id,)).fetchall()
	# 		return bool(result[0][0])

	# def add_user(self, user_id, status = True):
	# 	with self.connection:
	# 		if not self.user_exists(user_id):
	# 			return self.cursor.execute('INSERT INTO `users` (`user_id`, `status`) VALUES (?, ?)', (user_id, status))
	# 		else:
	# 			self.update_user(user_id)

	# def update_user(self, user_id, status = True):
	# 	with self.connection:
	# 		if self.user_exists(user_id):
	# 			return self.cursor.execute('UPDATE `users` SET `status` = ? WHERE `user_id` = ?', (status, user_id))
	# 		else:
	# 			self.add_user(user_id, status)


if __name__ == '__main__':
	db = SQLObj('../database/uni.db')

	# db.update_cookies(_id=123, ddg1_=2, cookie=4, miden=5, uid=6)
	# print(db.get_cookies(123))
	# db.update_cookies(_id=123,  cookie=4, miden=5, uid=6)
	# print(db.get_cookies(123))
	# db.delete_cookies(123)
	# print(db.get_cookies(123))
	pprint(db.get_messages(123))
	db.delete_message_by_user(123)
	pprint(db.get_messages(123))

