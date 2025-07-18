#!/bin/env python3
# Implement a check to detect cases where user has pulled the working
# area without realizing that the checkout recipe was changed.
#
# It is intended to be run the first time by the checkout script, so that it
# stores the git commit ID of the script itself.
#
import subprocess
import os, sys

def validateCheckout() :
    oldrev = None
    path = os.environ['CMSSW_BASE'] + "/src/ZZAnalysis/"
    gitrev = (subprocess.check_output(['git', "log", "-n 1", "--format=%h", "checkout_13X.csh"], cwd=path)).decode('utf-8').rstrip()

    idfile=path+"AnalysisStep/data/checkoutId"
    if os.path.isfile(idfile) :
        f = open(idfile, 'r')
        oldrev = f.read()
        f.close()
        if oldrev != gitrev :
            print("Warning: the ZZAnalysis working area has been pulled, but the checkout recipe was udpated upstream since the area was checked out.\nPlease re-create the working area.")
            print("\nDiff in the checkout script:" )
            diff = subprocess.Popen(['git', "diff", "--color=always", oldrev+".."+gitrev, "checkout_13X.csh"], cwd=path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for line in diff.stdout:
                sys.stdout.buffer.write(line)
            print("\nIf you want to proceed anyhow, please rm $CMSSW_BASE/src/ZZAnalysis/AnalysisStep/data/checkoutId\n")
            return False
        else:
            return True
    else:
        print("Checkout recipe version is:", gitrev)
        f = open(idfile, 'w')
        f.write(gitrev)
        f.close()
        return True
    
ret = validateCheckout()
if not ret:
    exit(1)
