from __future__ import print_function
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
#from correctionlib._core import CorrectionSet
#from PhysicsTools.NATModules.modules.jetid_from_json import get_jetid_flags
#evaluator = CorrectionSet.from_file("/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/2024_Winter24/jetid.json.gz")


class jetIdUpdate(Module):
    def __init__(self):
        print("***jetIdUpdate", flush=True)

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        # Rename the original Jet_jetId branch
        self.out.branch("Jet_jetIdOriginal", "b", lenVar="nJet", title="Original Jet ID from NanoAOD")
        # Define the new corrected Jet_jetId branch
        self.out.branch("Jet_jetId", "b", lenVar="nJet", title="Corrected Jet ID based on manual recipe for NanoAODv12")

    def analyze(self, event):
        jets = Collection(event, 'Jet')
        new_jetId = []
        original_jetId = []

        for ijet, jet in enumerate(jets):
            #has_jetId = hasattr(jet, 'jetId')
            has_jetId = True # Set to true or the moment until we debug jetid_from_json from NATmodules
            jetid_value = getattr(jet, 'jetId', -1)
            original_jetId.append(jetid_value)

            # Initialize Jet ID flags
            Jet_passJetIdTight = False
            Jet_passJetIdTightLepVeto = False

            if not has_jetId:
                 print(has_jetId)
#                Jet_passJetIdTight, Jet_passJetIdTightLepVeto = get_jetid_flags(jet, jetType="AK4PUPPI")
#                print(f"[INFO] Jet[{ijet}] has no jetId. Using evaluator JSON.", flush=True)
#                nTotalMult = jet.chMultiplicity + jet.neMultiplicity
#                Jet_passJetIdTight = evaluator["AK4PUPPI_Tight"].evaluate(
#                    jet.eta, jet.chHEF, jet.neHEF, jet.chEmEF, jet.neEmEF, jet.muEF, jet.chMultiplicity, jet.neMultiplicity, nTotalMult
#                 )
#                Jet_passJetIdTightLepVeto = evaluator["AK4PUPPI_TightLeptonVeto"].evaluate(
#                    jet.eta, jet.chHEF, jet.neHEF, jet.chEmEF, jet.neEmEF, jet.muEF, jet.chMultiplicity, jet.neMultiplicity, nTotalMult
#                )

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
