"""
Main entry of PPAT
"""
import _io
import importlib
import os
import re
import sys
from functools import total_ordering

from prettytable import PrettyTable

from .pespeak import get_supported_languages, EspeakProcessManager

try:
    import readline
except:
    pass

DEFAULT_ACTIVATED_LANGUAGES = ['en-us']

RULES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'rules')

espeak_engine = EspeakProcessManager()

VERSION = 'v1.0'

WELCOME = """!!!Welcome to PPAT transliterate engine!!!

#    _____  _____     _______ 
#   |  __ \|  __ \ /\|__   __|
#   | |__) | |__) /  \  | |   
#   |  ___/|  ___/ /\ \ | |   
#   | |    | |  / ____ \| |   
#   |_|    |_| /_/    \_\_|   
#                             
#                             

Version {}
Start loading rule files...
""".format(VERSION)

READY = """
All rule files are loaded!
Input names of people or places after the prompt.
Type ":help" for more instructions.
"""

CONFIG = """
:config languages <lang1> <lang2> ...  Set languages for transliterating.
:config verbose <on|off>               Enable verbose mode for debugging messages.
"""

HELP = """
Type a word without spaces to transliterate.

:c\t:config                Get all available configurations.
:c\t:config <key> <value>  Set a configuration.
:l\t:lang                  Get all available languages.
:q\t:quit                  Quit PPAT.
:h\t:help                  Print this message.

The default source languages are set to:
{}
""".format('\n'.join(i for i in DEFAULT_ACTIVATED_LANGUAGES))

BYE = """Bye.
"""


def get_rule_file_path(language):
    return os.path.join(RULES_DIR, language + '.rule')


def get_rule_script_import_path(language):
    return '.rules.{}'.format(language.replace('-', '_'))


def get_rule_script_file_path(language):
    return os.path.join(RULES_DIR, language.replace('-', '_') + '.py')


def log(msg, line_number, file_path, section=None):
    assert isinstance(line_number, int)
    assert isinstance(file_path, str)

    if section:
        return msg + ' in section "{}" at line {} in file : {}'.format(section, line_number, file_path)
    else:
        return msg + ' at line {} in file : {}'.format(line_number, file_path)


def espeak(word, language_code):
    """
    Call EspeakProcessManager.to_ipa_for_language(), replace stresses.
    :param word:
    :param language_code:
    :return:
    """
    assert language_code in get_supported_languages()

    return espeak_engine.to_ipa_for_language(word, language_code).decode('utf8')\
        .translate(str.maketrans({'ˈ': None, 'ˌ': None}))


@total_ordering
class MatchRule(object):
    """
    <pre>)<match>(<pro> => coord

    <match> will be separated into str by "|" when loaded by Rule.
    <pre> WILL NOT be added a "$" at the tail when loaded by Rule.
    <post> WILL NOT be added a "^" at the beginning when loaded by Rule.

    """

    @staticmethod
    def highest_priority(match_rule_list):
        """
        The MatchRule with the smallest line_number is the one with highest priority.
        Because matches of the same line is definitely different, there won't be two different matches at the same line
        :param match_rule_list:
        :return:
        """
        assert all([isinstance(i, MatchRule) for i in match_rule_list])

        return min(match_rule_list)

    def __init__(self, line_number, prefix, match, postfix, coord):
        assert isinstance(line_number, int) and line_number > 0
        assert isinstance(match, str)
        assert isinstance(coord, int) and coord > 0

        self.line_number = line_number
        self.match = match
        self.prefix = prefix
        self.postfix = postfix
        self.coord = coord

    def check(self, prefix, postfix):
        """
        Check candidate's prefix and postfix if prefix or postfix is not None
        :param prefix: the actual prefix
        :param postfix: the actual postfix
        :return:
        """
        prefix_pass = True
        postfix_pass = True
        if self.prefix is not None:
            if not re.search(self.prefix, prefix):
                prefix_pass = False
        if self.postfix is not None:
            if not re.search(self.postfix, postfix):
                postfix_pass = False
        return prefix_pass and postfix_pass

    def __eq__(self, other):
        return self.line_number == other.line_number

    def __lt__(self, other):
        return self.line_number < other.line_number


class Rule(object):
    """
    Python Object of one .rule file
    """
    vowels = []
    consonants = []
    vowels_people = {}
    vowels_places = {}
    consonants_people = {}
    consonants_places = {}
    max_match_length = -1  # Max match's length over the matches
    transliteration_people = {}
    transliteration_places = {}
    to_phonetics_people = None
    to_phonetics_places = None
    post_process_people = None
    post_process_places = None
    info_sections = ('.meta', '.phonetics',)
    method_sections = ('.to_phonetics', '.post_process',)
    match_sections = ('.vowels people', '.vowels places', '.consonants people', '.consonants places',)
    transliteration_sections = ('.transliteration people', '.transliteration places',)
    all_sections = info_sections + method_sections + match_sections + transliteration_sections

    def _get_section_attr(self, section_name):
        assert section_name in self.match_sections + self.transliteration_sections

        return getattr(self, section_name[1:].replace(' ', '_'))

    @staticmethod
    def split_kv(line):
        assert isinstance(line, str)

        items = line.split('=')
        assert len(items) == 2, 'Line "{}" is supposed to be a "key=value" pair.'.format(line)
        return items[0].strip(), items[1].strip()

    @staticmethod
    def parse_k_in_match_section(k):
        assert isinstance(k, str)

        prefix_end = k.find(')')
        postfix_start = k.find('(')

        prefix = k[0: prefix_end].strip() if prefix_end != -1 else None
        postfix = k[postfix_start + 1:].strip() if postfix_start != -1 else None
        if prefix_end != -1 and postfix_start != -1:
            match_str = k[prefix_end + 1: postfix_start].strip()
        elif prefix_end != -1 and postfix_start == -1:
            match_str = k[prefix_end + 1:].strip()
        elif prefix_end == -1 and postfix_start != -1:
            match_str = k[: postfix_start].strip()
        else:
            match_str = k.strip()
        match_list = [s.strip() for s in match_str.split('|')]
        return prefix, match_list, postfix

    @staticmethod
    def parse_k_in_transliteration_section(k):
        assert isinstance(k, str) and ',' in k, \
            'Key "{}" in transliteration section should in "coord_c, coord_v" format. Check your rule file.'.format(k)

        items = k.split(',')
        assert len(items) == 2

        return int(items[0].strip()), int(items[1].strip())

    @staticmethod
    def coord_to_key(coord_c, coord_v):
        assert isinstance(coord_c, int) and isinstance(coord_v, int)

        return str(coord_c) + ',' + str(coord_v)

    def parse_pre_or_post(self, pre_or_post):
        if pre_or_post is None:
            return None
        any_consonants = '[' + '|'.join(self.consonants) + ']'
        any_vowels = '[' + '|'.join(self.vowels) + ']'
        return pre_or_post.replace('&', any_consonants).replace('@', any_vowels)

    def __init__(self, rule_file):
        assert isinstance(rule_file, _io.TextIOWrapper)

        self.rule_file_name = rule_file.name
        self.language_code = os.path.split(os.path.splitext(rule_file.name)[0])[1]
        current_section = ''
        met_sections = {k: False for k in self.all_sections}
        line_number = 0
        for line in rule_file:
            line = line.strip()
            line_number += 1
            if line.startswith('//') or line == '':
                continue
            if line.startswith('.'):
                assert not met_sections[line], log('Section "{}" duplicated'.format(line),
                                                   line_number, rule_file.name)
                met_sections[line] = True
                current_section = line
                continue
            if current_section == '.meta':
                k, v = self.split_kv(line)
                self.language_full_name = v if k == 'language_full_name' else 'NOT DEFINED'
            elif current_section == '.phonetics':
                k, v = self.split_kv(line)
                assert k in ('vowels', 'consonants',), log('Key "{}" not allowed',
                                                           line_number, rule_file.name, current_section)
                setattr(self, k, [i.strip() for i in v.split('|')])
            elif current_section == '.to_phonetics':
                k, v = self.split_kv(line)
                if v == 'copy':
                    setattr(self, 'to_phonetics_' + k, lambda x: x)
                elif v == 'lowercase':
                    setattr(self, 'to_phonetics_' + k, lambda x: x.lower())
                elif v == 'espeak':
                    assert self.language_code in get_supported_languages(), \
                        'Cannot use espeak for language "{}"'.format(self.language_code)
                    setattr(self, 'to_phonetics_' + k, lambda x: espeak(x, self.language_code))
                else:
                    assert os.path.exists(get_rule_script_import_path(self.language_code)), \
                        log('No such file {}.py'.format(self.language_code),
                            line_number, rule_file.name, current_section)
                    setattr(self, 'to_phonetics_' + k,
                            importlib.import_module(
                                get_rule_script_import_path(self.language_code),
                                package='ppat').__getattribute__(v),
                            )
            elif current_section in self.match_sections:
                k, v = self.split_kv(line)
                pre, match_list, post = self.parse_k_in_match_section(k)
                pre = self.parse_pre_or_post(pre)
                post = self.parse_pre_or_post(post)
                coord = int(v)
                for match in match_list:
                    if len(match) > self.max_match_length:
                        self.max_match_length = len(match)
                    rule = MatchRule(line_number, pre, match, post, coord)
                    if rule.match in self._get_section_attr(current_section).keys():
                        self._get_section_attr(current_section)[rule.match].append(rule)
                    else:
                        self._get_section_attr(current_section)[rule.match] = [rule]
            elif current_section in self.transliteration_sections:
                k, v = self.split_kv(line)
                coord_c, coord_v = self.parse_k_in_transliteration_section(k)
                self._get_section_attr(current_section)[self.coord_to_key(coord_c, coord_v)] = v
            elif current_section == '.post_process':
                k, v = self.split_kv(line)
                assert k in ('people', 'places')

                if v == 'copy':
                    setattr(self, 'post_process_' + k, lambda x: x)
                else:
                    assert os.path.exists(get_rule_script_file_path(self.language_code)), \
                        log('No such file {}.py in {}'.format(get_rule_script_file_path(self.language_code),
                                                              self.language_code),
                            line_number, rule_file.name, current_section)
                    setattr(self, 'post_process_' + k,
                            importlib.import_module(
                                get_rule_script_import_path(self.language_code),
                                package='ppat').__getattribute__(v)
                            )
            else:
                log('Invalid section "{}"'.format(line), line_number, rule_file.name)
        assert all(met_sections.values()), 'Missing necessary section(s).\n' + str(met_sections)
        assert self.max_match_length > 1
        print('[OK] Rule file "{}".'.format(rule_file.name))


class RulesManager(object):
    rules = {}
    current_rule = None
    current_vowels_match_rules = None
    current_consonants_match_rules = None
    current_transliteration_dict = None
    verbose = False

    @staticmethod
    def list_rules_path():
        r = []
        for file_name in os.listdir(RULES_DIR):
            if os.path.splitext(file_name)[1] == '.rule':
                r.append(os.path.join(RULES_DIR, file_name))
        return r

    @staticmethod
    def debug(category, hans, coord_c, coord_v, phonetics, start):
        print('='*5, 'DEBUG MESSAGE', '='*5)
        print('category:', category)
        print('phonetics:', phonetics)
        print('rest:', phonetics[start:])
        print('hans:', hans)
        print('coord_c:', coord_c)
        print('coord_v:', coord_v)
        print('='*25)

    def __init__(self):
        for file_path in self.list_rules_path():
            with open(file_path, 'r', encoding='utf8') as rule_file:
                rule = Rule(rule_file)
                self.rules[rule.language_code] = rule

    def get_supported_languages(self):
        return self.rules.keys()

    def get_supported_language_full_name(self, language_code):
        return self.rules[language_code].language_full_name

    def get_supported_languages_and_full_names(self):
        return {k: self.rules[k].language_full_name for k in self.rules.keys()}

    def _longest_prefix_match(self, category, phonetics, start):
        assert category in ('vowels', 'consonants',)
        assert isinstance(phonetics, str)
        assert isinstance(start, int)

        # a match rule that both <people|places> and <vowels|conspnants> are specified
        match_rules = getattr(self, 'current_' + category + '_match_rules')  # dict{MatchRule.match: MatchRule())

        # Match from the possible longest length. If not matched, try a shorter one.
        expected_match_length = min(self.current_rule.max_match_length, len(phonetics[start:]))
        if expected_match_length <= 0:
            return -1, ''  # Nothing to match
        candidates = []  # MatchRules that have been checked pre/postfix
        while expected_match_length > 0:
            prefix = phonetics[0: start]
            expected_match = phonetics[start: start + expected_match_length]
            postfix = phonetics[start + expected_match_length:]
            candidate_matches = match_rules.get(expected_match, [])  # MatchRules that have not been checked pre/postfix
            for candidate_match in candidate_matches:
                if candidate_match.check(prefix, postfix):
                    candidates.append(candidate_match)
            if candidates:
                break
            else:
                expected_match_length -= 1
        if candidates:
            final_match_rule = MatchRule.highest_priority(candidates)
            return final_match_rule.coord, final_match_rule.match
        else:
            return -1, ''  # Nothing to match

    def _find_han_by_coords(self, coord_c, coord_v):
        assert isinstance(coord_c, int) and isinstance(coord_v, int)

        han = self.current_transliteration_dict.get(Rule.coord_to_key(coord_c, coord_v), '')
        assert han, 'No such coords ({}, {}) for rule "{}".'.format(coord_c, coord_v, self.current_rule.rule_file_name)
        return han

    def to_hans(self, phonetics, language, category):
        """
        phonetics => hans

        e.g.
        phonetics = fˌɪbənˈɑːtʃi
                       ^
                       start = 2 (ignore the stresses)
        <pre> = 'f'
        <match> = 'bə'
        <post> = 'nɑːtʃi'
        <coord_c> = coord of 'b', given by lpm(consonants)
        <coord_v> = coord of 'ə', given by lpm(vowels)
        :param phonetics:
        :param language:
        :param category:
        :return:
        """
        assert all([isinstance(i, str) for i in (phonetics, language, category)])
        assert language in self.get_supported_languages()
        assert category in ('people', 'places',)

        start = 0  # index where <match> begins
        match = ''  # <match>'s content if match succeeded, else ''
        hans = ''
        self.current_rule = self.rules[language]
        self.current_vowels_match_rules = getattr(self.current_rule, 'vowels_' + category)  # a MatchRule dict
        self.current_consonants_match_rules = getattr(self.current_rule, 'consonants_' + category)
        self.current_transliteration_dict = getattr(self.current_rule, 'transliteration_' + category)
        while start + len(match) < len(phonetics):
            coord_v, match = self._longest_prefix_match('vowels', phonetics, start)
            if match:
                hans += self._find_han_by_coords(1, coord_v)
                start += len(match)
            else:
                coord_c, match = self._longest_prefix_match('consonants', phonetics, start)
                if match:
                    start += len(match)
                    # the consonant is the last phonetic of the word, no need to check vowels
                    if start == len(phonetics):
                        hans += self._find_han_by_coords(coord_c, 1)
                        break
                    coord_v, match = self._longest_prefix_match('vowels', phonetics, start)
                    if match:
                        hans += self._find_han_by_coords(coord_c, coord_v)
                        start += len(match)
                    else:
                        hans += self._find_han_by_coords(coord_c, 1)
                else:
                    print('No {} rule matched for phonetics "{}", check your rules file.'.format(category, phonetics))
                    if self.verbose:
                        self.debug(category, hans, coord_c, coord_v, phonetics, start)
                    exit(-1)
            match = ''  # clear match for the next loop
        return hans

    def transliterate(self, word, language):
        assert isinstance(word, str) and ' ' not in word
        assert language in self.get_supported_languages()

        rule = self.rules[language]
        phonetics_people = rule.to_phonetics_people(word)
        hans_people = self.to_hans(phonetics_people, language, 'people')
        phonetics_places = rule.to_phonetics_places(word)
        hans_places = self.to_hans(phonetics_places, language, 'places')

        return phonetics_people, hans_people, phonetics_places, hans_places


class PPAT(object):
    """
    PPAT Main Program
    """
    rule_manager = None
    activated_languages = DEFAULT_ACTIVATED_LANGUAGES

    def config(self, command):
        if command in ('config', 'c', ):
            print(CONFIG)
            return
        items = command.split(' ')
        if items[1] == 'verbose':
            if len(items) != 3:
                print('Usage: :config verbose <on|off>')
                return
            if items[2] == 'on':
                self.rule_manager.verbose = True
            elif items[2] == 'off':
                self.rule_manager.verbose = False
            else:
                print('Invalid value "{}". Usage: :config verbose <on|off>'.format(items[2]))
        elif items[1] == 'languages':
            if len(items) < 3:
                print('Please specify one language at least. See all available languages by typing ":lang".')
            else:
                if any([i not in self.rule_manager.get_supported_languages() for i in items[2:]]):
                    print('Invalid language code. See all available languages by typing ":lang".')
                    return
                self.activated_languages = items[2:]

    def command(self, command):
        if command in ('help', 'h', ):
            print(HELP)
        elif command in ('lang', 'l', ):
            x = PrettyTable()
            x.field_names = ['Language Code', 'Language Full Name', 'Status']
            for language_code, language_full_name in self.rule_manager.get_supported_languages_and_full_names().items():
                x.add_row([language_code,
                           language_full_name,
                           'ON' if language_code in self.activated_languages else 'OFF'
                           ])
            print(x)
        elif command.startswith('c') or command.startswith('config'):
            self.config(command)
        else:
            print('Invalid command "{}". Type ":help" for more instructions.'.format(command))

    def cli(self, _verbose=False):
        print(WELCOME)
        self.rule_manager = RulesManager()
        self.rule_manager.verbose = _verbose
        print(READY)
        while True:
            word = input('> ')
            if word.startswith(':quit') or word.startswith(':q'):
                break
            if word.startswith(':'):
                self.command(word.lstrip(':'))
            else:
                self.transliterate(word)
        print(BYE)

    def transliterate(self, word):
        if ' ' in word:
            print('Word cannot contain spaces.')
            return
        x = PrettyTable()
        x.field_names = ['Language', 'Phonetics(people)', 'Chinese(people)', 'Phonetics(places)', 'Chinese(places)']
        for language in self.activated_languages:
            row = [self.rule_manager.get_supported_language_full_name(language)]+\
                    list(self.rule_manager.transliterate(word, language))
            x.add_row(row)
        print(x)

def main():
    if sys.getdefaultencoding() != 'utf-8':
        print('The system deault encoding is not UTF-8. Please set your shelli\'s encoding to UTF-8 for multi-language display.')
        print("""In Linux:
        \texport LANG=C.UTF-8
        In Windows Powershell:
        \tPlease Google "Windows Powershell utf8"
        Exiting...
        """
        )
        exit(0)
    verbose = True if 'verbose' in sys.argv[1:] else False
    ppat = PPAT()
    ppat.cli(verbose)


if __name__ == '__main__':
    main()

