'''
Replace pT of leptons with up/down scale/smearing syst variations. 
This is intended for specific studies of systematics and not for general usage.
'''
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

class lepScaleShifter(Module):
    def __init__(self, id, var):
        '''
        replace pT of leptons with abs(pdgId)==<id> with the one of syst variation <var>.
        id == 0 -> passthrough (module does nothing)
        '''
        print(f"***lepScaleShifter: id: {id}, var: {var}") 
        if id not in [0, 11, 13] :
            raise ValueError(f"lepScaleShifter: invalid id {id}")
        modes = {"scaleUp" : 0, "scaleDn" : 1, "smearUp": 2, "smearDn": 3}
        if id !=0 :
            try : 
                self.mode = modes[var]
            except :
                raise ValueError(f"lepScaleShifter: invalid var {var}")
        self.id = id
        self.var = var

    
    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        if self.id == 0 :
            return
        elif self.id == 11:
            self.out.branch("Electron_pt", "F", lenVar="nElectron", title=f"pT shifted, {self.var}")
            self.out.branch("Electron_corrected_pt", "F", lenVar="nElectron", title=f"pT (central correction)")
        else :
            self.out.branch("Muon_pt", "F", lenVar="nMuon", title=f"pT shifted, {self.var}")
            self.out.branch("Muon_corrected_pt", "F", lenVar="nMuon", title=f"pT (central correction")
            

    def analyze(self, event):
        if self.id == 0 :
            return True

        elif self.id == 11:
            if event.nElectron == 0 : return True
            self.out.fillBranch("Electron_corrected_pt", event.Electron_pt)
            if self.mode == 0 :
                pts = event.Electron_scaleUp_pt
            elif self.mode == 1 :
                pts = event.Electron_scaleDn_pt
            elif self.mode == 2 :
                pts = event.Electron_smearUp_pt
            elif self.mode == 3 :
                pts = event.Electron_smearDn_pt
            self.out.fillBranch("Electron_pt", pts)
        else :
            if event.nMuon == 0 : return True
            self.out.fillBranch("Muon_corrected_pt", event.Muon_pt)
            if self.mode == 0 :
                pts = event.Muon_scaleUp_pt
            elif self.mode == 1 :
                pts = event.Muon_scaleDn_pt
            elif self.mode == 2 :
                pts = event.Muon_smearUp_pt
            elif self.mode == 3 :
                pts = event.Muon_smearDn_pt
            self.out.fillBranch("Muon_pt", pts)

        return True
