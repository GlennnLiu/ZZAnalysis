'''
Add categorization to ZZCand and ZLLCand collections.
This is currently for validation/x-checks, as the actual categorization
for physics results is normally defined in the statistical analysis step.
'''

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

class ZZCategorization(Module):
    def __init__(self, processCR=False):
        self.processCR = processCR
        print("***ZZCategorization", flush=True)
        fake=ROOT.KFactors.kfactor_qqZZ_qcd_M # trigger loading of library, so that functions become available

        
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.book("ZZCand")
        if self.processCR :
            self.book("ZLLCand")

    def analyze(self, event) :
        jets = Collection(event, "Jet")
        nBTag = sum(1 for jet in jets if (jet.jetId == 6 and jet.ZZMask == False and jet.btagDeepFlavB>0.19 and jet.pt>30.)) # FIXME: handle the different pT cut at large eta - best way would be to add a new flag in jetFiller
        self.fill('ZZCand', event, nBTag)
        if self.processCR :
            self.fill('ZLLCand', event, nBTag)
        return True

    def book(self, collName) :
        theLenVar="n"+collName
        self.out.branch(collName+"_categoryMor18", "S", lenVar=theLenVar, title="Categorization")

    def fill(self, collName, event, nBTag) :
        cands = Collection(event, collName)
        cats = [-1]*len(cands)

        dir=ROOT.gDirectory.GetDirectory("") #cache dir, since categoryMor18 internally changes directory
        for iC, aC in enumerate(cands):            
            cats[iC] = ROOT.categoryMor18(aC.nExtraLep,
                                          aC.nExtraZ,
                                          event.nCleanedJetsPt30,
                                          nBTag,
                                          ROOT.nullptr, # jetQGLikelihood, unused if useQGTagging==False
			                  aC.P_JJQCD_SIG_ghg2_1_JHUGen_JECNominal,
			                  aC.P_JQCD_SIG_ghg2_1_JHUGen_JECNominal,
			                  aC.P_JJVBF_SIG_ghv1_1_JHUGen_JECNominal,
			                  aC.P_JVBF_SIG_ghv1_1_JHUGen_JECNominal,
			                  aC.P_JVBF_SIG_ghv1_1_JHUGen_JECNominal_aux, #pAux_JVBF_SIG_ghv1_1_JHUGen_JECNominal,
			                  aC.P_HadWH_SIG_ghw1_1_JHUGen_JECNominal,
			                  aC.P_HadZH_SIG_ghz1_1_JHUGen_JECNominal,
				          aC.P_HadWH_SIG_ghw1_1_JHUGen_JECNominal_mavjj, #P_HadWH_mavjj_JECNominal,
				          aC.P_HadWH_SIG_ghw1_1_JHUGen_JECNominal_mavjj_true, #P_HadWH_mavjj_true_JECNominal,
				          aC.P_HadZH_SIG_ghz1_1_JHUGen_JECNominal_mavjj, #P_HadZH_mavjj_JECNominal,
				          aC.P_HadZH_SIG_ghz1_1_JHUGen_JECNominal_mavjj_true, #P_HadZH_mavjj_true_JECNominal,
			                  ROOT.nullptr, # jetPhi, unused if useQGTagging==False
			                  aC.mass,
			                  0., # PFMET, unused if useVHMETTagged == False
                                          False, # useVHMETTagged
                                          False  # useQGTagging
                                          )
         
        dir.cd()
        self.out.fillBranch(collName+"_categoryMor18", cats)
