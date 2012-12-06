#!/bin/bash

alttest=jap_glab_brachy.cdna.fa
protein=jap_glab_brachy.pep.fa
rmlib=PReDa_121015_short.fasta
repeat_protein=TE_protein_db_121015_short_header.fasta
snaphmm=O.sativa.hmm

<<<<<<< HEAD
maker -CTL
=======
maker -CTL -c `grep -c "^processor" /proc/cpuinfo`
>>>>>>> 43d28ecea668073691cf03873e045c793f51ab37
python setoption.py maker_opts.ctl alttest $alttest
python setoption.py maker_opts.ctl protein $protein
python setoption.py maker_opts.ctl rmlib $rmlib
python setoption.py maker_opts.ctl repeat_protein $repeat_protein
python setoption.py maker_opts.ctl snaphmm $snaphmm
<<<<<<< HEAD
python setoption.py maker_opts.ctl genome $WORK_FILE
python setoption.py maker_opts.ctl cpus `grep -c "^processor" /proc/cpuinfo`
=======

>>>>>>> 43d28ecea668073691cf03873e045c793f51ab37
if [[ ! ( -f $alttest && -f $protein && -f $rmlib && -f $snaphmm ) ]]; then
	cp /home/ubuntu/maker_constant/* .
else
	echo "Done"
fi
