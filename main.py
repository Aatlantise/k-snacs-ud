import csv
import os

import stanza
import json
import re
from util import p2xpos, decompose_hangul, compose_syllable
from typing import List
from tqdm import tqdm


def parse_tsv(file_path):
    # This will hold all documents
    docs = []

    # Open and read the tsv file
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter='\t')

        current_doc_id = None
        current_sent_id = None
        current_doc = []
        current_sent = []

        # Process each row
        for row in reader:
            # Convert the string ids to integers for comparison
            doc_id = int(row['doc_id'])
            sent_id = int(row['sent_id'])

            # If this is a new document, save the current doc and start a new one
            if current_doc_id is not None and doc_id != current_doc_id:
                docs.append(current_doc)
                current_doc = []
                current_sent = []

            # If this is a new sentence within the current document, save the current sentence and start a new one
            if current_sent_id is not None and sent_id != current_sent_id and current_sent:
                current_doc.append(current_sent)
                current_sent = []

            # Create a dictionary for each word (token) with the word-level information
            word_info = {
                'token_id': row["token_id"],
                'form': row["form"],
                'morph': row["morph"],
                'p': row["p"],
                'gold_scene': row["gold_scene"],
                'gold_function': row["gold_function"]
            }

            # Add the word to the current sentence
            current_sent.append(word_info)

            # Update the document and sentence ids for tracking
            current_doc_id = doc_id
            current_sent_id = sent_id

        # After the loop, add the last sentence and document
        if current_sent:
            current_doc.append(current_sent)
        if current_doc:
            docs.append(current_doc)

    return docs


def read_original_annotation():
    file_path = "little_prince_ko.tsv"
    little_prince = parse_tsv(file_path)
    with open("little_prince_ko.json", "w", encoding='utf-8') as f:
        json.dump(little_prince, f, indent=4, ensure_ascii=False)
    return little_prince


def get_stanza_annotation(og_anno):
    """
    Retrieve Stanza annotation.

    Sentence segmentation is disabled.
    Tokenization using the GSD package, others the KAIST package.

    :param og_anno: original annotations
    :return: stanza annotations
    """
    nlp = stanza.Pipeline(lang="ko", processors="tokenize,pos,lemma,depparse", tokenize_no_ssplit=True)

    sentences_in_raw_text = []
    dd = []
    for d in tqdm(og_anno):
        ss = []  # one document
        _ss = []
        for s in d:
            sentence_text = ' '.join([w['form'] for w in s if w['token_id'][-2:] not in ["-2", "-3"]])
            # There are duplicate entries for stacked postpositions, with -2 and -3 token ids. We do not count those.
            _ss.append(sentence_text)

            parsed = nlp(sentence_text)
            ss += parsed.to_dict()  # parsed.to_dict comes with an extra layer of nested []

        sentences_in_raw_text.append(_ss)
        dd.append(ss)

    with open("little_prince_raw_sentences.json", "w", encoding='utf-8') as f:
        json.dump(sentences_in_raw_text, f, indent=4, ensure_ascii=False)

    with open("little_prince_stanza.json", "w", encoding='utf-8') as f:
        json.dump(dd, f, indent=4, ensure_ascii=False)

    return dd


def just_korean_chars(mixed_text):
    # Regular expression to match only Korean characters (Hangul)
    korean_char_pattern = re.compile(r'[ㄱ-ㅎ가-힣]+')
    # Find all Korean character sequences
    korean_chars = korean_char_pattern.findall(mixed_text)
    # Join and return the found Korean characters as a single string
    return ''.join(korean_chars)


def align_original_with_stanza(og_book, stanza_book):
    """
    Original annotations with the KOMA tagger do not separate punctuation, while stanza annotations do. Here we map
    KOMA tokens to stanza tokens (one to many).

    For example,
    KOMA form "있겠지......>하고" becomes five tokens: "있겠지", ".", ".", ".", ".", ".", ".", ">하고".

    Tokens "." are taken care of in the following adjust_token_boundaries() function.

    This function uses many counters:
        n_chapter: Chapter number id
        n_sent: Sentence number id, inside the chapter
        o: KOMA token id inside sentence
        s: Stanza token id inside sentence

    :param og_book: original annotations, in JSON format
    :param stanza_book: stanza annotations, also in JSON format
    :return: JSON object, where original annotation information is added to stanza entries.
    """

    merged_book = [] # entire annotation book
    for n_chapter, [og_chapter, stanza_chapter] in enumerate(zip(og_book, stanza_book)):
        merged_chapter = []  # contains merged sentences
        og_tokens_in_chapter = [t for s in og_chapter for t in s] # flatten all tokens in og chapter
        o = 0
        for n_sent, stanza_sent in enumerate(stanza_chapter):
            merged_sent = [] # contains merged tokens

            s = 0
            while s < len(stanza_sent):
                og_token = og_tokens_in_chapter[o]
                stanza_token = stanza_sent[s]

                # stanza token is equivalent to og token
                if stanza_token["text"] == og_token["form"]:
                    merged_sent.append({**og_token, **stanza_token})
                    # if next OG entry contains the same token, keep s constant--next OG token also needs
                    # current Stanza parse.
                    # There exists 4 cases '"저녁에는', '"제겐', '"어린아이들만이', '"나에겐' where an og-token with stacked postposition
                    # start with a punct in its form, 0 cases where an og-token with stacked postposition with ends with one.
                    # Check whether next OG token refers to the identical token, to escape cases
                    # like a token 4-2 being followed by token 5-1.
                    if '-' in og_token["token_id"] and '-' in og_tokens_in_chapter[o + 1]["token_id"] and \
                            (og_token["token_id"].split('-')[0] == og_tokens_in_chapter[o + 1]["token_id"].split('-')[0]):
                        o += 1
                    # otherwise, move to next token
                    else:
                        o += 1
                        s += 1
                elif stanza_token["text"] in og_token["form"]: # only partial match
                    og_token_form = og_token["form"]
                    partial_s_tokens_together = ""
                    local_stanza_tokens_list = []

                    # parse through stanza tokens until we cover the entire og token
                    # e.g. parse through stanza tokens: "있겠지", ".", "....", ".", ">하고", corresponding to og token "있겠지......>하고"
                    # This assumes that stanza tokens will respect og sentence boundary
                    while partial_s_tokens_together != og_token_form and s < len(stanza_sent):
                        stanza_token = stanza_sent[s]
                        partial_s_tokens_together += stanza_token["text"]

                        # If p not in stanza token, then remove p and SNACS annotations
                        if adp_in_text(og_token["p"], stanza_token["text"]):
                            local_stanza_tokens_list.append({**og_token, **stanza_token})
                        else:
                            local_stanza_tokens_list.append({**og_token,
                                                             **stanza_token,
                                                             **{"p": "_", "gold_scene": "_", "gold_function": "_"}
                                                             })

                        s += 1
                    # Done parsing.
                    # Now check if next og token is duplicate, in case of stacked postpositions
                    if '-' in og_token["token_id"] and '-' in og_tokens_in_chapter[o + 1]["token_id"] and \
                            (og_token["token_id"].split('-')[0] == og_tokens_in_chapter[o + 1]["token_id"].split('-')[
                                0]):
                        # Yes, duplicate--we do not see any cases where og tokens with stacked tokens end with
                        # punctuation, so we do not care about order
                        # this way, we will always have ["punct", "punct", "main-word-adp-1", "main-word-adp-2"]
                        o += 1
                        og_token = og_tokens_in_chapter[o]
                        local_stanza_tokens_list += [{**og_token, **_s} for _s in local_stanza_tokens_list if _s["upos"] != "PUNCT"]
                    else:
                        # Nothing to do if no stacked postposition
                        pass

                    # add to merged_sent, move to next og and stanza tokens
                    merged_sent += local_stanza_tokens_list
                    # advnace just o since s has been advanced in the while loop parsing through local stanza tokens
                    o += 1

                else: # no match
                    print(json.dumps(og_token, indent=4, ensure_ascii=False))
                    print(json.dumps(stanza_token, indent=4, ensure_ascii=False))
                    print("Something's wrong, man!")
                    s += 1
            merged_chapter.append(merged_sent)
        merged_book.append(merged_chapter)

    with open("little_prince_merged.json", "w", encoding="utf-8") as f:
        json.dump(merged_book, f, ensure_ascii=False, indent=4)

    return merged_book


def adp_in_text(_p, _text):
    k_text = just_korean_chars(_text)
    if not k_text:
        return False

    # Ensure adposition is part of text
    substring_cond = (_p in k_text or
                      _p in k_text[:-1] + compose_syllable(*decompose_hangul(k_text[-1])[:2]) or
                      _p == "에게" and any([_ in k_text for _ in ["내게", "내겐", "네게", "네겐", "제게", "제겐"]]) or
                      _p == "에게서" and any([_ in k_text for _ in ["내게서", "내게선", "네게서", "네게선", "제게서", "제게선"]]) or
                      _p == "이라고" and "라고" in k_text or
                      _p == "이란" and "란" in k_text or
                      _p == "이" and "게" in k_text) # 것이
    bachim_cond = _p in ["ㄴ", "ㄹ"] and any([decompose_hangul(syll)[2] == _p for syll in just_korean_chars(k_text)])
    assimilation_cond = _p in ["의"] and k_text in ["내", "네", "제"]
    p_in_text = (substring_cond or
                 bachim_cond or
                 assimilation_cond)

    return p_in_text

def create_adposition_abstract_node(full_token, _ord: int):
    match_errors = 0
    xpos_errors = 0

    p_node = json.loads(json.dumps(full_token))
    _id = p_node['id'] - 1 if _ord > 1 else p_node['id']
    p_node['id'] = f"{_id}-{_ord}"
    p_node['form'] = p_node["p"]
    p_node["text"] = p_node["p"]
    p_node["lemma"] = p_node["p"]
    p_node["upos"] = "ADP"
    p_node["deprel"] = "_"  # abstract nodes should not have deprel
    p_node["deps"] = f"{p_node['id'].split('-')[0]}:case"
    p_node["head"] = "_"
    if p_node["text"] in full_token["text"]:
        p_node["start_char"] = full_token["start_char"] + full_token["text"].index(p_node["text"])
        p_node["end_char"] = p_node["start_char"] + len(p_node["text"])
    else:  # -ㄴ from 난, -의 from 내
        p_node["start_char"] = "_"
        p_node["end_char"] = "_"
    p_node["head"] = "_"  # not full_token["id"]; abstract nodes should not have deprel
    if "form" in p_node:
        del p_node["form"]
    if "morph" in p_node:
        del p_node["morph"]
    if "token_id" in p_node:
        del p_node["token_id"]

    p, text = p_node["p"], full_token["text"]
    assert adp_in_text(p, text)

    # Check for lemma-xpos length mismatch error and xpos type
    xpos = p_node["xpos"].split("+")
    if len(full_token["lemma"].split("+")) != len(xpos):
        match_errors += 1
        full_token["match_error"] = True
    if not any([re.match(r'j[cx][acjmorst]', xpo) for xpo in xpos]):
        xpos_errors += 1
        full_token["xpos_error"] = True

    # Use the p to xpos table for XPOS.
    p_node["xpos"] = p2xpos(p_node["p"], p_node["gold_function"])
    return p_node, match_errors, xpos_errors


def adjust_token_boundaries(merged_anno):
    """
    Here, we adjust token boundaries by performing two tasks.

     1. join separated ellipses: ....(SE) + .(SF) -> .....(SE)
     2. duplicate postpositions as additional node: 마리만 -> 마리만(NNB+JXC) + 만(JXC)

    :param merged_anno: Merged annotations
    :return: Boundary adjusted annotations
    """

    # First, we join separated ellipses
    _adjusted_doc = []
    for chapter in merged_anno:
        adjusted_chapter = []
        for sentence in chapter:
            i = 0
            new_index = 1
            id2nid = {}
            adjusted_sentence = []
            while i < len(sentence):
                # Map id to newly formed id
                # Could be part of separated elipsis
                if sentence[i]["text"] == "." and i < len(sentence) - 1:
                    # check if elipsis, and length of elipsis if yes
                    j = 1
                    while i + j < len(sentence):
                        if sentence[i + j]["text"] == ".":
                            j += 1
                            continue
                        else:
                            break

                    # sentence[i:i+j] is ellipsis
                    merged_period_or_ellipsis_token = {
                            "token_id": sentence[i]["token_id"],
                            "form": sentence[i]["form"],
                            "morph": sentence[i]["morph"],
                            "p": "_",
                            "gold_scene": "_",
                            "gold_function": "_",
                            "id": new_index,
                            "text": ''.join([p["text"] for p in sentence[i:i + j]]),
                            "lemma": ''.join([p["lemma"] for p in sentence[i:i + j]]),
                            "upos": "PUNCT",
                            "xpos": "sf", # should be sf, rather than sl or sr
                            "head": sentence[i]["head"], # take the first head, as the second period often points to the previous elㅣipsis
                            "deprel": sentence[i]["deprel"], # should probably be punct, but there are some artifacts that relates to head too
                            "start_char": sentence[i]["start_char"],
                            "end_char": sentence[i + j - 1]["end_char"]
                        }

                    adjusted_sentence.append(merged_period_or_ellipsis_token)
                    id2nid[sentence[i]["id"]] = new_index
                    i += j
                    new_index += 1

                elif "-2" in sentence[i]["token_id"] or "-3" in sentence[i]["token_id"]:
                    token_with_new_index = {**sentence[i], "id": new_index} # use previous index, as it represents the same token
                    adjusted_sentence.append(token_with_new_index)
                    id2nid[sentence[i]["id"]] = new_index

                    i += 1
                    # do not increase index, as it was already increased before entering this stacked adp token
                    new_index += 0

                # no elㅣipsis in this token
                else:
                    token_with_new_index = {**sentence[i], "id": new_index}
                    adjusted_sentence.append(token_with_new_index)
                    id2nid[sentence[i]["id"]] = new_index
                    i += 1
                    new_index += 1

            # We update the head when the sentence is finished parsing by
            # using an original_id to new_id map,
            # since the indices may have shifted due to ellipsis processing
            for adj_token in adjusted_sentence:
                if adj_token['head'] == 0: # root stays root
                    pass
                else:
                    adj_token['head'] = id2nid[adj_token['head']]
            adjusted_chapter.append(adjusted_sentence)
        _adjusted_doc.append(adjusted_chapter)

    # Then, duplicate the postpositions
    # If single postposition, duplicate the postposition to produce one additional node
    # If stacked postposition, duplicate each postposition to produce one additional node per stacked postposition
    # Postposition annotations are made at the additional postposition node
    adjusted_doc = []
    xpos_errors = 0
    match_errors = 0
    for chapter in _adjusted_doc:
        adjusted_chapter = []
        for sentence in chapter:
            i = 0
            adjusted_sentence = []
            while i < len(sentence):
                token = sentence[i]
                if '-' not in token['token_id'] or '-1' in token['token_id']:
                    # Add token and postposition if it exists
                    full_token = json.loads(json.dumps(token)) # deepcopy
                    full_token['p'] = "_"
                    full_token["gold_scene"] = "_"
                    full_token["gold_function"] = "_"
                    del full_token["form"]
                    del full_token["morph"]
                    del full_token["token_id"]

                    if token['p'] != "_" and token["upos"] not in ["PUNCT"]:
                        p_node, _match_errors, _xpos_errors = create_adposition_abstract_node(token, 1)
                        match_errors += _match_errors
                        xpos_errors += _xpos_errors


                        # Add to sentence (list of tokens)
                        adjusted_sentence.append(full_token)
                        adjusted_sentence.append(p_node)
                    else:
                        adjusted_sentence.append(full_token)

                else:
                    # Pseudo-token for marking second or third stacked postposition
                    # We do not have access to head token id, so we use the first part of the pseudo-token id
                    # e.g. map id = "1-2" to id = 1
                    p_node = json.loads(json.dumps(token))

                    _ord = int(p_node['token_id'][-1])
                    p_node, _match_errors, _xpos_errors = create_adposition_abstract_node(token, _ord)

                    adjusted_sentence.append(p_node)
                i += 1

            adjusted_chapter.append(adjusted_sentence)
        adjusted_doc.append(adjusted_chapter)

    print(f"Encountered {xpos_errors} xpos_errors, {match_errors} match_errors.")

    with open("little_prince_annotation_ready.json", "w", encoding="utf-8") as _f:
        json.dump(adjusted_doc, _f, ensure_ascii=False, indent=4)

    return adjusted_doc


if __name__ == "__main__":
    original_annotations = read_original_annotation()
    stanza_annotations = get_stanza_annotation(original_annotations)

    # with open("little_prince_ko.json", encoding='utf-8') as f:
    #     original_annotations = json.load(f)
    # with open("little_prince_stanza.json", encoding='utf-8') as f:
    #     stanza_annotations = json.load(f)

    merged_annotations = align_original_with_stanza(original_annotations, stanza_annotations)

    # with open("little_prince_merged.json", encoding='utf-8') as f:
    #     merged_annotations = json.load(f)
    assert all([len(m_doc) == len(s_doc) for m_doc, s_doc in zip(merged_annotations, stanza_annotations)])

    adjusted_annotations = adjust_token_boundaries(merged_annotations)
