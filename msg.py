#!/bin/env python
import sys,os
from colorama import init, Fore, Back

init()

str = sys.argv[1]
print(Back.YELLOW+Fore.BLACK+str+Fore.RESET+Back.RESET)
os.system(f'webExecute.py "{str}"')