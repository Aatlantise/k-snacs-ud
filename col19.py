#!/usr/bin/env python3
# coding=utf-8

import sys

# BIO symbols
I_BAR, I_TILDE, i_BAR, i_TILDE = 'I_', 'I~', 'i_', 'i~'

# ------------------------------
# BIO tagging function
# ------------------------------
def sent_tags(token_ids, smwe_groups, wmwe_groups):
    tagging = {}
    parents = {}
    gapstrength = {}

    # Strong MWEs
    for grp in smwe_groups:
        g = sorted(grp)
        skip = False
        for i, j in zip(g[:-1], g[1:]):
            if j > i+1 and i in gapstrength:
                skip = True
                break
        if skip: continue
        for i, j in zip(g[:-1], g[1:]):
            if j not in parents:
                parents[j] = (i, '_')
            if j > i+1:
                for h in range(i+1, j):
                    gapstrength[h] = '_'

    # Weak MWEs
    for grp in wmwe_groups:
        g = sorted(grp)
        skip = False
        for i in g:
            if i in gapstrength and any(j for j in g if j not in gapstrength):
                skip = True
                break
        if skip: continue
        for i, j in zip(g[:-1], g[1:]):
            if j not in parents:
                parents[j] = (i, '~')
            if j > i+1:
                for h in range(i+1, j):
                    gapstrength.setdefault(h, '~')

    all_parents = set([p for p, s in parents.values()]) if parents else set()

    for tid in token_ids:
        parent, strength = parents.get(tid, (0, ''))
        amInGap = (tid in gapstrength)
        if parent == 0:
            if tid in all_parents:
                tag = 'b' if amInGap else 'B'
            else:
                tag = 'o' if amInGap else 'O'
        elif strength == '_':
            tag = i_BAR if amInGap else I_BAR
        else:
            tag = i_TILDE if amInGap else I_TILDE
        tagging[tid] = tag

    return tagging


# ------------------------------
# Read CoNLL-U-Lex
# ------------------------------
def read_conllu_lex(filepath):
    sentences = []
    sent = {'toks': [], 'smwes': {}, 'wmwes': {}, 'anno': ''}
    smwe_map, wmwe_map = {}, {}
    with open(filepath, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                if sent['toks']:
                    sentences.append(sent)
                sent = {'toks': [], 'smwes': {}, 'wmwes': {}, 'anno': ''}
                smwe_map, wmwe_map = {}, {}
                continue
            if line.startswith("#"):
                sent['anno'] += line + '\n'
                continue

            cols = line.split('\t')
            if len(cols) < 19:
                cols.extend(['_'] * (19 - len(cols)))

            idx = cols[0]
            try:
                idx_int = int(float(idx))
            except ValueError:
                continue

            tok = {
                '#': idx,
                'idx_int': idx_int,
                'form': cols[1],
                'smwe': None,
                'wmwe': None,
                'lexcat': cols[12],
                'ss': None if cols[13] == '_' else cols[13],
                'ss2': None if cols[14] == '_' else cols[14],
                'lextag': None,
                'cols': cols
            }

            # Parse SMWE
            if cols[10] != '_':
                parts = cols[10].split(":")
                try:
                    num = int(parts[0])
                    pos = int(parts[1]) if len(parts) > 1 and parts[1] != '_' else 1
                    tok['smwe'] = (num, pos)
                    smwe_map.setdefault(num, {'toknums': []})
                    smwe_map[num]['toknums'].append(idx_int)
                    sent['smwes'] = smwe_map
                except ValueError:
                    tok['smwe'] = None

            # Parse WMWE
            if cols[11] != '_':
                parts = cols[11].split(":")
                try:
                    num = int(parts[0])
                    pos = int(parts[1]) if len(parts) > 1 and parts[1] != '_' else 1
                    tok['wmwe'] = (num, pos)
                    wmwe_map.setdefault(num, {'toknums': []})
                    wmwe_map[num]['toknums'].append(idx_int)
                    sent['wmwes'] = wmwe_map
                except ValueError:
                    tok['wmwe'] = None

            sent['toks'].append(tok)

    if sent['toks']:
        sentences.append(sent)
    return sentences


# ------------------------------
# Populate LEXTAG with optional debug
# ------------------------------
def populate_lextags(sent, debug=False):
    smwe_groups = [g['toknums'] for g in sent['smwes'].values()]
    wmwe_groups = [g['toknums'] for g in sent['wmwes'].values()]
    if not sent['toks']:
        return

    token_ids = sorted(tok['idx_int'] for tok in sent['toks'])
    tags_dict = sent_tags(token_ids, smwe_groups, wmwe_groups)

    for tok in sent['toks']:
        tid = tok['idx_int']
        tag = tags_dict.get(tid, 'O')
        full_tag = tag

        append_info = tok['smwe'] is None or tok['smwe'][1] == 1
        if append_info:
            if tok['lexcat'] != '_':
                full_tag += '-' + tok['lexcat']
            if tok['ss']:
                full_tag += '-' + tok['ss']
                if tok['ss2'] and tok['ss2'] != tok['ss']:
                    full_tag += '|' + tok['ss2']

        if tok['wmwe']:
            wmwe_num, pos = tok['wmwe']
            if pos == 1:
                wcat = tok['cols'][15]
                if wcat != '_':
                    full_tag += '+' + wcat

        tok['lextag'] = full_tag

        if debug:
            print(f"Token ID={tok['#']}, FORM={tok['form']}, SMWE={tok['smwe']}, WMWE={tok['wmwe']}, "
                  f"LEXCAT={tok['lexcat']}, SS={tok['ss']}, SS2={tok['ss2']}, LEXTAG={tok['lextag']}")


# ------------------------------
# Write CoNLL-U-Lex
# ------------------------------
def write_conllu_lex(sentences, outfile):
    with open(outfile, 'w', encoding='utf-8') as f:
        for sent in sentences:
            for tok in sent['toks']:
                cols = tok['cols']
                if len(cols) < 19:
                    cols.extend(['_'] * (19 - len(cols)))
                cols[18] = tok['lextag'] if tok['lextag'] else '_'
                f.write('\t'.join(cols) + '\n')
            f.write('\n')


# ------------------------------
# Main
# ------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python populate_lextag.py input.conllu-lex output.conllu-lex [--debug]")
        sys.exit(1)

    infile = sys.argv[1]
    outfile = sys.argv[2]
    debug = '--debug' in sys.argv

    sentences = read_conllu_lex(infile)
    for sent in sentences:
        populate_lextags(sent, debug=debug)
    write_conllu_lex(sentences, outfile)
