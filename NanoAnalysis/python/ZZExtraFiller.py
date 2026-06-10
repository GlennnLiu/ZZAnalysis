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
from ZZAnalysis.NanoAnalysis.tools import branchCollection, rebuildCandidate
import heapq
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
        self.fillerSR = branchCollection(wrappedOutputTree, lenVar="nZZCand")
        self.bookExtra("ZZCand", self.fillerSR)
        if self.processCR :
            self.fillerCR = branchCollection(wrappedOutputTree, lenVar="nZLLCand")
            self.bookExtra("ZLLCand", self.fillerCR)

    def bookExtra(self, collName, filler) :
        filler.branch(collName+"_nExtraLep", "I",    title="number of extra leptons passing H4l full sel")
        filler.branch(collName+"_extraLep1Idx", "S", title="index of the first extra lepton (ordered by descending pT)")
        filler.branch(collName+"_extraLep2Idx", "S", title="index of the second extra lepton (ordered by descending pT)")
        filler.branch(collName+"_nExtraZ", "I",      title="number of extra Zs passing H4l full sel")

        if self.isMC:
            filler.branch(collName+"_dataMCWeight", "F", title="data/MC efficiency correction weight", limitedPrecision=12)
            if collName=="ZZCand" : #Only for SR for the time being
                filler.branch("ZZCand_escaleUp_mass", "F", title="mass, ele scale up var", limitedPrecision=18) # 18 bits = <0.2 MeV rounding
                filler.branch("ZZCand_escaleDn_mass", "F", title="mass, ele scale dn var", limitedPrecision=18)
                filler.branch("ZZCand_esmearUp_mass", "F", title="mass, ele scale up var", limitedPrecision=18)
                filler.branch("ZZCand_esmearDn_mass", "F", title="mass, ele scale dn var", limitedPrecision=18)
                filler.branch("ZZCand_muscaleUp_mass", "F", title="mass, mu scale up var", limitedPrecision=18)
                filler.branch("ZZCand_muscaleDn_mass", "F", title="mass, mu scale dn var", limitedPrecision=18)
                filler.branch("ZZCand_musmearUp_mass", "F", title="mass, mu scale up var", limitedPrecision=18)
                filler.branch("ZZCand_musmearDn_mass", "F", title="mass, mu scale dn var", limitedPrecision=18)

                
        # Book MELA angle branches. These will have to be moved to RecoProbFiller.
        theLenVar="n"+collName
        self.out.branch(collName + "_costheta1", "F", lenVar=theLenVar, limitedPrecision=12)
        self.out.branch(collName + "_costheta2", "F", lenVar=theLenVar, limitedPrecision=12)
        self.out.branch(collName + "_Phi", "F", lenVar=theLenVar, limitedPrecision=12)
        self.out.branch(collName + "_costhetastar", "F", lenVar=theLenVar, limitedPrecision=12)
        self.out.branch(collName + "_Phi1", "F", lenVar=theLenVar, limitedPrecision=12)

    def analyze(self, event) :
        electrons = Collection(event, "Electron")
        muons = Collection(event, "Muon")
        self.leps = list(electrons) + list(muons)
        self.Zs = Collection(event, 'ZCand')
        self.fsrPhotons = Collection(event, "FsrPhoton")

        self.addExtra('ZZCand', event, self.fillerSR)
        if self.processCR :
            self.addExtra('ZLLCand', event, self.fillerCR)

        return True

    def addExtra(self, collName, event, filler) :
        cands = Collection(event, collName)

        # MELA angle arrays
        helcosthetaZ1s = [-999.] * len(cands)
        helcosthetaZ2s = [-999.] * len(cands)
        helPhis = [-999.] * len(cands)
        costhetastars = [-999.] * len(cands)
        phistarZ1s = [-999.] * len(cands)
        mZ1s = [-999.] * len(cands)
        mZ2s = [-999.] * len(cands)

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
            filler.appendValue(collName+"_nExtraLep", len(extraLeps))
            # Take the two highest-pT additional leptons
            leadingLeps = (heapq.nlargest(2, extraLeps, key=lambda x: self.leps[x].pt) + [-1, -1])[:2]
            filler.appendValue(collName+"_extraLep1Idx", leadingLeps[0])
            filler.appendValue(collName+"_extraLep2Idx", leadingLeps[1])
            filler.appendValue(collName+"_nExtraZ", len(extraZs))

            theCandLeps = [self.leps[i] for i in theCandLepIdxs] 
            if self.isMC:
                filler.appendValue(collName+"_dataMCWeight", self.getDataMCWeight(theCandLeps))
                if collName=="ZZCand" :
                    filler.appendValue("ZZCand_escaleUp_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.scaleUp_pt if abs(l.pdgId)==11 else l.pt)))
                    filler.appendValue("ZZCand_escaleDn_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.scaleDn_pt if abs(l.pdgId)==11 else l.pt)))
                    filler.appendValue("ZZCand_esmearUp_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.smearUp_pt if abs(l.pdgId)==11 else l.pt)))
                    filler.appendValue("ZZCand_esmearDn_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.smearDn_pt if abs(l.pdgId)==11 else l.pt)))
                    filler.appendValue("ZZCand_muscaleUp_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.scaleUp_pt if abs(l.pdgId)==13 else l.pt)))
                    filler.appendValue("ZZCand_muscaleDn_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.scaleDn_pt if abs(l.pdgId)==13 else l.pt)))
                    filler.appendValue("ZZCand_musmearUp_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.smearUp_pt if abs(l.pdgId)==13 else l.pt)))
                    filler.appendValue("ZZCand_musmearDn_mass", self.getVariedM(aCand, self.leps, self.fsrPhotons, lambda l : (l.smearDn_pt if abs(l.pdgId)==13 else l.pt)))

            # Kinematic angles 
            
            dressedLepsp4 = [self.getDressedP4(l, self.fsrPhotons) for l in theCandLeps]
            

            if self.MELA != None: 

                daughters = Mela.SimpleParticleCollection_t()
                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[0].pdgId, dressedLepsp4[0].Px(), dressedLepsp4[0].Py(), dressedLepsp4[0].Pz(), dressedLepsp4[0].E()))
                
                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[1].pdgId, dressedLepsp4[1].Px(), dressedLepsp4[1].Py(), dressedLepsp4[1].Pz(), dressedLepsp4[1].E()))

                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[2].pdgId, dressedLepsp4[2].Px(), dressedLepsp4[2].Py(), dressedLepsp4[2].Pz(), dressedLepsp4[2].E()))

                daughters.add_particle(Mela.SimpleParticle_t(theCandLeps[3].pdgId, dressedLepsp4[3].Px(), dressedLepsp4[3].Py(), dressedLepsp4[3].Pz(), dressedLepsp4[3].E()))
                

                self.MELA.setInputEvent(daughters, None, None, 0)

                qH, mZ1, mZ2, helcosthetaZ1, helcosthetaZ2, helPhi, costhetastar, phistarZ1 = self.MELA.computeDecayAngles() 

                self.MELA.resetInputEvent()

                # Store angles
                helcosthetaZ1s[iCand] = helcosthetaZ1
                helcosthetaZ2s[iCand] = helcosthetaZ2
                helPhis[iCand] = helPhi
                costhetastars[iCand] = costhetastar
                phistarZ1s[iCand] = phistarZ1
                mZ1s[iCand] = mZ1
                mZ2s[iCand] = mZ2
        
        filler.fillBranches(cands)

        # Fill MELA angle branches
        self.out.fillBranch(collName + "_costheta1", helcosthetaZ1s)
        self.out.fillBranch(collName + "_costheta2", helcosthetaZ2s)
        self.out.fillBranch(collName + "_Phi", helPhis)
        self.out.fillBranch(collName + "_costhetastar", costhetastars)
        self.out.fillBranch(collName + "_Phi1", phistarZ1s)

    def getDressedP4(self, lep, fsrPhotons):
        '''Returns the dressed 4-momentum including FSR photon if available'''
        p4 = lep.p4()
        if hasattr(lep, 'fsrPhotonIdx') and lep.fsrPhotonIdx >= 0:
            p4 += fsrPhotons[lep.fsrPhotonIdx].p4()
        return p4
            
    def getDataMCWeight(self, leps) :
        '''Compute lepton efficiency scale factor for the selected leptons'''

        dataMCWeight = 1.
        for lep in leps:
            dataMCWeight *= lep.dataMC        
            
        return dataMCWeight

    def getVariedM(self, cand, leps, fsrPhotons, varied_pt_fun) :
        ret, p4 = rebuildCandidate(cand, leps, fsrPhotons, varied_pt_fun)
        return p4.M() if ret == 0 else -p4.M() # Set as negative is failing kin cuts
