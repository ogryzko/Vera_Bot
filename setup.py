try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Simple chat-bot for vk social net',
    'author': 'genro',
    'url': 'URL to get it at',
    'download_url': 'Where to download it',
    'author_email': 'genroe@gmail.com',
    'version': '0.1',
    'install_requires': ['nose', 'vk', 'chatterbotapi'],
    'packages': ['NAME'],
    'scripts': [],
    'name': 'VeraBot'
}

