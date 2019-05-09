"""
Espeak's Python Binding
"""
import os
import platform
import subprocess
from datetime import datetime
from functools import total_ordering

import pexpect

DEBUG = True

ESPEAK_EXEC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'espeak', 'espeak.install', 'bin', 'espeak')

ESPEAK_INTERACT_COMMAND = ESPEAK_EXEC_PATH + ' --ipa -q -v {}'  # --ipa for printing IPA, -q for quiet

ESPEAK_VERSION_COMMAND = ESPEAK_EXEC_PATH + ' --version'

ESPEAK_VOICES_COMMAND = ESPEAK_EXEC_PATH + ' --voices'

# !!! DO NOT CALL IT !!! Use "get_supported_languages()" instead
__SUPPORTED_LANGUAGES__ = {}

# Max subprocess number, should be greater than the number of items in ALWAYS_ONLINE_LANGUAGES
MAX_CHILDREN_NUMBER = 12

# Languages that usually be used, will not be closed by EspeakProcessManager if the number of process reaches its limit
ALWAYS_ONLINE_LANGUAGES = ['en-us']


def subprocess_run_by_python_version(command):
    """
    Do subprocess.run() properly in python3.5(6) and 3.7.
    See https://stackoverflow.com/questions/53209127/subprocess-unexpected-keyword-argument-capture-output
    """
    python_version = platform.python_version()
    if python_version.startswith('3.5') or python_version.startswith('3.6'):
        from subprocess import PIPE
        return subprocess.run(command.split(' ')+['>>', '/dev/null'], stdout=PIPE, stderr=PIPE).stdout.decode('utf8')
    elif python_version.startswith('3.7'):
        return subprocess.run(command, shell=True, capture_output=True).stdout.decode('utf8')
    else:
        print('Invalid python version {}. You MUST have python3.5, 3.6 or 3.7 installed.')
        exit(0)


def get_supported_languages():
    """
    Get supported language codes by execute "espeak --voices"
    :return: dict<key=language_code, value=language_full_name>
    """
    if __SUPPORTED_LANGUAGES__:
        return __SUPPORTED_LANGUAGES__
    lang_table = subprocess_run_by_python_version(ESPEAK_VOICES_COMMAND)
    if not lang_table:
        raise FileNotFoundError('"espeak" has not been installed in your OS.')
    lines = lang_table.split('\n')
    for i in range(1, len(lines)):
        items = lines[i].split()
        if len(items) < 3:
            continue
        __SUPPORTED_LANGUAGES__[items[1]] = items[3]
    return __SUPPORTED_LANGUAGES__


assert len(ALWAYS_ONLINE_LANGUAGES) < MAX_CHILDREN_NUMBER
assert all([i in get_supported_languages().keys() for i in ALWAYS_ONLINE_LANGUAGES])


def print_supported_languages():
    print('Code', '\t', 'Full Name')
    for language_code, language_full_name in get_supported_languages().items():
        print(language_code, '\t', language_full_name)


def get_espeak_version():
    return subprocess_run_by_python_version(ESPEAK_VERSION_COMMAND)


def _spawn_espeak(language):
    """
    Spawn a espeak interactive subprocess
    :param language:
    :return:
    """
    assert language in get_supported_languages().keys()

    return pexpect.spawn(ESPEAK_INTERACT_COMMAND.format(language))


@total_ordering
class EspeakProcess(object):
    """
    An espeak interactive process
    """

    def __init__(self, language):
        assert language in get_supported_languages().keys()

        if DEBUG:
            self._create_time = datetime.now()
        self.language = language
        self._calls = 0
        self._child = _spawn_espeak(language)

    def __eq__(self, other):
        return self._calls == other.calls

    def __lt__(self, other):
        return self._calls < other.calls

    def __del__(self):
        self.close()

    def to_ipa(self, word):
        assert ' ' not in word

        if self._child.closed:
            self._child = _spawn_espeak(self.language)

        self._child.sendline(word)
        self._child.expect('\r\n', timeout=3)
        self._child.expect('\r\n', timeout=3)
        self._calls += 1
        return self._child.before

    @property
    def calls(self):
        return self._calls

    @property
    def closed(self):
        return self._child.closed

    def close(self):
        if DEBUG:
            period = (datetime.now() - self._create_time).seconds
            print('Process of language "{}" has lived for {} second(s) and been called {} time(s)'
                  .format(self.language, period, self._calls))

        self._child.close()


class EspeakProcessManager(object):
    """
    A manager manages all espeak processes, for providing the best performance
    """

    _always_online_processes = {i: EspeakProcess(i) for i in ALWAYS_ONLINE_LANGUAGES}
    _scalable_processes_limit = MAX_CHILDREN_NUMBER - len(_always_online_processes.keys())
    _scalable_processes = {}

    def to_ipa_for_language(self, word, language):
        """
        Get IPA for a certain language
        :param word:
        :param language:
        :return: str: phonetics
        """
        assert isinstance(word, str) and ' ' not in word
        assert isinstance(language, str) and language in get_supported_languages()

        return self.to_ipa_for_languages(word, [language])[language]

    def to_ipa_for_languages(self, word, languages):
        """
        Get IPA for several languages at a time
        :param word: str: Should not contains any spaces
        :param languages: list<str>: not repeated languages
        :return: dict{language_code: phonetics}
        """
        assert isinstance(word, str) and ' ' not in word
        assert isinstance(languages, list) and all([i in get_supported_languages().keys() for i in languages]) \
            and languages[1:] == languages[:-1]

        result = {}
        for language in languages:
            if language in self._always_online_processes.keys():
                result[language] = self._always_online_processes[language].to_ipa(word)
            elif language in self._scalable_processes.keys():
                result[language] = self._scalable_processes[language].to_ipa(word)
            else:
                # create a new espeak process
                new_process = EspeakProcess(language)
                result[language] = new_process.to_ipa(word)
                if len(self._scalable_processes.keys()) >= self._scalable_processes_limit:
                    # Start of Algorithm
                    tmp_min_item = self._scalable_processes.popitem()
                    for k, v in self._scalable_processes.items():
                        if v < tmp_min_item[1]:
                            tmp_min_item = (k, v)
                    # End of algorithm
                    self._scalable_processes[tmp_min_item[0]] = tmp_min_item[1]
                    self._scalable_processes.pop(tmp_min_item[0])
                self._scalable_processes[language] = new_process
        return result
