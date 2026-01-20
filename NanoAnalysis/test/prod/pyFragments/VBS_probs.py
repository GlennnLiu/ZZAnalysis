from ZZAnalysis.NanoAnalysis.tools import setConf

__common = {
    "MatrixElement": "MCFM",
    "Process": "bkgZZ",
    "Prod": True,
    "Dec": True,
    "Couplings": {},
    "context": "Reco",
    "computeprop": False
}

__probs = [
    {
        **__common,
        "Production": "JJVBF",
        "Name": "JJVBF_BKG_MCFM_JECNominal",
    },
    {
        **__common,
        "Name": "JJQCD_BKG_MCFM_JECNominal",
        "Production": "JJQCD",
    },
    {
        **__common,
        "Name": "JJEWQCD_BKG_MCFM_JECNominal",
        "Production": "JJEWQCD",
    },
]

for __prob in __probs:
    setConf("probabilities", __prob, append=True)

# Do not pollute the global namespace if someone does "import *" of this module
del __common, __probs, __prob
