import Mela
def initializeMELA(runMELA, year): 
    if runMELA == True:
        sqrts = 13. 
        if year >= 2022:
            sqrts = 13.6
        import sys, os
        devnull = os.open(os.devnull, os.O_WRONLY)
        stdout_fd = sys.stdout.fileno()
        saved_stdout = os.dup(stdout_fd)
        os.dup2(devnull, stdout_fd)
        m = Mela.Mela(13.6, 125, Mela.VerbosityLevel.ERROR) 
        m.setCandidateDecayMode(Mela.CandidateDecayMode.CandidateDecay_ZZ)  
        os.dup2(saved_stdout, stdout_fd)
        os.close(devnull)
        os.close(saved_stdout)
        print(f"initializeMELA: created Mela({sqrts:.1f},125,TVar.CandidateDecay_ZZ)", flush=True)
    else: 
        m = None
    return m