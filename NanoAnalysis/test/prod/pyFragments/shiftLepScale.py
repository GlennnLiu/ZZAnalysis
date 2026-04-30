from ZZAnalysis.NanoAnalysis.tools import setConf, getConf, insertBefore
from ZZAnalysis.NanoAnalysis.lepScaleShifter import *

# Note: scaleShiftId and scaleShiftVar should be defined externally; by default, this module does not apply any shift.
def customizeForScaleShift_(p) :
    insertBefore(p.modules, 'lepFiller', lepScaleShifter(getConf("scaleShiftId", 0),getConf("scaleShiftVar", None)))

setConf("customizations", customizeForScaleShift_, append=True) 
