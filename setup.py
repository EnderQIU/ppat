from setuptools import setup

setup(name='ppat',
      version='1.0',
      description='Places & People Automate Transliterator',
      keywords = 'transliterate language chinese',
      author='EnderQIU',
      author_email='a934560824@gmail.com',
      license = 'GPLv3',
      url='https://github.com/EnderQIU/ppat',
      packages=['ppat', ],
      entry_points={
          'console_scripts': [
              'ppat = ppat.ppat:main',
          ],
      },
      )
