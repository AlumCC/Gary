import re
import random
from util import hook


@hook.command
def choose(inp):
    ".choose <choice1>, <choice2>, ... <choice n> - Makes a decision"
    c = re.findall(r'([^,]+)', inp)
    if len(c) == 1:
        c = re.findall(r'(\S+)', inp)
    c = [x.strip() for x in c]
    if len(set(c)) == 1:
        return "Looks like you've already made that decision."
    return random.choice(c).strip()
