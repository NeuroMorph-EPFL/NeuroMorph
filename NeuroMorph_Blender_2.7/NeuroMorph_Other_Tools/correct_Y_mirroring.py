#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 22, 2017

@author: Tom Boissonnet
"""
import sys

if len(sys.argv) < 4:
    print("Too few arguments, need input/output files and the Y position to mirror")
    sys.exit(1)

obj_file  = open(sys.argv[1], 'r')
res_file  = open(sys.argv[2], 'w')

center_Y = float(sys.argv[3])

for line in obj_file:
    line_arr = line.split()
    if line_arr[0] == 'v':
        line_arr[2]  = center_Y + (center_Y - float(line_arr[2]))
        res_file.write(line_arr[0]+" "+line_arr[1]+" "+str(line_arr[2])+" "+line_arr[3]+"\n")
    else:
        res_file.write(line)

obj_file.close()
res_file.close()
    