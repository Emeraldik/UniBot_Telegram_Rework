class RequestException(Exception):
	"""Класс исключения при незарегистрированных cookies"""
	def __init__(self, *args):
		self.message = args[0] if args else None

	def __str__(self):
		return f'[!] <Request was excepted ({self.message})>'

class WebDriverException(Exception):
	"""Класс исключения при ошибках webdriver"""
	def __init__(self, *args):
		self.message = args[0] if args else None

	def __str__(self):
		return f'[!] <WebDriver was excepted ({self.message})>'
