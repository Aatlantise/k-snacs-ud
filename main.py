import csv
import stanza
import json
import re
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
                'token_id': row['token_id'],
                'form': row['form'],
                'morph': row['morph'],
                'p': row['p'],
                'gold_scene': row['gold_scene'],
                'gold_function': row['gold_function']
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
    nlp = stanza.Pipeline(lang="ko", processors="tokenize,pos,lemma,depparse", package={"tokenize": "gsd"},
                          tokenize_no_ssplit=True)

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
    korean_char_pattern = re.compile(r'[0-9가-힣]+')
    # Find all Korean character sequences
    korean_chars = korean_char_pattern.findall(mixed_text)
    # Join and return the found Korean characters as a single string
    return ''.join(korean_chars)


def align_original_with_stanza(og_anno, stanza_anno):
    """
    Original annotations with the KOMA tagger do not separate punctuation, while stanza annotations do. Here we map
    KOMA morphemes to stanza heads.

    :param og_anno: original annotations, in JSON format
    :param stanza_anno: stanza annotations, also in JSON format
    :return: JSON object, where original annotation information is added to stanza entries.
    """

    merged_anno = []
    for n_d, [og_doc, stanza_doc] in enumerate(zip(og_anno, stanza_anno)):
        merged_doc = []  # contains merged sentences
        for n_s, [og_sent, stanza_sent] in enumerate(zip(og_doc, stanza_doc)):
            merged_sent = []
            o = 0
            s = 0
            while o < len(og_sent) and s < len(stanza_sent):
                og_morpheme = og_sent[o]
                stanza_morpheme = stanza_sent[s]
                # stanza morpheme is equivalent to og morpheme
                if stanza_morpheme["text"] == og_morpheme["form"]:
                    merged_sent.append({**og_morpheme, **stanza_morpheme})
                    # if next OG entry contains the same morpheme, keep s constant--next OG morpheme also needs
                    # current Stanza parse.
                    # identical_token checks whether next OG token refers to the identical token, to escape cases
                    # like a token 4-2 being followed by token 5-1.
                    if '-' in og_morpheme["token_id"] and '-' in og_sent[o + 1]["token_id"] and \
                            (og_morpheme["token_id"].split('-')[0] == og_sent[o + 1]["token_id"].split('-')[0]):
                        o += 1
                    # otherwise, move to next morpheme
                    else:
                        o += 1
                        s += 1
                # stanza morpheme is head (korean text only) of og morpheme
                elif stanza_morpheme["text"] == just_korean_chars(og_morpheme["form"]):
                    merged_sent.append({**og_morpheme, **stanza_morpheme})
                    # if next OG entry contains the same OG morpheme, just increase o
                    if '-' in og_morpheme["token_id"] and '-' in og_sent[o + 1]["token_id"]:
                        o += 1
                    # if og morpheme ends with stanza morpheme, increase o too, as new morphemes exist for both
                    elif stanza_morpheme["text"] == og_morpheme["form"][-1 * len(stanza_morpheme["text"]):]:
                        s += 1
                        o += 1
                    # otherwise, just move to next stanza morpheme
                    else:
                        s += 1
                # stanza morpheme is part of the head of og token
                elif just_korean_chars(stanza_morpheme["text"]) in just_korean_chars(og_morpheme["form"]):
                    merged_sent.append({**og_morpheme, **stanza_morpheme})
                    s += 1
                    # if stanza morpheme is the final morpheme in og token, move to next og token as well
                    if "misc" not in stanza_morpheme or stanza_morpheme["misc"] != "SpaceAfter=No":
                        o += 1
                # stanza morpheme is non-ending punctuation of og morpheme
                elif stanza_morpheme["text"] in og_morpheme["form"] and \
                        (stanza_morpheme["deprel"] == "punct" or stanza_morpheme["upos"] == "PUNCT" or
                         "pad" in stanza_morpheme["xpos"]) and \
                        "misc" in stanza_morpheme and stanza_morpheme["misc"] == "SpaceAfter=No":
                    merged_sent.append({**og_morpheme, **stanza_morpheme})
                    s += 1
                # stanza morpheme is final punctuation of og morpheme
                elif stanza_morpheme["text"] == og_morpheme["form"][-1 * len(stanza_morpheme["text"]):] and \
                        (stanza_morpheme["deprel"] == "punct" or stanza_morpheme["upos"] == "PUNCT" or
                         "pad" in stanza_morpheme["xpos"]):
                    merged_sent.append({**og_morpheme, **stanza_morpheme})
                    s += 1
                    o += 1
                else:
                    print(f"Location: {n_d}:{n_s}")
                    print(og_morpheme)
                    print(stanza_morpheme)
                    raise ValueError("Something's wrong, man!")
            merged_doc.append(merged_sent)
        merged_anno.append(merged_doc)

    with open("little_prince_merged.json", "w", encoding="utf-8") as f:
        json.dump(merged_anno, f, ensure_ascii=False, indent=4)

    return merged_anno


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
            i_token = 1
            id2nid = {}
            adjusted_sentence = []
            while i < len(sentence):
                # Map id to newly formed id
                id2nid[sentence[i]["id"]] = i_token
                # Could be part of separated elipsis
                if re.fullmatch(r'\.+', sentence[i]["text"]) and i < len(sentence) - 1:
                    # thankfully, elipses seem to be only breaking once
                    if re.fullmatch(r'\.+', sentence[i + 1]["text"]):
                        merged_elipsis_token = {
                            "token_id": sentence[i]["token_id"],
                            "form": sentence[i]["form"],
                            "morph": sentence[i]["morph"],
                            "p": "_",
                            "gold_scene": "_",
                            "gold_function": "_",
                            "id": sentence[i]["id"],
                            "text": sentence[i]["text"] + sentence[i + 1]["text"],
                            "lemma": sentence[i]["lemma"] + sentence[i + 1]["lemma"],
                            "upos": "PUNCT",
                            "xpos": "sf", # should be sf, rather than sl or sr
                            "head": sentence[i]["head"], # take the first head, as the second period often points to the previous elipsis
                            "deprel": sentence[i]["deprel"], # should probably be punct, but there are some artifacts that relates to head too
                            "start_char": sentence[i]["start_char"],
                            "end_char": sentence[i+1]["end_char"]
                        }
                        adjusted_sentence.append(merged_elipsis_token)
                        i_token += 1
                        i += 1
                    i += 1
                # no elipsis in this token
                else:
                    adjusted_sentence.append(sentence[i])
                    i_token += 1
                    i += 1
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

                    adjusted_sentence.append(full_token)

                    if token['p'] != "_":
                        p_node = json.loads(json.dumps(token))
                        p_node['id'] = f"{p_node['id']}-1"
                        p_node['form'] = p_node["p"]
                        p_node["text"] = p_node["p"]
                        p_node["lemma"] = p_node["p"]
                        p_node["upos"] = "ADP"
                        p_node["deprel"] = "case"
                        p_node["start_char"] = token["end_char"] - 1 if token["text"][-1] == p_node["text"] else None
                        p_node["end_char"] = token["end_char"] if token["text"][-1] == p_node["text"] else None
                        p_node["head"] = full_token["id"]
                        del p_node["form"]
                        del p_node["morph"]
                        del p_node["token_id"]
                        # We update the head when the sentence is finished parsing by
                        # using an original_id to new_id map,
                        # since the indices may have shifted due to ellipsis processing

                        # xpos must be r'j[cx][acjmorst]'
                        # Annotate ERROR if:
                        # 1. There are more than 1 postposition tags in unstacked token
                        # 2. There are no postposition tags in token
                        try:
                            xpos_labels = p_node["xpos"].split("+")
                            p_node["xpos"] = xpos_labels[-1] if '-' not in token["token_id"] else [xpos for xpos in xpos_labels if re.match(r'j[cx][acjmorst]', xpos)][0]
                            assert re.match(r'j[cx][acjmorst]', p_node["xpos"])
                        except:
                            p_node["xpos"] = "ERROR"
                            xpos_errors += 1

                        adjusted_sentence.append(p_node)

                else: # second or third stacked postpositions
                    p_node = token

                    ord = p_node['token_id'][-1]
                    p_node['id'] = f"{p_node['id']}-{ord}"
                    p_node['form'] = p_node["p"]
                    p_node["text"] = p_node["p"]
                    p_node["lemma"] = p_node["p"]
                    p_node["upos"] = "ADP"
                    p_node["deprel"] = "case"
                    p_node["start_char"] = token["end_char"] - 1 if token["text"][-1] == p_node["text"] else None
                    p_node["end_char"] = token["end_char"] if token["text"][-1] == p_node["text"] else None
                    p_node["head"] = token["id"]
                    del p_node["form"]
                    del p_node["morph"]
                    del p_node["token_id"]

                    # xpos must be r'j[cx][acjmorst]'
                    # Annotate ERROR if:
                    # 1. Number of xpos labels is less than postposition stack depth (ord)
                    try:
                        xpos_labels = [xpos for xpos in p_node["xpos"].split("+") if re.match(r'j[cx][acjmorst]', xpos)]
                        assert len(xpos_labels) >= int(ord)
                        p_node["xpos"] = xpos_labels[int(ord)]
                    except:
                        p_node["xpos"] = "ERROR"
                        xpos_errors += 1

                    adjusted_sentence.append(p_node)
                i += 1

            adjusted_chapter.append(adjusted_sentence)
        adjusted_doc.append(adjusted_chapter)

    print(f"Encountered {xpos_errors} xpos_errors where annotated postposition was not matched to an xpos tag.")

    with open("little_prince_annotation_ready.json", "w", encoding="utf-8") as f:
        json.dump(adjusted_doc, f, ensure_ascii=False, indent=4)

    return adjusted_doc


if __name__ == "__main__":
    pass
    # original_annotations = read_original_annotation()
    # stanza_annotations = get_stanza_annotation(original_annotations)

    with open("little_prince_ko.json", encoding='utf-8') as f:
        original_annotations = json.load(f)
    with open("little_prince_stanza.json", encoding='utf-8') as f:
        stanza_annotations = json.load(f)

    merged_annotations = align_original_with_stanza(original_annotations, stanza_annotations)
    assert all([len(m_doc) == len(s_doc) for m_doc, s_doc in zip(merged_annotations, stanza_annotations)])

    adjusted_annotations = adjust_token_boundaries(merged_annotations)
