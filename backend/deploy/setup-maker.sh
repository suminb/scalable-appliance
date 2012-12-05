#!/bin/bash

python set_options.py maker_opts.ctl alttest jap_glab_brachy.cdna.fa
python set_options.py maker_opts.ctl protein jap_glab_brachy.pep.fa 
python set_options.py maker_opts.ctl rmlib PReDa_121015_short.fasta
python set_options.py maker_opts.ctl repeat_protein TE_protein_db_121015_short_header.fasta
python set_options.py maker_opts.ctl snaphmm O.sativa.hmm
