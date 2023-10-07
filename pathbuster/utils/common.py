import string
import random
from hashlib import md5


def random_str(length=30):
    """Generate a random string of fixed length """
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))


def count_lines(text: str):
    if len(text) > 0:
        return text.count("\n") + 1
    else:
        return 0


def count_words(text: str):
    if len(text) > 0:
        return text.count(" ") + 1
    else:
        return 0


def md5str(s):
    return md5(s.encode()).hexdigest()