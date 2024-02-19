#!/bin/env python
import sys
from colorama import init, Fore, Back

init()

str = sys.argv[1]
print(Back.YELLOW+Fore.BLACK+str+Fore.RESET+Back.RESET)