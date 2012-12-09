#!/bin/bash

alttest=jap_glab_brachy.cdna.fa
protein=jap_glab_brachy.pep.fa
rmlib=PReDa_121015_short.fasta
repeat_protein=TE_protein_db_121015_short_header.fasta
snaphmm=O.sativa.hmm

maker -CTL
python setoption.py maker_opts.ctl alttest $alttest
python setoption.py maker_opts.ctl protein $protein
python setoption.py maker_opts.ctl rmlib $rmlib
python setoption.py maker_opts.ctl repeat_protein $repeat_protein
python setoption.py maker_opts.ctl snaphmm $snaphmm
python setoption.py maker_opts.ctl genome $WORK_FILE
python setoption.py maker_opts.ctl cpus `grep -c "^processor" /proc/cpuinfo`

if [[ $WORK_FILE =~ barthii ]]; then
    est=O.barthii_trinity_merged.fasta
    est_gff=O.barthii_WG_merged.gff
    pred_gff=O.barthii.fg.gff3
elif [[ $WORK_FILE =~ brachyantha ]]; then
    est=O.brachyantha_trinity_merged.fasta
    est_gff=O.brachyantha_WG_merged.gff
    pred_gff=O.brachyantha.fg.gff3
elif [[ $WORK_FILE =~ punctata ]]; then
    est=O.punctata_trinity_merged.fasta
    est_gff=O.punctata_WG_merged.gff
    pred_gff=O.punctata.fg.gff3
elif [[ $WORK_FILE =~ japonica ]]; then
    pred_gff=O.japonica.fg.gff3
elif [[ $WORK_FILE =~ indica ]]; then
    pred_gff=O.indica.fg.gff3
else
    echo "Nothing else needed."
fi

python setoption.py maker_opts.ctl est $est
python setoption.py maker_opts.ctl est_gff $est_gff
python setoption.py maker_opts.ctl pred_gff $pred_gff

if [[ ( -z $est && -z $est_gff ) ]]; then
    if [ -f $pred_gff  ]; then
        echo "Variable data already copied."
    else
        cp /home/ubuntu/maker_variable/$pred_gff .
    fi
else
    if [[ !( -f $est && -f $est_gff && -f $pred_gff ) ]]; then
        cp /home/ubuntu/maker_variable/$est .
        cp /home/ubuntu/maker_variable/$est_gff .
        cp /home/ubuntu/maker_variable/$pred_gff .
    else
        echo "Variable data already copied."
    fi
fi

if [[ ! ( -f $alttest && -f $protein && -f $rmlib && -f $snaphmm ) ]]; then
	cp /home/ubuntu/maker_constant/* .
else
    echo "Constant data already copied."
fi

