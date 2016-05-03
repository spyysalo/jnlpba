#!/usr/bin/env python

# Split JNLPBA corpus data into single document per file.

# Data available from
#
#    http://www-tsujii.is.s.u-tokyo.ac.jp/GENIA/ERtask/report.html
#
# Given the JNLPBA data, run this script e.g. as
#
#    python jnlpbasplit.py -d train/ Genia4ERtask2.iob2
#    python jnlpbasplit.py -d test/ Genia4EReval2.iob2

import sys
import os
import re

options = None

# regular expression for new document start
NEWDOC_RE = re.compile(r'^###MEDLINE:(\d+)$')

DEFAULT_SUFFIX = 'conll'
DEFAULT_DIR = 'JNLPBA'

def argparser():
    import argparse
    
    ap=argparse.ArgumentParser(description='Split JNLPBA corpus data into ' +
                               'single document per file.')
    ap.add_argument('-s', '--suffix', default=DEFAULT_SUFFIX, metavar='SUFF',
                    help='output file suffix (default ' + DEFAULT_SUFFIX + ')')
    ap.add_argument('-d', '--directory', default=DEFAULT_DIR, metavar='DIR',
                    help='output directory (default ' + DEFAULT_DIR + ')')
    ap.add_argument('-v', '--verbose', default=False, action='store_true', 
                    help='verbose output')    
    ap.add_argument('data', metavar='DATA', nargs=1, 
                    help='JNLPBA data (e.g. Genia4ERtask2.iob2)')
    return ap

def output(lines, PMID):
    global options

    if not lines:
        return False

    assert PMID is not None, 'Missing PMID'

    if PMID not in output.written:
        base = PMID
    else:
        # duplicate PMID; find first numeric affix giving a filename
        # that has not been used.
        i = 2
        while True:
            base = '%s-%d' % (PMID, i)
            if base not in output.written:
                break
            i += 1
        if options.verbose:
            print >> sys.stderr, 'Duplicate PMID %s, writing %s' % (PMID, base)

    fn = os.path.join(options.directory, base+'.'+options.suffix)
    with open(fn, 'wt') as f:
        f.write('\n'.join(lines))
    output.written[base] = True

    return True
output.written = {}

def process(fn):
    with open(fn, 'rU') as f:
        PMID = None
        lines = []
        skipempty = False
        for l in f:
            l = l.rstrip('\n')

            if skipempty:
                assert not l or l.isspace(), \
                    'Missing empty line after PMID %s' % PMID
                skipempty = False
                continue

            m = NEWDOC_RE.match(l)
            if m:
                output(lines, PMID)
                PMID = m.group(1)
                lines = []
                # skip empty following PMID line
                skipempty = True
            else:
                lines.append(l)

        # last doc
        output(lines, PMID)

def main(argv=None):
    global options

    if argv is None:
        argv = sys.argv

    options = argparser().parse_args(argv[1:])

    process(options.data[0])

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
