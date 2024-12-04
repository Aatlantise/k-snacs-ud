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
        "하고": "jcr",
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
    "뿐": {"xpos": "xsn"}, # XPOS elaboration for adposition tag in 하나뿐인
    "요": {"xpos": "ef"}, # XPOS elaboration for adposition tag in 왜요
    "먹는다는게": {"lemma": "먹+는다는+것+이", "xpos": "pvg+etm+nbn+jcs", "upos": "NOUN"}, # todo: upos unsure; 이 separate as ADP; no similar examples in UD
    "불행히도": {},
    "널": {"lemma": "너+ㄹ", "xpos": "npp+jco", "upos": "PRON"},
    "것을요": {"lemma": "것+을+요", "xpos": "nbn+jco+ef", "upos": "VERB"},
    "제게": {"lemma": "제+게", "xpos": "npp+jca", "upos": "ADV"},
    "날": {"lemma": "나+ㄹ", "xpos": "npp+jco", "upos": "PRON"},
    "모든게": {"lemma": "모든+것+이", "xpos": "mma+nbn+jcs", "upos": "NOUN"},
    '......"': {"lemma": "......+\"", "xpos": "sf+sr", "upos": "PUNCT"}, # segmentation artifact that happens when a supertoken with both punctuation and adposition is segmented. Also need to remove the ghost ADP
    "그럴지도": {"lemma": "그럴지+도", "xpos": "mag+jxc", "upos": "ADV"},
    "체험담이라는": {"lemma": "체험담+이라는", "xpos": "ncn+jca", "upos": "NOUN"},
    "가까이서": {"xpos": "mag+jca", "upos": "ADV"},
    "멋이": {"xpos": "ncn+jcs", "lemma": "멋+이", "upos": "NOUN"},
    "겁에질려": {"lemma": "겁+에+질리+어", "xpos": "ncn+jca+pvg+ecx", "upos": "VERB"},
    "한가운데서": {"lemma": "한가운데서", "xpos": "ncn+jca", "upos": "NOUN"},
    "그림이라서": {"xpos_error": False}, # correct, flagged error bc of incorrectly associated adposition
    "그리곤": {"xpos": "maj+jxt", "lemma": "그리고+ㄴ", "upos": "CCONJ"},
    "저걸": {"xpos": "npd+jxt", "lemma": "저거+ㄹ", "upos": "PRON"},
    "타고서야": {"lemma": "타+고서+야", "xpos": "pvg+ecs+jcx"},
    "사람아": {"xpos": "ncn+ef", "lemma": "사람+아", "upos": "PART"},
    "애도": {"xpos": "ncn+jxc", "lemma": "애+도"},
    "앤": {"lemma": "애+ㄴ", "xpos": "ncn+jxt"},
    "그때야": {"lemma": "그+때+야", "xpos": "mmd+ncn+jxc", "upos": "ADV"},
    "증거이다": {"xpos_error": False}, # correct, flagged error bc of incorrectly associated adposition
    "왔다": {"xpos_error": False}, # correct, flagged error bc of incorrectly associated adposition
    "날마다": {"lemma": "날+마다", "xpos": "ncn+jxc", "upos": "ADV"},
    "놓아야겠네": {"xpos_error": False}, # correct, flagged error bc of incorrectly associated adposition
    "말을했다": {"lemma": "말+을+하+었+다", "xpos": "ncpa+jco+xsv+ep+ef"},
    "지길": {"lemma": "지기+ㄹ", "xpos": "pvg+jco", "upos": "VERB", "deprel": "obl"},
    "달려갈수만": {"lemma": "달려+가+ㄹ+수+만", "xpos": "pvg+px+etm+nbn+jxc", "upos": "NOUN"},
    "꽃도": {"lemma": "꽃+도",
                "upos": "ADV",
                "xpos": "ncn+jxc",},
    "가시는": {"lemma": "가시+는", "xpos": "jxt", "upos": "NOUN"},
    "사람이야>라고": {"lemma": "사람+이+야+>+라고", "xpos": "ncn+jp+ef+sr+jcr"},
    "중요한게": {"lemma": "중요+하+ㄴ+것+이", "xpos": "ncps+xsm+etm+nbn+jcs", "upos": "NOUN"},
    "있겠지": {"xpos_error": False}, # correct, flagged error bc of incorrectly associated adposition
    ">하고": {"lemma": ">+하고", "xpos": "sr+jcr", "upos": "ADP"},
    "버리곤": {"lemma": "버리+고+ㄴ", "xpos": "pvg+ecx+jxt",},
    "바보밥나무인지도": {"lemma": "바보밥나무+이+ㄴ+지+도", "xpos": "ncn+jp+etm+nbn+jxc"},
    "언제까지고": {"lemma": "언제+까지+고", "xpos": "mag+jxc+ef", "upos": "ADV"},
    "있을리가": {"lemma": "있+ㄹ+리+가", "xpos": "paa+etm+nbn+jcs", "upos": "NOUN"},
    "있을때는": {},
    "노력하길": {},
    "한번도": {},
    "네게": {},
    "겁이나서": {},
    "장군더러": {},
    "말하곤": {},
    "있을게": {},
    "날아다": {},
    "것은요": {},
    "갖추어지길": {},
    "된것이": {},
    "준수되길": {},
    "찬양하는게": {},
    "마시는게": {},
    "애기야": {},
    "되는게": {},
    "뭘해": {},
    "지가": {},
    "그야": {},
    "산은요": {},
    "사막은요": {},
    "될지도": {},
    "발견했을때는": {},
    "멀리서": {},
    "가져올때까지": {},
    "존재야": {},
    "보는게": {},
    "포함해서": {},
    "말을하면": {},
    "찾아온게": {},
    "지구야": {},
    "여긴": {},
    "말만하니": {},
    "이걸": {},
    "버릴지도": {},
    "나하고": {},
    "너하고": {},
    "맺는다": {},
    "는": {},
    "별에서": {},
    "병아리는": {},
    "저길": {},
    "내게서": {},
    "오는게": {},
    "말고": {},
    "전철수": {},
    "사람": {},
    "거라곤": {},
    "친구야": {},
    "......": {},
    "그렇지": {},
    "별이건": {},
    "느낌까지": {},
    "가는게": {},
    "있는게": {},
    "하는게": {},
    "여기는": {},
    "이젠": {},
    "꼬마야": {},
    "바라보는게": {},
    "왕자야": {},
    "죽는건": {},
    "하곤": {},
    "나왔을지도": {},
    "않았느냐에": {},
}


if __name__ == "__main__":
    with open("little_prince_annotation_ready.json", encoding="utf-8") as f:
        annotation_json = json.load(f)
    json2conllu(annotation_json)
