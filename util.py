import unicodedata


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
    "뿐": {"xpos": "xsn"} # XPOS elaboration for adposition tag in 하나뿐인
    "요": {"xpos": "ef"} # XPOS elaboration for adposition tag in 왜요
    "먹는다는게": {"lemma": "먹+는다는것+이", "xpos": "pvg+etm+jcs", },
    "불행히도": {},
    "널": {},
    "것을요": {},
    "제게": {},
    "날": {},
    "모든게": {},
    '......"': {},
    "그럴지도": {},
    "체험담이라는": {},
    "가까이서": {},
    "멋이": {},
    "겁에질려": {},
    "한가운데서": {},
    "그림이라서": {},
    "그리곤": {},
    "저걸": {},
    "타고서야": {},
    "사람아": {},
    "애도": {},
    "앤": {},
    "그때야": {},
    "증거이다": {},
    "왔다": {},
    "날마다": {},
    "놓아야겠네": {},
    "말을했다": {},
    "지길": {},
    "달려갈수만": {},
    "꽃도": {},
    "가시는": {},
    "사람이야>라고": {},
    "중요한게": {},
    "있겠지": {},
    ">하고": {},
    "버리곤": {},
    "바보밥나무인지도": {},
    "언제까지고": {},
    "있을리가": {},
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
