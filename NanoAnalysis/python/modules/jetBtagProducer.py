"""
Instantiate the correctionlib-based b-tagging module.
"""

import os


def getJetBtagProducer(era, tag, is_mc, WP="M"):
    from PhysicsTools.NATModules.modules.jetBtag import jetBtag

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "btagEff"))

    if era == 2022:
        tagger = "particleNet"
        tagger_name = "btagPNetB"
        if "pre_EE" in tag:
            json_SF = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2022_Summer22/btagging.json.gz"
            json_eff = os.path.join(data_dir, "btag_2022.json.gz")
        else:
            json_SF = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2022_Summer22EE/btagging.json.gz"
            json_eff = os.path.join(data_dir, "btag_2022EE.json.gz")

    elif era == 2023:
        tagger = "particleNet"
        tagger_name = "btagPNetB"
        if "pre_BPix" in tag:
            json_SF = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2023_Summer23/btagging.json.gz"
            eff_year = "2023"
        else:
            json_SF = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2023_Summer23BPix/btagging.json.gz"
            eff_year = "2023BPix"
        json_eff = os.path.join(data_dir, "btag_%s.json.gz" % eff_year)

    elif era == 2024:
        tagger = "UParTAK4"
        tagger_name = "btagUParTAK4B"
        json_SF = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2024_Summer24/btagging.json.gz"
        json_eff = os.path.join(data_dir, "btag_2024.json.gz")

    elif era >= 2016 and era <= 2018:
        # FIXME: official Run 2 SF JSONs and local efficiencies should be wired when available.
        print("WARNING: official btagging json not available, using the one for 2022_Summer22")
        tagger = "particleNet"
        tagger_name = "btagPNetB"
        json_SF = "/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2022_Summer22/btagging.json.gz"
        json_eff = os.path.join(data_dir, "btag_2022.json.gz")

    else:
        raise ValueError("getJetBtagProducer: Era", era, tag, "not supported")

    if is_mc and not os.path.exists(json_eff):
        raise ValueError("getJetBtagProducer: efficiency JSON not found: %s" % json_eff)

    print(
        "***jetBtag: era:",
        era,
        "tag:",
        tag,
        "is MC:",
        is_mc,
        "tagger:",
        tagger,
        "tagger branch:",
        tagger_name,
        "WP:",
        WP,
        "json_SF:",
        json_SF,
        "json_eff:",
        json_eff,
    )

    return jetBtag(is_mc, tagger, tagger_name, WP, json_SF, json_eff)
