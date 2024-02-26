#!/bin/bash
cd /home/jw/store/src/longanim
D=`date +%y-%m-%d_%H%S`

find . -type f \( -name "*.json*" -o -name "*.py" \) -exec tar -czf ~/share/boat_bak_${D}.tar.gz '{}' \+     