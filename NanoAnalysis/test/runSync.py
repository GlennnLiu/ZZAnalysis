#!/usr/bin/env python3
'''Script to prepare sync files

Run with: 
./runSync.py
'''

from __future__ import print_function
from ZZAnalysis.NanoAnalysis.tools import setConf, getConf, insertAfter

# Check that the checkout recipe has been properly updated 
from ZZAnalysis.AnalysisStep.validateCheckout import validateCheckout 
if not validateCheckout() :
    exit(1)

### Choose sync periods
SampleToRun = "ggH_2022EE"
#SampleToRun = "ZH_2022EE"
#SampleToRun = "ggH_2023postBPix"
#SampleToRun = "ZH_2023preBPix"

### Customize processing variables
#setConf("DEBUG", True)
setConf("runMELA", True)
setConf("bestCandByMELA", False) # best cand by KD
setConf("APPLYMUCORR", True) # Apply muon SS corrections
setConf("APPLYELECORR", True) # Apply electron SS corrections
setConf("APPLYJETCORR", False) # Apply jet corrections

json = None #replace this if needed

################################################################################
setConf("SAMPLENAME", "sync")
if SampleToRun == "ggH_2022EE" or SampleToRun == "ZH_2022EE" :
    # 2022 MC samples
    setConf("DATA_TAG", "post_EE")
    setConf("LEPTON_SETUP", 2022)
    setConf("IsMC", True)
    setConf("store","root://cms-xrd-global.cern.ch/")
    if SampleToRun == "ggH_2022EE" :
        setConf("XSEC", 52.23*0.0002745)
        setConf("fileNames",[
            "/store/mc/Run3Summer22EENanoAODv12/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg2-JHUGenV752-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/2540000/25c8f5ff-9de0-4a0c-9e2f-757332ad392f.root", #ggH 13.2 kevts
        ])
        outfile = "ZZ4lSync_ggH_2022postEE.root"
    elif SampleToRun == "ZH_2022EE" :
        setConf("XSEC", 0.9439*0.00082131) #including filter eff
        setConf("fileNames",[
        "/store/mc/Run3Summer22EENanoAODv12/ZHto2Zto4L_M125_TuneCP5_13p6TeV_powheg2-minlo-HZJ-JHUGenV752-pythia8/NANOAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/2520000/60da2336-6355-438e-ad2b-c8c4d83e50fe.root" #ZH 32.6 kevts 
        ])
        outfile = "ZZ4lSync_ZH_2022postEE.root"

elif SampleToRun == "ggH_2023postBPix" :
    # 2022 MC samples
    setConf("DATA_TAG", "post_BPix")
    setConf("XSEC", 52.23*0.0002745)
    setConf("LEPTON_SETUP", 2023)
    setConf("IsMC", True)
    setConf("store","root://cms-xrd-global.cern.ch/")
    setConf("APPLY_QCD_GGF_UNCERT", True) # for ggH
    setConf("fileNames",[
        "/store/mc/Run3Summer23BPixNanoAODv12/GluGluHtoZZto4L_M-125_TuneCP5_13p6TeV_powheg-jhugen-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_postBPix_v6-v2/50000/4daf03b4-93c9-4d35-bf53-738bb6cba90e.root", # 12 kevts
        ])
    outfile = "ZZ4lSync_ggH_2023postBPix.root"

elif SampleToRun == "ZH_2023preBPix" :
    # 2022 MC samples
    setConf("DATA_TAG", "pre_BPix")
    setConf("XSEC", 0.8196*0.00078669)
    setConf("LEPTON_SETUP", 2023)
    setConf("IsMC", True)
    setConf("store","root://cms-xrd-global.cern.ch/")
    setConf("fileNames",[
        "/store/mc/Run3Summer23NanoAODv12/ZH_Hto2Z_4LFilter_M-124p5_TuneCP5_13p6TeV_powheg-jhugenv752-pythia8/NANOAODSIM/130X_mcRun3_2023_realistic_v15-v3/40000/83211296-6c7d-493e-b7c8-0a42ed3a770c.root", # 15024 events
        ])
    outfile = "ZZ4lSync_ZH_2023preBPix.root"
else :
    print(SampleToRun, "not supported")
    exit(1)
    
# This pyFragments specifies the branches to be written
import prod.pyFragments.sync

def customizeProcessForLocalSync(p) :
    ### Tweak postprocessor parameters as necessary
    p.prefetch=True # Prefetch remote files
    p.longTermCache=True # keep prefetched files (useful for rerunning tests several times)

    p.haddFileName = outfile

    ### Select specific events to debug
    #p.cut = "event==1583673"

    ### Print out detailed candidate information for debug purposes
    #from ZZAnalysis.NanoAnalysis.dumpEvents import dumpEvents
    #p.cut = None # Remove preselction
    #insertAfter(p.modules,"lepFiller",dumpEvents(level=-1),getConf("NANOVERSION", 11)) 

    #replace JSON
    p.json = json

    #from ZZAnalysis.NanoAnalysis.dumpEvents import dumpEvents
    #insertAfter(p.modules,"lepFiller",dumpEvents(level=-1,nanoVersion=12))

setConf("customizations", customizeProcessForLocalSync, append=True)
    
#####################################################################
### This import should be done AFTER all customizations (setConf calls)
from ZZAnalysis.NanoAnalysis.nanoZZ4lAnalysis import *
######################################################################

### Run the postprocessor
p.run()

### Generate documentation file
import subprocess,os
subprocess.run(["./inspectNanoFile.py", outfile, "--doc", outfile.replace(".root",".html")])
