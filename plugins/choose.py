import re
import random
from util import hook


@hook.command('c')
@hook.command
def choose(inp):
    """choose <choice1>, <choice2>, ... <choice n> - Makes a decision."""
    c = re.findall(r'([^,]+)', inp)
    if len(c) == 1:
        c = re.findall(r'(\S+)', inp)
    c = set(x.strip() for x in c)  # prevent weighting, normalize
    if len(c) == 1:
        return "Looks like you've already made that decision."
    x = random.choice(list(c))
    if x == '4':
        return 'http://imgs.xkcd.com/comics/random_number.png'  # heh
    return x
