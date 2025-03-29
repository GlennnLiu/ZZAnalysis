import os

# Set up the NATModules eleScaleRes module
def getEleScaleRes(era, tag, is_mc, overwritePt=True, EtDependent=True) :
    from PhysicsTools.NATModules.modules.eleScaleRes import eleScaleRes

    # Check for supported eras
    if era not in [2022, 2023]:
        raise ValueError(f"getEleScaleRes: Era {era} not supported")

    if era == 2022:
        if "pre_EE" in tag :
            scaleKey = "EGMScale_Compound_Ele_2022preEE"
            smearKey = "EGMSmearAndSyst_ElePTsplit_2022preEE" if is_mc else None
            fname = "electronSS_EtDependent_2022preEE.json.gz"
        else:
            scaleKey = "EGMScale_Compound_Ele_2022postEE"
            smearKey = "EGMSmearAndSyst_ElePTsplit_2022postEE" if is_mc else None
            fname = "electronSS_EtDependent_2022postEE.json.gz"

    elif era == 2023:
        if "pre_BPix" in tag:
            scaleKey = "EGMScale_Compound_Ele_2023preBPIX"
            smearKey = "EGMSmearAndSyst_ElePTsplit_2023preBPIX" if is_mc else None
            fname = "electronSS_EtDependent_2023preBPix.json.gz"
        else:
            scaleKey = "EGMScale_Compound_Ele_2023postBPIX"
            smearKey = "EGMSmearAndSyst_ElePTsplit_2023postBPIX" if is_mc else None
            fname = "electronSS_EtDependent_2023postBPix.json.gz"
 
    json = "%s/src/ZZAnalysis/NanoAnalysis/data/%s" % (os.environ['CMSSW_BASE'], fname)

    print("***eleScaleRes: era:", era, "tag:", tag, "is MC:", is_mc, "overwritePt:", overwritePt, "json:", json)
    return eleScaleRes(json, scaleKey, smearKey, overwritePt, EtDependent)
