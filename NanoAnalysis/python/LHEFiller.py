### 
# -Jet-Lepton cross-cleaning. Should be called after JES/JEC modules.
# TODO:
# - to be implemented
# - Add b-tagging info (?)
###

from __future__ import print_function
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.HeppyCore.utils.deltar import deltaR


class LHEFiller(Module):
    # def __init__(self, sampleType = "ggH"):
    def __init__(self):
        print("***LHEFiller", flush=True)
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        #self.out.branch("LHEPart_MELAStatus", "S") #Classification for LHEMothers, LHEDaughters, LHEAssociatedParticles formerly used in the miniAOD format. MELAStatus = -1 --> Intermediate, MELAStatus = 1 --> Mothers, MELAStatus =2 --> Daughters, MELAStatus = 3 --> Associated, MELASTATUS == 4 --> Jets
        self.out.branch("LHEPart_MELAStatus", "S", lenVar="nLHEPart", title="MELA_Status")
    def analyze(self, event):
        LHEPart = Collection(event, 'LHEPart')
        #Logic to sort into MELA sub-collections is based on the sample type. 
        MELA_Status = [0.]*len(LHEPart)
        for i, lp in enumerate(LHEPart):
            # print("This is i: " , i)
            # print("This is lp: ", lp)
            # print("This is PDG: ", lp.pdgId)
            if lp.status == -1: 
                #self.out.fillBranch("LHEPart_MELAStatus", 1)
                MELA_Status[i] = 1
            elif lp.status == 1: 
                parentIdx = lp.firstMotherIdx
                parentPdg = LHEPart[parentIdx].pdgId

                gParentIdx = LHEPart[parentIdx].firstMotherIdx 
                if gParentIdx == -1: 
                    gParentPdg = 0
                else: 
                    gParentPdg = LHEPart[gParentIdx].pdgId 
                if parentPdg == 23 and gParentPdg == 25:
                    #self.out.fillBranch("LHEPart_MELAStatus", 2)
                    MELA_Status[i] = 2
                else: 
                   # self.out.fillBranch("LHEPart_MELAStatus", 3)
                    MELA_Status[i] = 3
            else: 
                #self.out.fillBranch("LHEPart_MELAStatus", -1)
                MELA_Status[i] = -1 
        
        self.out.fillBranch("LHEPart_MELAStatus", MELA_Status)
        return True
    

    def getAnglesProbs(self, event):
        LHEPart = Collection(event, 'LHEPart')
        LHEMothers = filter(lambda p: p.MELAStatus==1, LHEPart)
        LHEDaughters = filter(lambda p: p.MELAStatus==2, LHEPart)
        LHEAssociated = filter(lambda p: p.MELAStatus==3, LHEPart)

        print(LHEMothers)

        return True



    # def analyze(self, event):
    #     LHEPart = Collection(event, 'LHEPart')
    #     for i, lp in enumerate(LHEPart):
    #         MELA_Stati = []
    #         if lp.status == -1: 
    #             MELA_Stati.append(1)
    #         elif lp.status == 1: 
    #             parentIdx = lp.firstMotherIdx
    #             parentPdg = LHEPart[parentIdx].pdgId

    #             gParentIdx = LHEPart[parentIdx].firstMotherIdx 
    #             if gParentIdx == -1: 
    #                 gParentPdg = 0
    #             else: 
    #                 gParentPdg = LHEPart[gParentIdx].pdgId 
    #             if parentPdg == 23 and gParentPdg == 25:
    #                 MELA_Stati.append(2)
    #             else: 
    #                 MELA_Stati.append(3)
    #         else: 
    #             MELA_Stati.append(-1)
    #         self.out.fillBranch("LHEPart_MELAStatus", MELA_Stati)
    #     return True