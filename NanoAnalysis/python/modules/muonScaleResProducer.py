import os

# Set up the NATModules muonScaleRes module
def getMuonScaleRes(era, tag, is_mc, overwritePt=True) :
    from PhysicsTools.NATModules.modules.muonScaleRes import muonScaleRes 

    if era == 2022:
        if "pre_EE" in tag :
            fname = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run3-22CDSep23-Summer22-NanoAODv12/2026-06-18/muon_scalesmearing.json.gz"

        else :
            fname = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run3-22EFGSep23-Summer22EE-NanoAODv12/2026-06-18/muon_scalesmearing.json.gz" 

    elif era == 2023:
        if "pre_BPix" in tag:
            fname = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run3-23CSep23-Summer23-NanoAODv12/2026-06-18/muon_scalesmearing.json.gz"

        else:
            fname = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run3-23DSep23-Summer23BPix-NanoAODv12/2026-06-18/muon_scalesmearing.json.gz"

    elif era == 2024:
        fname = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run3-24CDEReprocessingFGHIPrompt-Summer24-NanoAODv15/2026-06-18/muon_scalesmearing.json.gz"

    elif era == 2025:
        fname = "/cvmfs/cms-griddata.cern.ch/cat/metadata/MUO/Run3-25Prompt-Summer24-NanoAODv15/2026-04-28/muon_scalesmearing.json.gz"

    else:
        raise ValueError(f"getMuonScaleRes: Era {era} is not supported")

    print("***muonScaleRes: era:", era, "tag:", tag, "is MC:", is_mc, "overwritePt:", overwritePt, "json:", fname)
    return muonScaleRes(fname, is_mc, overwritePt, minPt=3.)

