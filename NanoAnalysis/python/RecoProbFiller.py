import copy
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from ZZAnalysis.NanoAnalysis.MELAProbHelper import MELAProbHelper
from ZZAnalysis.NanoAnalysis.tools import branchCollection
import Mela


class RecoProbFiller(Module):
    """Calculates proabilities with Reco-level information. 
    MELA = Pointer to MELA passed from nanoZZ4lAnalysis.py 
    MELASettings = dictionary with settings for the probabilities to be computed
    processCR = if True, also fill ZLLCand with the same probabilities as ZZCand
    """
    
    def __init__(self, MELA, NANOVERSION, MELASettings=None, processCR=False):
        self.MELA = MELA
        self.NANOVERSION = NANOVERSION
        self.MELASettings = MELASettings
        self.processCR = processCR
        self.probHelpers = {"ZZCand": MELAProbHelper(self.MELA, self.MELASettings, "Reco", candColl="ZZCand")}
        if self.processCR:
            self.probHelpers["ZLLCand"] = MELAProbHelper(self.MELA, self.MELASettings, "Reco", candColl="ZLLCand")
        print("***RecoProbFiller: set for: ", self.probHelpers["ZZCand"].names,
              "processCR:", self.processCR, flush=True)
        self.filler = {}


    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.filler["ZZCand"] = branchCollection(wrappedOutputTree, lenVar="nZZCand")
        self.bookAngles("ZZCand", self.filler["ZZCand"])
        if self.processCR:
            self.filler["ZLLCand"] = branchCollection(wrappedOutputTree, lenVar="nZLLCand")
            self.bookAngles("ZLLCand", self.filler["ZLLCand"])
        
        if self.MELASettings is not None:
            for probHelper in self.probHelpers.values():
                probHelper.bookProbs(wrappedOutputTree)
            
    def bookAngles(self, collName, filler) :
        filler.branch(collName + "_costheta1", "F", limitedPrecision=12)
        filler.branch(collName + "_costheta2", "F", limitedPrecision=12)
        filler.branch(collName + "_Phi", "F", limitedPrecision=12)
        filler.branch(collName + "_costhetastar", "F", limitedPrecision=12)
        filler.branch(collName + "_Phi1", "F", limitedPrecision=12)
                
    def _buildMELAInputs(self, cands, event, leps, fsrPhotons, jets):
        jets_idx = [i for i in (event.JetLeadingIdx, event.JetSubleadingIdx) if i >= 0]
        jets_MELA = Mela.SimpleParticleCollection_t()
        for idx in jets_idx:
            jet = jets[idx]
            p4 = jet.p4()
            jets_MELA.add_particle(Mela.SimpleParticle_t(0, p4.Px(), p4.Py(), p4.Pz(), p4.E()))

        candsDaughters = [Mela.SimpleParticleCollection_t() for _ in cands]
        candsAssociated = [copy.deepcopy(jets_MELA) for _ in cands]

        for iCand, aCand in enumerate(cands):
            theCandLepIdxs = [aCand.Z1l1Idx, aCand.Z1l2Idx, aCand.Z2l1Idx, aCand.Z2l2Idx]
            theCandLeps = [leps[i] for i in theCandLepIdxs]
            dressedLepsp4 = [self.getDressedP4(lep=l, fsrPhotons=fsrPhotons) for l in theCandLeps]
            daughters = candsDaughters[iCand]
            associated = candsAssociated[iCand]
            daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[0].pdgId, dressedLepsp4[0].Px(), dressedLepsp4[0].Py(), dressedLepsp4[0].Pz(), dressedLepsp4[0].E()))
            daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[1].pdgId, dressedLepsp4[1].Px(), dressedLepsp4[1].Py(), dressedLepsp4[1].Pz(), dressedLepsp4[1].E()))
            daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[2].pdgId, dressedLepsp4[2].Px(), dressedLepsp4[2].Py(), dressedLepsp4[2].Pz(), dressedLepsp4[2].E()))
            daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[3].pdgId, dressedLepsp4[3].Px(), dressedLepsp4[3].Py(), dressedLepsp4[3].Pz(), dressedLepsp4[3].E()))

            extralep_idx = [i for i in (aCand.extraLep1Idx, aCand.extraLep2Idx) if i>=0]
            for idx in extralep_idx:
                lep = leps[idx]
                p4 = lep.p4()
                associated.add_particle(Mela.SimpleParticle_t(lep.pdgId, p4.Px(), p4.Py(), p4.Pz(), p4.E()))

        return candsDaughters, candsAssociated

    def analyze(self, event):
        leps = Collection(event, 'Lepton')
        fsrPhotons = Collection(event, "FsrPhoton")
        jets = Collection(event, 'Jet')

        for collName, probHelper in self.probHelpers.items():
            cands = Collection(event, collName)
            theFiller = self.filler[collName]
            candsDaughters, candsAssociated = self._buildMELAInputs(cands, event, leps, fsrPhotons, jets)
            for c in candsDaughters:
                self.MELA.setInputEvent(c, None, None, False)
                qH, mZ1, mZ2, helcosthetaZ1, helcosthetaZ2, helPhi, costhetastar, phistarZ1 = self.MELA.computeDecayAngles() 
                theFiller.appendValue(collName + "_costheta1", helcosthetaZ1)
                theFiller.appendValue(collName + "_costheta2", helcosthetaZ2)
                theFiller.appendValue(collName + "_Phi", helPhi)
                theFiller.appendValue(collName + "_costhetastar", costhetastar)
                theFiller.appendValue(collName + "_Phi1", phistarZ1)
            theFiller.fillBranches(cands)
            if self.MELASettings is not None:
                probHelper.fillProbs(candsDaughters, candsAssociated, None)
        return True

    def getDressedP4(self, lep, fsrPhotons):
        '''Returns the dressed 4-momentum including FSR photon if available'''
        p4 = lep.p4()
        if hasattr(lep, 'fsrPhotonIdx') and lep.fsrPhotonIdx >= 0:
            p4 += fsrPhotons[lep.fsrPhotonIdx].p4()
        return p4
