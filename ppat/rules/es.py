def post_process_people(word):
    """
    6-1 (弗)用于词首
    """
    s_word = ""
    if word.startswith('夫'):
        s_word += '弗'
        s_word += word[1:]
    else:
        s_word = word
    return s_word


def post_process_places(word):
    """
    6-1 (弗)用于词首
    """
    s_word = ""
    if word.startswith('夫'):
        s_word += '弗'
        s_word += word[1:]
    else:
        s_word = word
    return s_word