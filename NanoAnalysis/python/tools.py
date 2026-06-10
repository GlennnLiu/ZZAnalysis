### Various helper funcions
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

## handle configuration variables
_myConf = {}

def getConf(name,default=None):
    global _myConf
    return _myConf[name] if name in _myConf else default

def setConf(name,value=True, append=False):
    global _myConf
    if append == True :
        if name in _myConf :
            if type(_myConf[name]) == list :
                _myConf[name].append(value)
            else :
                print(f"ERROR setConf: cannot append to variable {name}, since it is not a list")
                exit(1)
        else :
            _myConf[name] = [value]
    else : # replace value, if already set
        _myConf[name] = value

# Insert a module in a processing sequence before the specified module
def insertBefore(sequence, moduleName, module) :
    if type(moduleName)!=str :
        raise ValueError("insertBefore: moduleName should be a string")
    for im, m in enumerate(sequence) :
        if type(m).__name__ == moduleName :
            sequence.insert(im, module)
            return


# Insert a module in a processing sequence after the specified module
def insertAfter(sequence, moduleName, module) :
    if type(moduleName)!=str :
        raise ValueError("insertAfter: moduleName should be a string")
    for im, m in enumerate(sequence) :
        if type(m).__name__ == moduleName :
            sequence.insert(im+1, module)
            return

# Remove a module in a sequence
def removeModule(sequence, moduleName) :
    if type(moduleName)!=str :
        raise ValueError("insertAfter: moduleName should be a string")
    for im, m in enumerate(sequence) :
        if type(m).__name__ == moduleName :
            del sequence[im]
        
# Get the four leptons of a ZZ or ZLL candidate
def getLeptons(aCand, event) :
    idxs = [aCand.Z1l1Idx, aCand.Z1l2Idx, aCand.Z2l1Idx, aCand.Z2l2Idx]
    electrons = Collection(event, "Electron")
    muons = Collection(event, "Muon")
    leps = list(electrons) + list(muons)
    return [leps[i] for i in idxs]

def Mother(part, gen):
    '''
        Find the ID and Idx of the mother of a given GenPart (`part`)
        amongst all the particles in GenPart (`gen`) collection.
        The function returns Idx and ID of the mother.
    '''
    idxMother= part.genPartIdxMother
    while idxMother>=0 and gen[idxMother].pdgId == part.pdgId:
        idxMother = gen[idxMother].genPartIdxMother
    idMother=0
    if idxMother >=0 : idMother = gen[idxMother].pdgId
    return idxMother, idMother

def getParentID(part, gen) :
    '''
        Return the ID of the leptons's parent:
        25 for H->Z->l; 23 for Z->l; +-15 for
        tau->l if genlep is e,mu.
    '''
    pIdx, pID = Mother(part, gen)
    if pIdx < 0 : return 0
    ppIdx = gen[pIdx].genPartIdxMother
    if pID == 23 and ppIdx>=0 and gen[ppIdx].pdgId == 25 :
        pID = 25
    return pID

def get_genEventSumw(input_file, maxEntriesPerSample=None):
    '''
       Util function to get the sum of weights per event.
       Returns the sum of weights, similarly to what we
       stored in Counters->GetBinContent(40) in the miniAODs.
    '''
    f = input_file

    runs  = f.Runs
    event = f.Events
    nRuns = runs.GetEntries()
    nEntries = event.GetEntries()

    iRun = 0
    genEventCount = 0
    genEventSumw = 0.

    while iRun < nRuns and runs.GetEntry(iRun) :
        genEventCount += runs.genEventCount
        genEventSumw += runs.genEventSumw
        iRun +=1
    print ("gen=", genEventCount, "sumw=", genEventSumw)

    if maxEntriesPerSample is not None:
        print(f"Scaling to {maxEntriesPerSample} entries")
        if nEntries>maxEntriesPerSample :
            genEventSumw = genEventSumw*maxEntriesPerSample/nEntries
            nEntries=maxEntriesPerSample
        print("    scaled to:", nEntries, "sumw=", genEventSumw)

    return genEventSumw

# Return efficiency and asymmetric (up, down) errors for sel over tot events
def getEff(tot, sel):
    from ROOT import TEfficiency
    eff = sel/tot
    up = TEfficiency.ClopperPearson(tot, sel, 0.683, True)
    dn = TEfficiency.ClopperPearson(tot, sel, 0.683, False)
    return eff, up-eff, eff-dn

# Define a set of branches to be booked and filled for a collection
class branchCollection():
    def __init__(self, wrappedOutputTree, lenVar=None, title=None) :
        """Helper to book and fill a set of branches for a collection. 
        Arguments: 
           lenVar = variable wich holds the collection lenght
           title = documentation string for the collection
        """
        self.out = wrappedOutputTree
        self.branchNames = []
        self.getters = []
        self.buffers = {}
        self.lenVar = lenVar
        if title is not None : # Needs to be booked explicitly only to set the title
            self.out.branch(lenVar, "I", title=title)

    def branch(self, name, rootBranchType, getter = None, title = None, limitedPrecision = False) :
        """Define a branch to be filled. 
        Parameters:
           getter: lambda that will be used to extract the value vor variable 'name'. if None, a buffer will be used instead, either internally managed if set(name, value) is called for each variable and object, or explicitly handled getBuffer(name, n, default), which is slightly more efficient.
           title: documentation string
        """
        self.out.branch(name, rootBranchType, lenVar=self.lenVar, title=title, limitedPrecision=limitedPrecision)
        self.branchNames.append(name)
        self.getters.append(getter)
        self.buffers[name] = []

    def getBuffer(self, name, n, default=None):
        """Get a pre-allocated buffer for manual filling. 
        Call once per event before filling."""
        self.buffers[name] = [default] * n
        return self.buffers[name]
        
    def appendValue(self, name, value) :
        """Set value in the buffer for variable <name>. 
        Called once per collection element. Note this has a larger overhead than using getBuffer() because of per-element dictionary lookup and dynamic reallocation due to append()"""
        self.buffers[name].append(value)
        
    def fillBranches(self, collection) :
        """Fill all branches with one entry per item in collection"""
        for i, name in enumerate(self.branchNames) :
            getter = self.getters[i]
            if getter is not None:
                vals = [getter(item) for item in collection]
            else :
                vals = self.buffers[name]
                if len(vals) != len(collection):
                    raise RuntimeError(
                        f"Buffer length mismatch for branch '{name}': "
                        f"expected {len(collection)}, got {len(self.buffers[name])}. "
                    )
            self.out.fillBranch(name, vals)
            vals.clear()


def getZaZb(zzleps, p4s) :
    """build Za/Zb alternative pairing used in 'smart cut'"""
    if zzleps[0].pdgId == -zzleps[2].pdgId :
        mZa = (p4s[0]+p4s[2]).M()
        mZb = (p4s[1]+p4s[3]).M()
    elif zzleps[0].pdgId == -zzleps[3].pdgId :
        mZa = (p4s[0]+p4s[3]).M()
        mZb = (p4s[1]+p4s[2]).M()
    if (abs(mZa-91.1876)>abs(mZb-91.1876)) : mZa, mZb = mZb, mZa
    return mZa, mZb

            
def rebuildCandidate(aCand, leps, fsr, varied_pt_fun=None, checkPassCuts=True, debug=False):
    """Recompute the p4 of the candidate using a scale/smearing variation for pT. Example for varied_pt_fun for ele scale up:
    lambda l : (l.scaleUp_pt if abs(l.pdgId)== 11 else l.pt)
    The varied candidate is tested for failing cuts; first return value !=0 indicates which cut failed.
    """
    idxs = [aCand.Z1l1Idx, aCand.Z1l2Idx, aCand.Z2l1Idx, aCand.Z2l2Idx]
    pts=[None]*4
    p4s=[None]*4
    dressedp4s=[None]*4
    candLeps =[None]*4
    for i, idx in enumerate(idxs) :
        candLeps[i] = l = leps[idx]
        pts[i] = pt = varied_pt_fun(l)
        p4s[i] = p4 = l.p4(pt)
        if l.fsrPhotonIdx>=0 :
            dressedp4s[i] = p4 + fsr[l.fsrPhotonIdx].p4()
        else : 
            dressedp4s[i] = p4

    p4Z1 = dressedp4s[0]+dressedp4s[1]
    p4Z2 = dressedp4s[2]+dressedp4s[3]
    p4ZZ = p4Z1+p4Z2

    if checkPassCuts==False:
        return 0, p4ZZ

    ### Check if candidate still pass cuts
    # test pT thresholds
    npt20 = 0;
    npt10 = 0;
    for il, l in enumerate(candLeps) :
        if (abs(l.pdgId)==11 and pts[il]<7.) or pts[il]<5: 
            if debug: print(f" Below pT threshold : {l.pdgId}, {pts[il]} -> {l.pt}")
            return 1, p4ZZ
        if pts[il] > 20 : npt20+=1
        if pts[il] > 10 : npt10+=1
    if npt20<1 or npt10<2 :
        if debug: print(f" fail pt20, 10 cut")
        return 2, p4ZZ

    # test mass windows
    if p4Z1.M() <40. or p4Z1.M()>120. :
        if debug: print(f" Z1 outside mass window: {p4Z1.M()}")
        return 3, p4ZZ
    if p4Z2.M() <12. or p4Z2.M()>120. :
        if debug: print(f" Z2 outside mass window: {p4Z2.M()}")
        return 4, p4ZZ

    # Test QCD suppression on undressed leptons
    for k in range(4):
        for l in range (k+1,4):             
            if candLeps[k].charge!=candLeps[l].charge and (p4s[k]+p4s[l]).M()<=4.:
                fail = True
                if debug: print(f" fail QCD cut {(p4s[k]+p4s[l]).M()}")
                return 5, p4ZZ

    # Test "smart cut"
    if aCand.Z1flav == aCand.Z2flav :
        mZa, mZb = getZaZb(candLeps, dressedp4s)
        
        if (abs(mZa-91.1876)<abs(p4Z1.M()-91.1876)) and mZb < 12.:
            dressedp4s_orig=[None]*4
            for i, idx in enumerate(idxs) :
                l = leps[idx]
                dressedp4s_orig[i] = l.p4()
                if l.fsrPhotonIdx>=0 :
                    dressedp4s_orig[i] += fsr[l.fsrPhotonIdx].p4()
            if debug: print(f" fail smart cut: mZa: {mZa} mZ1: {p4Z1.M()}, mZb: {mZb}")
            return 6, p4ZZ

    # Other cuts that are not tested: 
    # - deltaR cut, cannot be affected by scale/smear
    # - variation of relative isolation (l.combRelIsoPFFSRCorr < 0.35) for mu
    # - variation of ele ID since MVA cuts are pt-dependent (the original pT should be used in principle anyhow)
    # - different FSR-lepton association due to leptons moving in/out of acceptance (should be extremely rare)

    return 0, p4ZZ
