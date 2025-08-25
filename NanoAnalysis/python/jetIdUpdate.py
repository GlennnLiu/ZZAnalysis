"""
This module recomputes the JetId as recommended for nanoAODv12 based on the example:
https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetID13p6TeV#nanoAOD_Flags
For nanoAODv13 and later, the correctionlib-based module should be used instead (see python/modules/jetIdProducer.py)
"""
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from array import array

class jetIdUpdate(Module):
    def __init__(self):
        print("***jetIdUpdate", flush=True)

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.has_jetId=hasattr(inputTree,'Jet_jetId')
        # Define the new corrected Jet_jetId branch. "b" = UChar_t in ROOT
        self.out.branch("Jet_jetId", "b", lenVar="nJet", title="Corrected Jet ID based on manual recipe for NanoAODv12")
        if self.has_jetId:
            # Rename the original Jet_jetId branch
            self.out.branch("Jet_jetIdOriginal", "b", lenVar="nJet", title="Original Jet ID from NanoAOD")

    def analyze(self, event):
        jets = Collection(event, 'Jet')
        new_jetId = array('B', event.nJet*[0]) # Note: UChar_t is uppercase 'B' in python array
        original_jetId = array('B', event.nJet*[0])

        for ijet, jet in enumerate(jets):
            if self.has_jetId :
                original_jetId[ijet] = jet.jetId

            # Initialize Jet ID flags
            Jet_passJetIdTight = False
            Jet_passJetIdTightLepVeto = False

            # Jet-passJetIdTight based on eta conditions
            if abs(jet.eta) <= 2.7:
                Jet_passJetIdTight = bool(jet.jetId & (1 << 1))
            elif 2.7 < abs(jet.eta) <= 3.0:
                Jet_passJetIdTight = bool(jet.jetId & (1 << 1)) and (jet.neHEF < 0.99)
            elif abs(jet.eta) > 3.0:
                Jet_passJetIdTight = bool(jet.jetId & (1 << 1)) and (jet.neEmEF < 0.4)

            # Jet-passJetIdTightLepVeto based on additional lepton veto conditions
            if abs(jet.eta) <= 2.7:
                Jet_passJetIdTightLepVeto = Jet_passJetIdTight and (jet.muEF < 0.8) and (jet.chEmEF < 0.8)
            else:
                Jet_passJetIdTightLepVeto = Jet_passJetIdTight

            # Determine the new jet ID
            if Jet_passJetIdTight and not Jet_passJetIdTightLepVeto:
                new_jetId[ijet] = 2
            elif Jet_passJetIdTight and Jet_passJetIdTightLepVeto:
                new_jetId[ijet] = 6
            else:
                new_jetId[ijet] = 0

        # Fill the original and new jet ID branches
        self.out.fillBranch("Jet_jetId", new_jetId)
        if self.has_jetId :
            self.out.fillBranch("Jet_jetIdOriginal", original_jetId)

        return True
