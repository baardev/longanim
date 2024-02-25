#!/bin/env python
import sys
import os
from glob import glob
import long_anim_lib as p
from collections import deque


def reverse(start, end, arr):
    # No of iterations needed for reversing the list
    no_of_reverse = end - start + 1

    # By incrementing count value swapping
    # of first and last elements is done.
    count = 0
    while ((no_of_reverse) // 2 != count):
        arr[start + count], arr[end - count] = arr[end - count], arr[start + count]
        count += 1
    return arr


def left_rotate_array(arr, d):
    # Reverse the Entire List
    size = len(arr)
    start = 0
    end = size - 1
    arr = reverse(start, end, arr)

    # Divide array into twosub-array
    # based on no of rotations.
    # Divide First sub-array
    # Reverse the First sub-array
    start = 0
    end = size - d - 1
    arr = reverse(start, end, arr)

    # Divide Second sub-array
    # Reverse the Second sub-array
    start = size - d
    end = size - 1
    arr = reverse(start, end, arr)
    return arr

# res = sys.argv[1]
# project = sys.argv[2]
# parts = res.split(":")
# W = parts[0]
# H = parts[1]
#
# files = p.get_sorted_files("images/*png")
files = p.get_sorted_files("*png")
files2 = files.copy()
files2 = left_rotate_array(files2, 1)
print("../cleantargets.py")

c = 1
tot = len(files)
for i in range(tot):
    j = i % len(files)
    i1 = files[j]
    i2 = files2[j]

    print(f"../mergerun.py -c {c}:{tot} -f {p.split_path(files[j])['nameonly']} -t {p.split_path(files2[j])['nameonly']}")
    c +=1
print("../post.py")


