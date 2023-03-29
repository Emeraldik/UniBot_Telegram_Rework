import sqlite3

class SQLObj():
	def __init__(self, db_file):
		self.connection = sqlite3.connect(db_file)
		self.cursor = self.connection.cursor()

	def table_exists(self, user_id):
		with self.connection:
			self.cursor.execute(f'''Create TABLE if not exists messages_{user_id} (
				message_id INT,
				m_date TEXT,
				m_text TEXT,
				m_file BOOLEAN,
				m_type INT
			);''')

	def close(self):
		self.connection.close()

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
