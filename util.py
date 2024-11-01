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

