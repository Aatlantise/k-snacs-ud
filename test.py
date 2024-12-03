import re
from typing import Union, List

class TokenObject:
    def __init__(self, args: dict):
        self.p = None
        self.gold_scene = None
        self.gold_function = None
        self.id = -1
        self.text = "_"
        self.lemma = "_"
        self.upos = "_"
        self.feats = "_"
        self.xpos = "_"
        self.head = -1
        self.deprel = "_"
        self.deps = "_"
        self.start_char = -1
        self.end_char = -1
        self.misc = "_"

        for key, value in args.items():
            if value == "_":
                setattr(self, key, None)
            else:
                setattr(self, key, value)

        self.lemma = self.lemma.split("+")
        self.xpos = self.xpos.split("+")

    @staticmethod
    def to_str(attr) -> str:
        if type(attr) == list:
            return "+".join(attr)
        else:
            return str(attr)

    def conllu_line(self):
        return '\t'.join([self.to_str(k) for k in [self.id, self.text, self.lemma, self.upos, self.xpos, self.feats,
                                                   self.head, self.deprel, self.deps, self.misc]])

    def _lemma_xpos_length_match_test(self):
        return len(self.lemma) == len(self.xpos)

    def _xpos_includes_adp_test(self):
        return any([re.match(r'j[cx][acjmorst]', xpos) for xpos in self.xpos])

    def non_adp_test(self):
        assert self.p is None
        assert self.gold_scene is None
        assert self.gold_function is None
        assert self.deprel != "case"
        assert type(self.id) == int

    def adp_container_test(self):
        self.non_adp_test()
        assert self._lemma_xpos_length_match_test()
        # todo: ensure XPOS list aligns with adp_node XPOS

    def adp_node_test(self):
        assert self.p in ["의", "에", "은", "에다", "에서", "를", "가", "ㄹ", "이", "만", "을", "까지", "는", "도",
                             "ㄴ", "과", "에게", "와", "나", "이나", "마다", "서", "로서", "라고", "처럼", "고", "으로",
                             "하고", "이라는", "야", "아", "뿐", "더러", "요", "에게서", "이라고", "보디", "이라도", "만큼",
                             "한테", "부터", "으로부터", "로써", "께", "서부터", "조차", "이란", "야말로", "란", "로", "밖에",
                             "로부터"]
        assert self.text == self.p
        assert self.gold_scene is not None # todo: replace is not None with actual list of gold_scene annotations
        assert self.gold_function is not None

    def __call__(self):
        if self.xpos == "ADP":
            self.adp_node_test()
        elif self.p != "_":
            self.adp_container_test()
        elif self.p == "_":
            self.non_adp_test()
        else:
            raise ValueError("p attribute somehow incorrect")

# todo: text-lemma mistmatch check
# e.g.
#                 "text": ".....",
#                 "lemma": "....+하+지",





