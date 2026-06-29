#!/bin/tcsh
# #set echo

set opt=$1
set debug=0

if ( $opt == "help" ) then
    echo "Scan production chunks and archive completed ones. Usage:"
    echo "checkProd.csh [option] [goodDir] [badDir]"
    echo "Options: "
    echo " dry = only print, do not archive chunks (default is to move files to AAAOK/)"
    echo " quiet = do not list jobs that are still running"
    echo " mf = move failed jobs to AAAFAIL/"
    echo " lf = link failed jobs (then you can run cleanup.csh; resubmit_Condor.csh in AAAFAIL)" #FIXME to be rechecked if this still works
    echo "[goodDir], [badDir] = folder names to be used instead of AAAOK and AAAFAIL"
    exit
endif

if ( $#argv >= 2 ) then
  set gooddir=$2
else
  set gooddir=AAAOK
endif

if ( $#argv >= 3 ) then
  set baddir=$3
else
  set baddir=AAAFAIL
endif

# Search for chunk -> condor ProcId map file that is written by job creation script
set  idFile = log/ProcIds
if ( ! -e $idFile ) then
    echo "ERROR: $idFile not found"
    exit 1
endif

# Search for condor log, which is a single one for all Chunks, and derive the condor ClusterId
# (cleanup and submit script guarantee there can be only one)
set nonomatch
set logFile = ( log/*.log )
if ( -e $logFile[1] ) then
    set ClusterId = `basename -s .log $logFile[1]`
else
    echo "ERROR: $logFile not found"
    exit 1
endif
unset nonomatch

if ( $debug ) echo "ClusterId: $ClusterId"

foreach chunk ( *Chunk* )
 set fail=0
 set OUTPATH=$chunk

 # Derive ProcId from ProcIds file, with padding of 3 zeroes as in logs
 set tmpstr = ( `grep "^$chunk\ " log/ProcIds` )
# echo $tmpstr
 if ( $? != 0 ) then
    echo "ERROR $chunk not found in log/ProcIds")
    exit 1
 endif
 set ProcId = `printf "%03d" $tmpstr[2]`
 
if ( $debug ) echo "   ${chunk}: ProcId: $ProcId"
 
 # Find out if output was copied to /eos instead than to submit folder 
 if (`grep ^TRANSFER_DIR ${chunk}/batchScript.sh` != "TRANSFER_DIR=" ) then
    set nonomatch
    set outFile = ( ${chunk}/log/*.out )
    if ( -e $outFile[1] ) then
	set OUTPATH=`grep "^Transferring output" $outFile[$#outFile] | sed s/^Transferring\ output\ to:\ //`
    endif
    unset nonomatch
 endif

 # Check that root file is existing and not empty
 set filename=${OUTPATH}/ZZ4lAnalysis.root
 if ( ! -e $filename ) then
   if ( $debug ) echo "   Missing root file in " ${filename}
   set fail=1
 else if ( -z $filename ) then
   if ( $debug ) echo "   Empty file: " $filename
   set fail=1
 endif

 # Check job exit status. Cf. https://twiki.cern.ch/twiki/bin/view/CMSPublic/JobExitCodes , https://twiki.cern.ch/twiki/bin/view/CMSPublic/StandardExitCodes
 set exitStatus = 0
 if ( -es ${OUTPATH}/exitStatus.txt ) then
   set exitStatus=`cat ${OUTPATH}/exitStatus.txt`
   set fail=1
 else if ( ! -e ${OUTPATH}/exitStatus.txt ) then
   set fail=1
 endif

 # Check for failures reported in the Condor log, that would otherwise fail detection
 if ( $exitStatus == 0 ) then 
  if ( -e $logFile[1] ) then
    if ( `grep -e ${ClusterId}\.${ProcId} $logFile[1] | grep -c -e "Job removed.*time exceeded"` != 0 ) then
      set exitStatus=-152
      set fail=1
    else if ( `grep -e ${ClusterId}\.${ProcId} $logFile[1] | grep -c -e "The job attribute PeriodicRemove expression.*evaluated to TRUE"` != 0 ) then
      set exitStatus=-153
      set fail=1
    else if ( `grep -e ${ClusterId}\.${ProcId} $logFile[1] | grep -c -e "Job was aborted"` != 0 ) then
      set exitStatus=-154
      set fail=1
    endif
  endif
 endif

 # Archive succesful jobs, or report failure
 if ( $fail == 0 ) then
  if ( $opt != "dry" ) then 
    mkdir -p $gooddir
    mv $chunk $gooddir/
  endif
 else
  set description=""
   if ( $exitStatus == 0 ) then
     # is the job terminated?
     set nonomatch
     set errFile = ( ${chunk}/log/*.err )
     if ( -e $logFile[1] ) then
        if ( `grep -e ${ClusterId}\.${ProcId} $logFile[1] | grep -c -e "Job terminated"` != 0 ) then
            if ( `grep -c -e "mkdir: cannot create directory '/eos" $errFile[$#errFile]` != 0 ) then
		echo $chunk ": eos transfer problem, see " $errFile[$#errFile]
	    else
		echo $chunk ": terminated, unknown failure"
	    endif
        else if ( $opt != "quiet" ) then
	    echo $chunk ": still running (or unknown failure)"
	endif
     else if ( $opt != "quiet" ) then # this should be no longer possible
	echo $chunk ": still pending (or unknown failure)"
     endif
     unset nonomatch
   else
     if ( $exitStatus == 84 ) set description="(missing input file)"
     if ( $exitStatus == 85 ) set description="(error reading file)"
     if ( $exitStatus == 92 ) set description="(failed to open file)"
     if ( $exitStatus == 134 ) set description="(Crashed)"
     if ( $exitStatus == 137 ) set description="(killed - probably Condor problem)"
     if ( $exitStatus == 152 || $exitStatus == -152) set description="(Exceeded CPU time)"
     if ( $exitStatus == 153 || $exitStatus == -153) set description="(Condor crashed, see log file)"
     if ( $exitStatus == 154 || $exitStatus == -154) set description="(You cancelled the job)"
    echo $chunk ": failed, exit status = " $exitStatus $description
   endif
   if ( $opt == "mf" && $exitStatus != 0 ) then
     mkdir -p $baddir
     mv $chunk $baddir/
   else if ( $opt == "lf" && $exitStatus != 0 ) then
     mkdir -p $baddir
     ln -s ../$chunk $baddir/
     ln -sf ../condor.sub $baddir
   endif
 endif
end
