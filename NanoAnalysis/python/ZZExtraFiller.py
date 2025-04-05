### 
# Add extra objects/variables to the best ZZ and CR candidates in the event, for categorization
# -extra lepts
# -extra Zs
#
# TODO:
# -add other categorization variables (MELA discriminants besides KD, etc)
#
###

from __future__ import print_function
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
#from PhysicsTools.NanoAODTools.postprocessing.tools import deltaR
from ctypes import c_float
import Mela

class ZZExtraFiller(Module):
    def __init__(self, MELA, isMC, year, data_tag, processCR):
        print("***ZZExtraFiller: isMC:", isMC, "year:", year, "data_tag:", data_tag, flush=True)
        self.isMC = isMC
        self.processCR = processCR
        self.year = year
        self.MELA = MELA

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.bookExtra("ZZCand")
        if self.processCR :
            self.bookExtra("ZLLCand")

    def bookExtra(self, collName) :
        theLenVar="n"+collName
        self.out.branch(collName+"_nExtraLep", "I", lenVar=theLenVar, title="number of extra leptons passing H4l full sel")
        self.out.branch(collName+"_nExtraZ", "I", lenVar=theLenVar, title="number of extra Zs passing H4l full sel")
        if self.isMC:
            self.out.branch(collName+"_dataMCWeight", "F", lenVar=theLenVar, title="data/MC efficiency correction weight", limitedPrecision=12)

    def analyze(self, event) :
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        self.leps = list(electrons) + list(muons)
        self.Zs = Collection(event, 'ZCand')

        self.addExtra('ZZCand', event)
        if self.processCR :
            self.addExtra('ZLLCand', event)

        return True

    def addExtra(self, collName, event) :
        cands = Collection(event, collName)

        nExtraLeps = [-1]*len(cands)
        nExtraZs = [-1]*len(cands)
        wDataMC = [-1]*len(cands)
        for iCand, aCand in enumerate(cands):
            theCandLepIdxs = [aCand.Z1l1Idx, aCand.Z1l2Idx, aCand.Z2l1Idx, aCand.Z2l2Idx]

            # Extra leps
            extraLeps = []
            for i in range(len(self.leps)) :
                if i in theCandLepIdxs : continue
                if self.leps[i].ZZFullSel : extraLeps.append(i)

            # Extra Zs
            extraZs = []
            for iZ, Z in enumerate(self.Zs) :
                if Z.l1Idx in theCandLepIdxs or Z.l2Idx in theCandLepIdxs : continue
                extraZs.append(iZ)
            nExtraLeps[iCand] = len(extraLeps)
            nExtraZs[iCand] = len(extraZs)

            theCandLeps = [self.leps[i] for i in theCandLepIdxs] 
            if self.isMC:
                wDataMC[iCand] = self.getDataMCWeight(theCandLeps)

            # Kinematic angles 
            
            dressedLepsp4 = [l.p4() for l in theCandLeps] # FIXME must add FSR if present

            

            if self.MELA != None: 

                daughters = Mela.SimpleParticleCollection_t()
                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[0].pdgId, dressedLepsp4[0].Px(), dressedLepsp4[0].Py(), dressedLepsp4[0].Pz(), dressedLepsp4[0].E()))
                
                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[1].pdgId, dressedLepsp4[1].Px(), dressedLepsp4[1].Py(), dressedLepsp4[1].Pz(), dressedLepsp4[1].E()))

                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[2].pdgId, dressedLepsp4[2].Px(), dressedLepsp4[2].Py(), dressedLepsp4[2].Pz(), dressedLepsp4[2].E()))

                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[3].pdgId, dressedLepsp4[3].Px(), dressedLepsp4[3].Py(), dressedLepsp4[3].Pz(), dressedLepsp4[3].E()))
                

                self.MELA.setInputEvent(daughters, None, None, 0)

                qH, mZ1, mZ2, helcosthetaZ1, helcosthetaZ2, helPhi, costhetastar, phistarZ1 = self.MELA.computeDecayAngles() 

                self.MELA.resetInputEvent()
        
        self.out.fillBranch(collName+"_nExtraLep", nExtraLeps)
        self.out.fillBranch(collName+"_nExtraZ", nExtraZs)
        if self.isMC:
            self.out.fillBranch(collName+"_dataMCWeight", wDataMC)    
            
            
    def getDataMCWeight(self, leps) :
        '''Compute lepton efficiency scale factor for the selected leptons'''

        dataMCWeight = 1.
        for lep in leps:
            dataMCWeight *= lep.dataMC        
            
        return dataMCWeight

        
