#!/bin/tcsh

set nonomatch
set list = ( */*.root */*.corrupted */*.recovered */*.gz */*.txt */core* */jobid  */LSFJOB*/ */log/* */output/* */error/* */*.DAT */*.cc */br.sm?)

foreach f ( ${list} )
    if ( -e $f ) then
	rm -r $f
    endif
end

if ( -d log/ ) then
    set logFile = ( log/*.log )
    if ( -e $logFile[1] ) then
	set ClusterId = `basename -s .log $logFile[1]`
	mv  $logFile[1]  $logFile[1].bak
	mv log/ProcIds log/ProcIds.$ClusterId
endif
