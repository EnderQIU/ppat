# People & Places Automated Translator

When translating games such as Crusader Kings 2 and Europa Universals 4, there are many names of places and people for
 translators to search in search engines and dictionaries, which will slow down their efficiency and enthusiasm. 
This project is aimed to translate the names automatedly but accurately.

## Getting Started From Scratch

1. Clone project by `git clone https://github.com/EnderQIU/ppat.git` or `git clone git@github.com:EnderQIU/ppat.git`. If you want to clone espeak submodule at the same time, add `--recursive` option to the end.
2. Simply run `python setup.py install` and follow the instructions in it.
3. Command `ppat` is ready on your shell.

## Usage

- Most common usage:

```sh
$ ppat
!!!Welcome to PPAT transliterate engine!!!

#    _____  _____     _______
#   |  __ \|  __ \ /\|__   __|
#   | |__) | |__) /  \  | |
#   |  ___/|  ___/ /\ \ | |
#   | |    | |  / ____ \| |
#   |_|    |_| /_/    \_\_|
#
#

Version v1.0
Start loading rule files...

[OK] Rule file "/home/*************/rules/en-us.rule".

All rule files are loaded!
Input names of people or places after the prompt.
Type ":help" for more instructions.
```

- Enable verbose mode to debug your rule files:

```sh
$ ppat verbose
```

## Write Transliteration Rules

Transliteration rules are stored in `ppat/rules` directory. You can write your own rule for a specified language follow
 the `en-us.rule` example.

## Acknowledgement

Portion of this software may utilize the following copyrighted materials, the use of which is hereby acknowledged.

- [espeak](http://espeak.sourceforge.net)

## Authors

- [EnderQIU](https://github.com/EnderQIU)

## License

This project is open-sourced under the GPL v3 License.

## About Copyright

1. No copyright infringement intended.
2. If there is a copyright violation content, please e-mail <a934560824@163.com> to delete.
3. No money is being made of this project.
