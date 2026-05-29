"""
Instantiate jetId correctionlib module (for nanoAODv13 onwards, cf. https://gitlab.cern.ch/cms-nanoAOD/jsonpog-integration/-/blob/master/examples/jetidExample.py)
"""

def getJetIdProducer(era, tag) :
    from PhysicsTools.NATModules.modules.jetId import jetId
    
    if era == 2022:
        if "pre_EE" in tag:
            json = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-22CDSep23-Summer22-NanoAODv12/2026-04-13/jetid.json.gz"
        else:
            json = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-22EFGSep23-Summer22EE-NanoAODv12/2026-04-13/jetid.json.gz"
    
    elif era == 2023:
        if "pre_BPix" in tag:
            json = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-23CSep23-Summer23-NanoAODv12/2026-04-13/jetid.json.gz"
        else:
            json = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-23DSep23-Summer23BPix-NanoAODv12/2026-04-13/jetid.json.gz"

    elif era == 2024:
       json = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/2025-12-02/jetid.json.gz" #from new versioned repository; identical to 2022_Summer22

    elif era >= 2016 and era <=2018:
        # FIXME: Assume the same as 2022_Summer22 since json file is not present in official repositories
        print("WARNING: official jetid json not available, using the one for 2022_Summer22")
        json = "/cvmfs/cms-griddata.cern.ch/cat/metadata/JME/Run3-22CDSep23-Summer22-NanoAODv12/2026-04-13/jetid.json.gz"

    else: 
        raise ValueError("getJetIdProducer: get: Era", era, tag, "not supported")  

    print("***jetId: era:", era, "tag:", tag, "json:", json)
       
    return jetId(json)
