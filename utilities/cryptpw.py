#!/usr/bin/env python

from core import chimera_crypto
import sys

try:
    pw = sys.argv[1]
except:
    print("string to encrypt must be given as an argument")
    sys.exit(1)

worker = chimera_crypto()

print worker.encrypt(pw)
