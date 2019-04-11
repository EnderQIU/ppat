# People & Places Automated Translator

When translating games such as Crusader Kings 2 and Europa Universals 4, there are many names of places and people for
 translators to search in search engines and dictionaries, which will slow down their efficiency and enthusiasm. 
This project is aimed to translate the names automatedly but accurately.

## Getting Started From Scratch

For running this project you need `Python3`, `gcc(clang)` and `make` installed.
And get the "espeak" submodules by executing `ppat/espeak/build.sh`.

## Usage

- From source code:

```sh
# With requirements already installed
> cd ppat/
> python ppat.py
```

- From `setup.py`:

```
> python setup.py install
> ppat
```

- From `pip`:

```sh
> pip install ppat
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
