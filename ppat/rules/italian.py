def post_process_people(word):
    """
    6-1 (弗)用于词首
    (德)用于词首和词尾
    """
    s_word = ""
    if word.startswith('夫'):
        s_word += '弗'
        s_word += word[1:]
    elif word.startswith('代'):
        s_word += '德'
        s_word += word[1:]
    elif word.endswith('代'):
        s_word += word[:-1]
        s_word += '德'
    else:
        s_word = word
    return s_word


def post_process_places(word):
    """
    6-1 (弗)用于词首
    (德)用于词首和词尾
    """
    s_word = ""
    if word.startswith('夫'):
        s_word += '弗'
        s_word += word[1:]
    elif word.startswith('代'):
        s_word += '德'
        s_word += word[1:]
    elif word.endswith('代'):
        s_word += word[:-1]
        s_word += '德'
    else:
        s_word = word
    return s_word
