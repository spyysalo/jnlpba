#!/usr/bin/env python

# Convert JNLPBA data to standoff format with reference to the
# original text.

# This script is a modification of BIOtoStandoff.py, which is part of
# the codebase of brat (http://brat.nlplab.org/) and available from
# https://github.com/nlplab/brat/blob/master/tools/BIOtoStandoff.py
# (BSD license)

from __future__ import with_statement

import sys
import re
import os
import codecs

INPUT_ENCODING='UTF-8'

VERBOSE = False

class taggedEntity:
    def __init__(self, startOff, endOff, eType, idNum, fullText):
        self.startOff = startOff
        self.endOff   = endOff  
        self.eType    = eType   
        self.idNum    = idNum   
        self.fullText = fullText

        self.eText = fullText[startOff:endOff]

    def __str__(self):
        return "T%d\t%s %d %d\t%s" % (self.idNum, self.eType, self.startOff, 
                                      self.endOff, self.eText)

    def check(self):
        # sanity checks: the string should not contain newlines and
        # should be minimal wrt surrounding whitespace
        assert "\n" not in self.eText, \
            "ERROR: newline in entity: '%s'" % self.eText
        assert self.eText == self.eText.strip(), \
            "ERROR: entity contains extra whitespace: '%s'" % self.eText

unescape_map = {
    '``' : '"',
    "''" : '"',
    '.' : ':',   # structured abstract heading, e.g. "METHODS." vs. "METHODS:"
    '--' : ':',  # structured abstract heading, e.g. "METHODS --" vs. "METHODS:"
}

def unescape_align(text, offset, tokentext):
    # attempt unescapes to match text
    for e, u in unescape_map.items():
        if e not in tokentext:
            continue
        candidate = tokentext.replace(e, u)
        if text[offset:offset+len(candidate)] == candidate:
            return candidate, True

    return None, False

def align_token(text, offset, token):
    # attempt to align token with text starting at offset,
    # returning appropriately modified form of token. In case a
    # match cannot be found, return the original form.

    if text[offset:offset+len(token)] == token:
        return token

    if VERBOSE:
        print >> sys.stderr, 'Mismatch: "%s" vs. "%s"' % \
            (text[offset:offset+len(token)], token)

    unescaped, success = unescape_align(text, offset, token)
    if success:
        return unescaped

    # resolve possible space deletions in token
    chars = []
    i, o = 0, offset
    while i < len(token):
        if text[o].isspace() and not token[i].isspace():
            chars.append(text[o])
        else:
            chars.append(token[i])
            i += 1
        o += 1
    respaced = ''.join(chars)
    if respaced != token:
        if VERBOSE:
            print >> sys.stderr, 'Note: respaced "%s" to "%s"' % (token, 
                                                                  respaced)
        token = respaced

    unescaped, success = unescape_align(text, offset, token)
    if success:
        return unescaped

    return token

def find_token_offset(text, offset, token):
    # find token in text starting at offset, returning matching
    # offset. Only skip space and limited other exceptions.
    
    while offset < len(text) and text[offset].isspace():
        offset += 1

    # short-circuit most common case
    if (offset+len(token) <= len(text) and
        text[offset:offset+len(token)] == token):
        return offset

    # check intervening material
    o = text[offset:].find(token)
    
    if o == -1:
        # can't align
        return offset

    skip = text[offset:offset+o]

    if len([c for c in skip if not (c.isspace() or c in ['.'])]) != 0:
        return offset
    else:
        if VERBOSE:
            print >> sys.stderr, 'Skip: "%s"' % skip
        return offset+len(skip)

def find_closing_bracket(BIOlines, line, tokenidx):
    # Returns index of line containing the first closing bracket in
    # the input BIO data starting from the given line, or None if none
    # found. This is a special-purpose method for covering a set of
    # exceptional cases in JNLPBA data.

    firstline = line
    while line < len(BIOlines):
        BIOline = BIOlines[line]

        if re.match(r'^\s*$', BIOline):
            line += 1
        else:
            tokentext = BIOline.split('\t')[tokenidx]
            if tokentext == ']':
                if VERBOSE:
                    print >> sys.stderr, 'Skip bracketed: "%s"' % \
                        ' '.join([l.split('\t')[0] 
                                  for l in BIOlines[firstline:line+1]])
                return line
            line += 1
        
    return None
            

def BIO_to_standoff(BIOtext, reftext, tokenidx=0, tagidx=-1):
    BIOlines = BIOtext.split('\n')
    return BIO_lines_to_standoff(BIOlines, reftext, tokenidx, tagidx)

next_free_id_idx = 1

def BIO_lines_to_standoff(BIOlines, reftext, tokenidx=0, tagidx=-1):
    global next_free_id_idx

    taggedTokens = []

    ri, bi = 0, 0
    while(ri < len(reftext)):
        if bi >= len(BIOlines):
            if VERBOSE:
                print >> sys.stderr, "Warning: received BIO didn't cover given text"
            break

        BIOline = BIOlines[bi]

        if re.match(r'^\s*$', BIOline):
            # the BIO has an empty line (sentence split); skip
            bi += 1
        else:
            # assume tagged token in BIO. Parse and verify
            fields = BIOline.split('\t')

            try:
                tokentext = fields[tokenidx]
            except:
                print >> sys.stderr, "Error: failed to get token text " \
                    "(field %d) on line: %s" % (tokenidx, BIOline)
                raise

            try:
                tag = fields[tagidx]
            except:
                print >> sys.stderr, "Error: failed to get token text " \
                    "(field %d) on line: %s" % (tagidx, BIOline)
                raise

            m = re.match(r'^([BIO])((?:-[A-Za-z0-9_-]+)?)$', tag)
            assert m, "ERROR: failed to parse tag '%s'" % tag
            ttag, ttype = m.groups()

            # strip off starting "-" from tagged type
            if len(ttype) > 0 and ttype[0] == "-":
                ttype = ttype[1:]

            # sanity check
            assert ((ttype == "" and ttag == "O") or
                    (ttype != "" and ttag in ("B","I"))), \
                    "Error: tag/type mismatch %s" % tag

            # find next token in reference
            ri = find_token_offset(reftext, ri, tokentext)

            # possible additional alignment to match reference
            tokentext = align_token(reftext, ri, tokentext)

            # exception: in some cases, the tagged text has "extra"
            # text in brackets, such as the following in 91173312:
            # [published erratum appears in Science 1991 Oct 4;254(5028):11]
            # skip such cases.
            if tokentext == '[' and reftext[ri] != tokentext:
                bi = find_closing_bracket(BIOlines, bi, tokenidx) + 1
                continue
            
            # verify that the text matches the original
            assert reftext[ri:ri+len(tokentext)] == tokentext, \
                'ERROR: text mismatch: reference "%s" tagged "%s"' % \
                (reftext[ri:ri+len(tokentext)].encode("UTF-8"), 
                 tokentext.encode("UTF-8"))

            # store tagged token as (begin, end, tag, tagtype) tuple.
            taggedTokens.append((ri, ri+len(tokentext), ttag, ttype))
            
            # skip the processed token
            ri += len(tokentext)
            bi += 1

            # ... and skip whitespace on reference
            while ri < len(reftext) and reftext[ri].isspace():
                ri += 1

    # check for non-space "leftovers", fail if any alnum
    if len([c for c in reftext[ri:] if not c.isspace()]) != 0:
        extra = reftext[ri:]
        if VERBOSE:
            print >> sys.stderr, 'Leftover text in reference: "%s"' % extra
        assert len([c for c in extra if c.isalnum()]) == 0, 'Error: extra alnum'
            
    if len([c for c in BIOlines[bi:] if not re.match(r'^\s*$', c)]) != 0:
        extra = ' '.join([t.split('\t')[tokenidx] for t in BIOlines[bi:]])
        if VERBOSE:
            print >> sys.stderr, 'Leftover text in tagged: "%s"' % extra
        assert len([c for c in extra if c.isalnum()]) == 0, 'Error: extra alnum'

    standoff_entities = []

    # cleanup for tagger errors where an entity begins with a
    # "I" tag instead of a "B" tag
    revisedTagged = []
    prevTag = None
    for startoff, endoff, ttag, ttype in taggedTokens:
        if prevTag == "O" and ttag == "I":
            print >> sys.stderr, "Note: rewriting \"I\" -> \"B\" after \"O\""
            ttag = "B"
        revisedTagged.append((startoff, endoff, ttag, ttype))
        prevTag = ttag
    taggedTokens = revisedTagged

    # cleanup for tagger errors where an entity switches type
    # without a "B" tag at the boundary
    revisedTagged = []
    prevTag, prevType = None, None
    for startoff, endoff, ttag, ttype in taggedTokens:
        if prevTag in ("B", "I") and ttag == "I" and prevType != ttype:
            print >> sys.stderr, "Note: rewriting \"I\" -> \"B\" at type switch"
            ttag = "B"
        revisedTagged.append((startoff, endoff, ttag, ttype))
        prevTag, prevType = ttag, ttype
    taggedTokens = revisedTagged    

    prevTag, prevEnd = "O", 0
    currType, currStart = None, None
    for startoff, endoff, ttag, ttype in taggedTokens:

        if prevTag != "O" and ttag != "I":
            # previous entity does not continue into this tag; output
            assert currType is not None and currStart is not None, \
                "ERROR in %s" % fn
            
            standoff_entities.append(taggedEntity(currStart, prevEnd, currType, 
                                                  next_free_id_idx, reftext))

            next_free_id_idx += 1

            # reset current entity
            currType, currStart = None, None

        elif prevTag != "O":
            # previous entity continues ; just check sanity
            assert ttag == "I", "ERROR in %s" % fn
            assert currType == ttype, "ERROR: entity of type '%s' continues " \
                "as type '%s'" % (currType, ttype)
            
        if ttag == "B":
            # new entity starts
            currType, currStart = ttype, startoff
            
        prevTag, prevEnd = ttag, endoff

    # if there's an open entity after all tokens have been processed,
    # we need to output it separately
    if prevTag != "O":
        standoff_entities.append(taggedEntity(currStart, prevEnd, currType,
                                              next_free_id_idx, reftext))
        next_free_id_idx += 1

    for e in standoff_entities:
        e.check()

    return standoff_entities

RANGE_RE = re.compile(r'^(-?\d+)-(-?\d+)$')

def parse_indices(idxstr):
    # parse strings of forms like "4,5" and "6,8-11", return list of
    # indices.
    indices = []
    for i in idxstr.split(','):
        if not RANGE_RE.match(i):
            indices.append(int(i))
        else:
            start, end = RANGE_RE.match(i).groups()
            for j in range(int(start), int(end)):
                indices.append(j)
    return indices

def main(argv):
    if len(argv) < 3 or len(argv) > 5:
        print >> sys.stderr, "Usage:", argv[0], "TEXTFILE BIOFILE [TOKENIDX [BIOIDX]]"
        return 1
    textfn, biofn = argv[1], argv[2]

    tokenIdx = None
    if len(argv) >= 4:
        tokenIdx = int(argv[3])
    bioIdx = None
    if len(argv) >= 5:
        bioIdx = argv[4]

    with codecs.open(textfn, 'rU', encoding=INPUT_ENCODING) as textf:
        text = textf.read()
    with codecs.open(biofn, 'rU', encoding=INPUT_ENCODING) as biof:
        bio = biof.read()

    if tokenIdx is None:
        so = BIO_to_standoff(bio, text)
    elif bioIdx is None:
        so = BIO_to_standoff(bio, text, tokenIdx)
    else:
        try:
            indices = parse_indices(bioIdx)
        except:
            print >> sys.stderr, 'Error: failed to parse indices "%s"' % bioIdx
            return 1
        so = []
        for i in indices:
            so.extend(BIO_to_standoff(bio, text, tokenIdx, i))

    for s in so:
        print s

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
