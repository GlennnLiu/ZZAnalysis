#!/usr/bin/env python3
# 
#
from __future__ import print_function

import os
import glob
from pathlib import Path
import time
import re
import sys
from optparse import OptionParser
from prettytable import PrettyTable

use_walltime = True

if __name__ == '__main__':

    parser = OptionParser()
    parser.usage = """
    %prog <dir>
    Scan chunk logs in current production folder and print job CPU statistics for each sample
    """

    # (options,args) = parser.parse_args()
    # if len(args)>=1:
    #     path = args[0]
    # else :
    #     path="AAAOK/Chunks"

    ## read chunk -> job ID mapping
    with open("log/ProcIds") as f:
        chunks = {parts[0]: int(parts[1])for line in f if (parts := line.split())}

    ## read log file
    logfile = glob.glob("log/*.log")
    if len(logfile) == 0:
        print ("No log found.")
        sys.exit(1)
    elif len(logfile)>1 :
        print ("There should be 1 single log file, found: {logfile}")
        sys.exit(1)
          
    logfile = logfile[0]
    clusterId = Path(logfile).stem

    time_execute = {}

    with open(logfile) as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines):
        if " Job terminated." not in line:
            continue
        
        # Extract job ID from e.g. "(14517935.599.000)"
        match = re.search(r'\((\d+)\.(\d+)\.\d+\)', line)
        if not match:
            continue
        if clusterId != match.group(1) :
            print(f"clusterId mismatch, {clusterId} - {match.group(1)}")
        job_id = int(match.group(2))

        if use_walltime :
            # Search for "TimeExecute" in the following lines
            for j in range(i + 1, min(i + 20, len(lines))):
                te_match = re.search(r'TimeExecute \(s\)\s*:\s*([\d.]+)', lines[j])
                if te_match:
                    cpu = int(te_match.group(1))
                    break
        else:
            # Search for "Run Remote Usage" in the following lines
            for j in range(i + 1, min(i + 20, len(lines))):
                    if "Total Remote Usage" in lines[j]:
                        cpustring=lines[j].split()[2]
                        cpustring=cpustring.replace(",","")
                        tt=time.strptime(cpustring,"%H:%M:%S")
                        cpu=tt.tm_hour*3600 + tt.tm_min*60 + tt.tm_sec
                        break
        time_execute[job_id] = int(cpu)


    
    datasets = {}
    for chunkname, job_id in chunks.items() :
        dataset = re.sub("_Chunk.*$","",chunkname)
        try : 
            cpu = time_execute[job_id]
        except KeyError:
            print("Skipping unfinished job:", chunkname) 
            continue
        if cpu != -1 :
            if dataset in datasets:
                datasets[dataset] = [min(cpu,datasets[dataset][0]),cpu+datasets[dataset][1],max(cpu,datasets[dataset][2]),datasets[dataset][3]+1]
            else:
                datasets[dataset] = [cpu, cpu, cpu, 1]
    
    print("CPU usage: njobs, min/avg/max (h):")
    table = PrettyTable(['dataset', '#Chunks', 'min', 'avg', 'max'])

    for dataset in datasets:
        table.add_row([dataset,  datasets[dataset][3], f"{datasets[dataset][0]/3600.:.1f}", f"{datasets[dataset][1]/3600./datasets[dataset][3]:.1f}", f"{datasets[dataset][2]/3600.:.1f}"])

    for col in table.field_names:
        table.align[col] = "l"
    print(table)

    mex = """\n JobFlavours are:
espresso     = 20 minutes
microcentury = 1 hour
longlunch    = 2 hours
workday      = 8 hours
tomorrow     = 1 day
testmatch    = 3 days
nextweek     = 1 week"""
    print(mex)
