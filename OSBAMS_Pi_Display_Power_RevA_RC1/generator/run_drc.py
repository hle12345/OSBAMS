#!/usr/bin/python3
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
pcbnew.WriteDRCReport(b, sys.argv[2], pcbnew.EDA_UNITS_MILLIMETRES, True)
