import unicodedata
import json
from test import TokenObject


def json2conllu(annotation_json_obj):
    """
    Converts json annotation file to conll-u format, saves as a plain text file, per UD advice.

    :param annotation_json_obj: JSON object, imported from little_prince_annotation_ready.json
    :return: None. Saves little_prince_ko.conllu to root folder.
    """
    conll_file_name = "little_prince_ko.conllu"
    with open(conll_file_name, "w", encoding="utf-8") as f:
        for c, chapter in enumerate(annotation_json_obj):
            for s, sent in enumerate(chapter):
                sentence_text = " "
                token_lines = []
                for _tok in sent:
                    tok = TokenObject(_tok)
                    if type(tok.id) == int:
                        sentence_text += tok.text
                        sentence_text = sentence_text + " " if "SpaceAfter=No" not in tok.misc else sentence_text
                    token_lines.append(tok.conllu_line())
                f.write(f"# sent_id = {c}-{s}\n")
                f.write(f"#{sentence_text}\n")
                for token_line in token_lines:
                    f.write(token_line + "\n")


def p2xpos(p, function):
    table = {
        "의": "jcm",
        "에": "jca",
        "은": "jxt",
        "에다": "jca",
        "에서": "jca",
        "를": "jco",
        "가": "jcs",
        "ㄹ": "jco",
        "이": "jcs",
        "만": "jxc",
        "을": "jco",
        "까지": "jxc",
        "는": "jxt",
        "도": "jxc",
        "ㄴ": "jxt",
        "과": {"ancillary": "jct", "comparisonref": "jct", "ensemble": "jcj"},
        "에게": "jca",
        "와": {"ancillary": "jct", "comparisonref": "jct", "ensemble": "jcj"},
        "나": {"focus": "jxc", "ensemble": "jcj"},
        "이나": {"focus": "jxc", "ensemble": "jcj"},
        "마다": "jxc",
        "서": "jca",
        "로서": "jca",
        "라고": "jcr",
        "처럼": "jca",
        "고": "jcr",
        "으로": "jca",
        "하고": "jcr",  # todo: ancillary: jct (KAIST) jcj (dict def); quote~topic: jcr
        "이라는": "jca",
        "야": "jxc",
        "아": "ERROR",
        "뿐": "ERROR",
        "더러": "jca",
        "요": "ERROR",
        "에게서": "jca",
        "이라고": "jcr",
        "보다": "jca",
        "이라도": "jxc",
        "만큼": "jca",
        "한테": "jca",
        "부터": "jxc",
        "으로부터": "jxc",
        "로써": "jca",
        "께": "jxc",
        "서부터": "jxc",
        "조차": "jxc",
        "이란": "jxc",
        "야말로": "jxc",
        "란": "jxc",
        "로": "jca",
        "밖에": "jxc",
        "로부터": "jxc"
    }

    return table[p] if type(table[p]) == str else table[p][function]


def decompose_hangul(syllable):
    # Constants for Hangul decomposition
    hangul_base = 0xAC00
    onset_base = 588
    nucleus_base = 28

    # Onsets (초성) and codas (받침) lists
    onsets = [
        'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ',
        'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
    ]
    nuclei = [
        'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ',
        'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
    ]
    codas = [
        '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ',
        'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
    ]

    code = ord(syllable) - hangul_base
    onset_index = code // onset_base
    nucleus_index = (code % onset_base) // nucleus_base
    coda_index = code % nucleus_base

    onset = onsets[onset_index]
    nucleus = nuclei[nucleus_index]
    coda = codas[coda_index]

    return onset, nucleus, coda


xpos_error_fix = {
    "내": {"xpos": "npp+jcm", "lemma": "나+의"},
    "네": {"xpos": "npp+jcm", "lemma": "너+의"},
    "뭘": {"xpos": "npd+jco", "lemma": "무엇+을"},
    "그런데도": {"xpos": "maj+jxc", "lemma": "그런데+도"},
    "아직도": {"xpos": "maj+jxc", "lemma": "아직+도"},
    "하고": {"xpos": "jcr", "lemma": "하고"},
    "난": {"xpos": "npp+jxt", "lemma": "나+ㄴ", "upos": "PRON", "deprel": "obj"},
    "아저씬": {"xpos": "ncn+jxt", "lemma": "아저씨+는", "upos": "NOUN"},
    "제": {"xpos": "npp+jcm", "lemma": "저+의", "upos": "PRON"},
    "뿐": {"xpos": "xsn"},  # XPOS elaboration for adposition tag in 하나뿐인
    "요": {"xpos": "ef"},  # XPOS elaboration for adposition tag in 왜요
    "먹는다는게": {"lemma": "먹+는다는+것+이", "xpos": "pvg+etm+nbn+jcs", "upos": "NOUN"},
    # todo: upos unsure; 이 separate as ADP; no similar examples in UD
    "불행히도": {"lemma": "불행히+도", "xpos": "mag+jxc"},
    "널": {"lemma": "너+ㄹ", "xpos": "npp+jco", "upos": "PRON"},
    "것을요": {"lemma": "것+을+요", "xpos": "nbn+jco+ef", "upos": "VERB"},
    "제게": {"lemma": "제+게", "xpos": "npp+jca", "upos": "ADV"},
    "날": {"lemma": "나+ㄹ", "xpos": "npp+jco", "upos": "PRON"},
    "모든게": {"lemma": "모든+것+이", "xpos": "mma+nbn+jcs", "upos": "NOUN"},
    '......"': {"lemma": "......+\"", "xpos": "sf+sr", "upos": "PUNCT"},
    # segmentation artifact that happens when a supertoken with both punctuation and adposition is segmented. Also need to remove the ghost ADP
    "그럴지도": {"lemma": "그렇+ㄹ지+도", "xpos": "mag+ecs+jxc", "upos": "ADV"},
    "체험담이라는": {"lemma": "체험담+이라는", "xpos": "ncn+jca", "upos": "NOUN"},
    "가까이서": {"xpos": "mag+jca", "upos": "ADV"},
    "멋이": {"xpos": "ncn+jcs", "lemma": "멋+이", "upos": "NOUN"},
    "겁에질려": {"lemma": "겁+에+질리+어", "xpos": "ncn+jca+pvg+ecx", "upos": "VERB"},
    "한가운데서": {"lemma": "한가운데서", "xpos": "ncn+jca", "upos": "NOUN"},
    "그림이라서": {"xpos_error": False},  # correct, flagged error bc of incorrectly associated adposition
    "그리곤": {"xpos": "maj+jxt", "lemma": "그리고+ㄴ", "upos": "CCONJ"},
    "저걸": {"xpos": "npd+jxt", "lemma": "저거+ㄹ", "upos": "PRON"},
    "타고서야": {"lemma": "타+고서+야", "xpos": "pvg+ecs+jcx"},
    "사람아": {"xpos": "ncn+ef", "lemma": "사람+아", "upos": "PART"},
    "애도": {"xpos": "ncn+jxc", "lemma": "애+도"},
    "앤": {"lemma": "애+ㄴ", "xpos": "ncn+jxt"},
    "그때야": {"lemma": "그+때+야", "xpos": "mmd+ncn+jxc", "upos": "ADV"},
    "증거이다": {"xpos_error": False},  # correct, flagged error bc of incorrectly associated adposition
    "왔다": {"xpos_error": False},  # correct, flagged error bc of incorrectly associated adposition
    "날마다": {"lemma": "날+마다", "xpos": "ncn+jxc", "upos": "ADV"},
    "놓아야겠네": {"xpos_error": False},  # correct, flagged error bc of incorrectly associated adposition
    "말을했다": {"lemma": "말+을+하+었+다", "xpos": "ncpa+jco+xsv+ep+ef"},
    "지길": {"lemma": "지기+ㄹ", "xpos": "pvg+jco", "upos": "VERB", "deprel": "obl"},
    "달려갈수만": {"lemma": "달려+가+ㄹ+수+만", "xpos": "pvg+px+etm+nbn+jxc", "upos": "NOUN"},
    "꽃도": {"lemma": "꽃+도",
           "upos": "ADV",
           "xpos": "ncn+jxc", },
    "가시는": {"lemma": "가시+는", "xpos": "jxt", "upos": "NOUN"},
    "사람이야>라고": {"lemma": "사람+이+야+>+라고", "xpos": "ncn+jp+ef+sr+jcr"},
    "중요한게": {"lemma": "중요+하+ㄴ+것+이", "xpos": "ncps+xsm+etm+nbn+jcs", "upos": "NOUN"},
    "있겠지": {"xpos_error": False},  # correct, flagged error bc of incorrectly associated adposition
    ">하고": {"lemma": ">+하고", "xpos": "sr+jcr", "upos": "ADP"},
    "버리곤": {"lemma": "버리+고+ㄴ", "xpos": "pvg+ecx+jxt", },
    "바보밥나무인지도": {"lemma": "바보밥나무+이+ㄴ+지+도", "xpos": "ncn+jp+etm+nbn+jxc"},
    "언제까지고": {"lemma": "언제+까지+고", "xpos": "mag+jxc+ef", "upos": "ADV"},
    "있을리가": {"lemma": "있+ㄹ+리+가", "xpos": "paa+etm+nbn+jcs", "upos": "NOUN"},  # todo: 을 or ㄹ?
    "있을때는": {"lemma": "있+을+때+는", "xpos": "px+etm+ncn+jxt"},  # todo: 을 or ㄹ?
    "노력하길": {"lemma": "노력+하+기+ㄹ", "xpos": "ncpa+xsv+etn+jco", "upos": "NOUN"},
    "한번도": {"xpos": "nnc+nbu+jxc", "lemma": "한+번+도", },
    "네게": {"lemma": "너+에게", "xpos": "npp+jca", "upos": "ADV"},
    "겁이나서": {"lemma": "겁+이+나+서", "xpos": "ncn+jcs+pvg+ecs", },
    "장군더러": {"xpos": "ncn+jca", },
    "말하곤": {"xpos": "pvg+ecx+jxt", "lemma": "말하+고+ㄴ"},
    "있을게": {"lemma": "있+을+것+이", "xpos": "paa+etm+nbn+jcs"},  # todo: 을 or ㄹ?
    "날아다": {"xpos_error": False},  # correct, flagged error bc of incorrectly associated adposition
    "것은요": {"lemma": "것+은+요", "xpos": "nbn+jxt+ef", },
    "갖추어지길": {"lemma": "갖추+어+지+기+ㄹ", "xpos": "pvg+ecx+px+etn+jco", },
    "된것이": {"lemma": "되+ㄴ+것+이", "xpos": "xsv+etm+nbn+jcs", "upos": "NOUN"},
    "준수되길": {"lemma": "준수+되+기+ㄹ", "xpos": "ncpa+xsv+etn+jco", },
    "찬양하는게": {"lemma": "찬양+하+는+것+이", "xpos": "ncpa+xsv+etm+nbn+jcs", },
    "마시는게": {"lemma": "마시+는+것+이", "xpos": "pvg+etm+nbn+jcs", },
    "얘기야": {"xpos_error": False},  # correct, `d annotation seems to be faulty
    "되는게": {"lemma": "되+는+것+이", "xpos": "pvg+etm+nbn+jcs", },
    "뭘해": {"lemma": "무엇+을+해+아", "xpos": "npd+jco+pvg+ef"},
    "지가": {"lemma": "지+가", "xpos": "nbn+jcs"},
    "그야": {"lemma": "그+야", "xpos": "npd+jxc"},
    "산은요": {"lemma": "산+은+요", "xpos": "ncn+jxt+ef"},
    "사막은요": {"lemma": "사막+은+요", "xpos": "ncn+jxt+ef"},
    "될지도": {"lemma": "되+ㄹ지+도", "xpos": "px+ecs+jxc", },
    "발견했을때는": {"lemma": "발견+하+었+을+때+는", "xpos": "ncpa+xsv+ep+etm+nbn+jxt", "upos": "NOUN"},
    "멀리서": {"xpos": "mag+jca", "upos": "ADV"},  # mag or paa? affects upos as well
    "가져올때까지": {"lemma": "가져오+ㄹ+때+까지", "xpos": "pvg+etm+ncn+jxc"},  # todo: granularity correct? 가지+어+오? 가져+오 (pvg+px)?
    "존재야": {"xpos_error": False},  # correct, `d annotation seems to be faulty
    "보는게": {"lemma": "보+는+것+이", "xpos": "pvg+etm+nbn+jcs", "upos": "NOUN"},
    "포함해서": {"xpos_error": False},  # correct, flagged error bc of incorrectly associated adposition
    "말을하면": {"xpos": "ncpa+jco+pvg+ecs", "lemma": "말+을+하+면"},
    "찾아온게": {"lemma": "찾+아+오+ㄴ+것+이", "xpos": "pvg+ecx+px+etm+nbn+jcs", "upos": "NOUN"},
    "지구야": {"lemma": "지구+야", "xpos": "nqq+ef", "upos": "PROPN"},  # todo: `d vocative as ef?
    "여긴": {"lemma": "여기+ㄴ", "xpos": "npd+jxt", "upos": "PRON"},
    "말만하니": {"lemma": "말만+하+니", "xpos": "ncpa+jxc+xsv+ef", },
    "이걸": {"lemma": "이것+ㄹ", "xpos": "npd+jco"},
    "버릴지도": {"lemma": "버리+ㄹ지+도", "xpos": "pvg+ecs+jxc", },
    "나하고": {"lemma": "나+하고", "xpos": "npp+jct", },  # todo: 하고 mapping might be incorrect, see line 60
    "너하고": {"lemma": "나+하고", "xpos": "npp+jct", },  # todo: 하고 mapping might be incorrect, see line 60
    "맺는다": {"xpos_error": False},  # correct, `d annotation seems to be faulty
    "는": {"lemma": "는",
          "upos": "ADP",
          "xpos": "jxt", },  # todo: standalone adp, doesn't really need another node
    "별에서": {"lemma": "별+에서", "xpos": "ncn+jca", "upos": "ADV",},
    "병아리는": {"lemma": "병아리+는", "xpos": "ncn+jxt", "upos": "NOUN",}, # todo: fix syntactic node?
    "저길": {"lemma": "저기+길", "xpos": "npd+jco", "upos": "PRON",},
    "내게서": {"lemma": "나+에게서", "xpos": "npp+jca", "upos": "ADV",},
    "오는게": {"lemma": "오+는+것+이", "xpos": "pvg+etm+nbn+jcs", "upos": "NOUN"},
    "말고": {"xpos_error": False},  # flagged error bc of incorrectly associated adposition
    "전철수": {"xpos_error": False},  # flagged error bc of incorrectly associated adposition
    "사람": {"xpos_error": False},  # flagged error bc of incorrectly associated adposition
    "거라곤": {"lemma": "것+이+라+고+ㄴ", "xpos": "nbn+jp+ef+jxt", "upos": "NOUN"},
    "친구야": {"lemma": "친구+야", "xpos": "ncn+ef",},  # todo: `d vocative as ef?
    "......": {"lemma": "......", "upos": "PUNCT", "xpos": "sf", "deprel": "punct", "xpos_error": False},
    "그렇지": {"xpos_error": False},  # flagged error bc of incorrectly associated adposition
    "별이건": {"xpos_error": False},  # todo: -ㄴ doesn't seem to be an adposition here: also not annotated in 집이건
    "느낌까지": {"lemma": "느낌+까지", "xpos": "ncn+jxc",},
    "가는게": {"lemma": "가+는+것+이", "xpos": "pvg+etm+nbn+jcs", "upos": "NOUN"},
    "있는게": {"lemma": "있+는+것+이", "xpos": "paa+etm+nbn+jcs", "upos": "NOUN"},
    "하는게": {"lemma": "보+는+것+이", "xpos": "pvg+etm+nbn+jcs", "upos": "NOUN"},
    "여기는": {"xpos": "npd+jxt", "upos": "PRON"},
    "이젠": {"xpos": "ncn+jxt", "lemma": "이제+ㄴ", "upos": "NOUN"},
    "꼬마야": {"lemma": "꼬마+야", "xpos": "ncn+ef", "upos": "NOUN"},  # todo: `d vocative as ef?
    "바라보는게": {"lemma": "바라보+는+것+이", "xpos": "pvg+etm+nbn+jcs", "upos": "NOUN"},
    "왕자야": {"lemma": "왕자+야", "xpos": "ncn+ef", "upos": "NOUN"},  # todo: `d vocative as ef?
    "죽는건": {"lemma": "죽+는+것+ㄴ", "xpos": "pvg+etm+nbn+jxt", "upos": "NOUN"}, # todo: 거 vs 것?
    "하곤": {"lemma": "하+고+ㄴ", "xpos": "px+ecx",}, # todo: pretty sure is pvg, but can be px?
    "나왔을지도": {"lemma": "나와+았+ㄹ지+도", "xpos": "pvg+ep+ecs+jxc"},
    "않았느냐에": {"lemma": "않+았+느냐+에", "xpos": "px+ep+ef+jca", "upos": "NOUN"}, # upos unsure
}

if __name__ == "__main__":
    with open("little_prince_annotation_ready.json", encoding="utf-8") as f:
        annotation_json = json.load(f)
    json2conllu(annotation_json)
