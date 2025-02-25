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
from ROOT import LeptonSFHelper, TUtil
from ctypes import c_float

class ZZExtraFiller(Module):
    def __init__(self, isMC, year, data_tag, processCR):
        print("***ZZExtraFiller: isMC:", isMC, "year:", year, "data_tag:", data_tag, flush=True)
        self.isMC = isMC
        self.processCR = processCR
        self.year = year
        if isMC:
            self.lepSFHelper = LeptonSFHelper(data_tag)

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
            self.out.branch(collName+"_dataMCWeight", "F", lenVar=theLenVar, title="data/MC efficiency correction weight")

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
            costhetastar = helcosthetaZ1 = helcosthetaZ2 = helphi = phistarZ1 = c_float(0.)
            dressedLepsp4 = [l.p4() for l in theCandLeps] # FIXME must add FSR if present
            TUtil.computeAngles(costhetastar, helcosthetaZ1, helcosthetaZ2, helphi, phistarZ1,
                                dressedLepsp4[0], theCandLeps[0].pdgId,
                                dressedLepsp4[1], theCandLeps[1].pdgId,
                                dressedLepsp4[2], theCandLeps[2].pdgId,
                                dressedLepsp4[3], theCandLeps[3].pdgId)
           
        self.out.fillBranch(collName+"_nExtraLep", nExtraLeps)
        self.out.fillBranch(collName+"_nExtraZ", nExtraZs)
        if self.isMC:
            self.out.fillBranch(collName+"_dataMCWeight", wDataMC)


    ### Compute lepton efficiency scale factor
    def getDataMCWeight(self, leps) :
        if self.year > 2023 : #FIXME: not yet implemented
            return 1.
        dataMCWeight = 1.
        for lep in leps:
            myLepID = abs(lep.pdgId)
            mySCeta = lep.eta
            isCrack = False # FIXME: isGap() is not available in nanoAODs, and cannot be recomputed easily based on eta, phi. We thus use the non-gap SFs for all electrons.
            if myLepID==11 :
                mySCeta = lep.eta + lep.deltaEtaSC    

            # Deal with very rare cases when SCeta is out of 2.5 bounds
            mySCeta = min(mySCeta,2.49)
            mySCeta = max(mySCeta,-2.49)

            SF = self.lepSFHelper.getSF(self.year, myLepID, lep.pt, lep.eta, mySCeta, isCrack)
#            SF_Unc = self.lepSFHelper.getSFError(year, myLepID, lep.pt, lep.eta, mySCeta, isCrack)
            dataMCWeight *= SF

        return dataMCWeight

        
