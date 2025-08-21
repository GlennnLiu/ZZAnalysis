from __future__ import print_function
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

class jetIdUpdate(Module):
    def __init__(self):
        print("***jetIdUpdate", flush=True)

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        # Rename the original Jet_jetId branch
        self.out.branch("Jet_jetIdOriginal", "b", lenVar="nJet", title="Original Jet ID from NanoAOD")
        # Define the new corrected Jet_jetId branch
        self.out.branch("Jet_jetId", "b", lenVar="nJet", title="Corrected Jet ID based on manual recipe for NanoAODv12")
        self.has_jetId=hasattr(inputTree,'Jet_jetId') #FIXME hack while we implement the correctionlib module

    def analyze(self, event):
        jets = Collection(event, 'Jet')
        new_jetId = []
        original_jetId = []

        for ijet, jet in enumerate(jets):
            if self.has_jetId :
                original_jetId.append(jet.jetId)
            else :
                original_jetId.append(0)

            # Initialize Jet ID flags
            Jet_passJetIdTight = False
            Jet_passJetIdTightLepVeto = False

            if not self.has_jetId:
                pass # Will be replaced by a dedicated NATModule

            else:

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
                new_jetId.append(2)
            elif Jet_passJetIdTight and Jet_passJetIdTightLepVeto:
                new_jetId.append(6)
            else:
                new_jetId.append(0)

        # Fill the original and new jet ID branches
        self.out.fillBranch("Jet_jetIdOriginal", original_jetId)
        self.out.fillBranch("Jet_jetId", new_jetId)

        return True
