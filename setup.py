import os
import subprocess
from setuptools import setup, find_packages
from setuptools.command.install import install

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUILD_SCRIPT = os.path.join(BASE_DIR, 'ppat', 'espeak', 'build.sh')


class BuildEspeakInstallCommand(install):
    """Build espeak and install ppat.
    """
    def run(self):
        subprocess.check_call(BUILD_SCRIPT)
        install.do_egg_install(self)


install_requires = []
with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'requirements.txt')) as f:
    install_requires = f.read().splitlines()

setup(name='ppat',
      version='1.0',
      description='Places & People Automate Transliterator',
      keywords = 'transliterate language chinese',
      author='EnderQIU',
      author_email='a934560824@gmail.com',
      license='GPLv3',
      url='https://github.com/EnderQIU/ppat',
      install_requires=install_requires,
      packages=['ppat', 'ppat.rules'],
      package_data={'ppat': ['rules/*.rule']},
      include_package_data=True,
      entry_points={
          'console_scripts': [
              'ppat = ppat.ppat:main',
          ],
      },
      cmdclass={'install': BuildEspeakInstallCommand}
)

