import os

def getJetVetoMap(era, tag) :
    from PhysicsTools.NATModules.modules.jetVetoMap import jetVMAP

    if era not in [2022,2023,2024,2025]:
        raise ValueError("getJetvetoMap: Era", era, "not supported")

    if era == 2022:
            if "pre_EE" in tag:
                folderKey = "2022_Summer22"
                corrName = "Summer22_23Sep2023_RunCD_V1"
            else:
                folderKey = "2022_Summer22EE"
                corrName = "Summer22EE_23Sep2023_RunEFG_V1"
    
    elif era == 2023:
            if "pre_BPix" in tag:
                folderKey = "2023_Summer23"
                corrName = "Summer23Prompt23_RunC_V1"
            else:
                folderKey = "2023_Summer23BPix"
                corrName = "Summer23BPixPrompt23_RunD_V1"

    elif era == 2024:
       folderKey = "2024_Winter24"
       corrName = "Winter24Prompt2024BCDEFGHI_V1"

    json_JVMAP = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/%s/jetvetomaps.json.gz" % (folderKey)
    veto_map_name= "jetvetomap"
    print("folder key",folderKey)
    print("***jetJVMAP: era:", era, "tag:", tag)

    return jetVMAP(json_JVMAP, corrName, veto_map_name)
