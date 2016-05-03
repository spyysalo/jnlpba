# JNLPBA

This repository contains tools and resources related to the corpus of the 2004
[BioNLP / JNLPBA shared task](http://www.geniaproject.org/shared-tasks/bionlp-jnlpba-shared-task-2004).

This directory contains JNLPBA corpus data in standoff format and
tools for recreating this data from the TAB-separated BIO format in
which the corpus is distributed.


Contents:

- README.md: this file
- LICENSE: JNLBPA data license
- original-data/ JNLPBA data in BIO format and related resources
- standoff/ JNLBPA data in standoff format
- conversion/ resources for converting JNLPBA data into standoff format


Data sources:

The JNLPBA annotations are available via

    http://www-tsujii.is.s.u-tokyo.ac.jp/GENIA/ERtask/report.html

The original packages were downloaded from

    http://www.nactem.ac.uk/GENIA/current/Shared-tasks/JNLPBA/Train/Genia4ERtraining.tar.gz
    http://www.nactem.ac.uk/GENIA/current/Shared-tasks/JNLPBA/Evaluation/Genia4ERtest.tar.gz

The text files in standoff/train and standoff/test were extracted from
PubMed XML files, downloaded using the NCBI E-utilities
(http://www.ncbi.nlm.nih.gov/books/NBK25499/) as in the following
example

    wget 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=308841&retmode=xml' -O 308841.xml

and title and abstract text content extracted as

    python conversion/extractTIAB.py 308841.xml > 338841.txt

and converted into ASCII using unicode2ascii.py, distributed separately
from https://github.com/spyysalo/unicode2ascii, as

    python unicode2ascii.py 338841.txt > 338841-ASCII.txt

the texts were then semiautomatically processed to align with the
tokens of the JNLPBA data. Three text files were additionally
duplicated under different names (affixing "-2" to file base name) to
account for duplicate IDs in JNLPBA data.

Note that as the JNLBPA data file names are not current PubMed IDs but
rather older MedLine IDs, PubMed queries for the documents (as above)
require mapping between these IDs. The file conversion/MUID-PMID-map.txt 
provides this mapping for the JNLPBA data IDs. This mapping was extracted
from the following files distributed by NLM:

    ftp://ftp.ncbi.nih.gov/pubmed/MuId-PmId-1.zip
    ftp://ftp.ncbi.nih.gov/pubmed/MuId-PmId-2.zip
    ftp://ftp.ncbi.nih.gov/pubmed/MuId-PmId-3.zip
    ftp://ftp.ncbi.nih.gov/pubmed/MuId-PmId-4.zip
    ftp://ftp.ncbi.nih.gov/pubmed/MuId-PmId-5.zip
    ftp://ftp.ncbi.nih.gov/pubmed/MuId-PmId-6.zip


Conversion process

Given the packages Genia4ERtraining.tar.gz and Genia4ERtest.tar.gz and
the text files (.txt) in standoff/train and standoff/test (see Data
sources, above), the standoff annotations (.ann) can be created as
follows (assuming bash shell):

    tar xzf Genia4ERtraining.tar.gz 
    tar xzf Genia4ERtest.tar.gz

    python conversion/jnlpbasplit.py -d standoff/train Genia4ERtask2.iob2
    python conversion/jnlpbasplit.py -d standoff/test Genia4EReval2.iob2 

    for f in standoff/train/*.conll; do  python conversion/jnlpba2standoff.py ${f%.conll}.txt $f > ${f%.conll}.ann; done
    for f in standoff/test/*.conll; do  python conversion/jnlpba2standoff.py ${f%.conll}.txt $f > ${f%.conll}.ann; done

(The last two steps takes some minutes to complete.)
