import csv
import stanza
import json
import re
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
        json.dump(merged_anno, f, ensure_ascii=False)

    return merged_anno


if __name__ == "__main__":
    # original_annotations = read_original_annotation()
    # stanza_annotations = get_stanza_annotation(original_annotations)

    with open("little_prince_ko.json", encoding='utf-8') as f:
        original_annotations = json.load(f)
    with open("little_prince_stanza.json", encoding='utf-8') as f:
        stanza_annotations = json.load(f)

    merged_annotations = align_original_with_stanza(original_annotations, stanza_annotations)
    assert all([len(m_doc) == len(s_doc) for m_doc, s_doc in zip(merged_annotations, stanza_annotations)])

    with open("little_prince_merged.json", 'w', encoding='utf-8') as f:
        json.dump(merged_annotations, f, ensure_ascii=False, indent=4)
    pass