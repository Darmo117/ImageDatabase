import re

from lark import Lark, InlineTransformer, common
from sympy import Not, And, Or, symbols, simplify_logic

from app.data_access import ImageDao


class TreeToBoolean(InlineTransformer):
    def __init__(self):
        with open("app/queries/grammar.g") as f:
            grammar = "\n".join(f.readlines())

        self._parser = Lark(grammar, start="query")
        self._symbols = {}

    conjunction = And
    disjunction = Or
    negation = Not

    def group(self, a):
        return a

    def tag(self, t):
        return self._symbols[str(t)]

    def get_sympy(self, query, simplify=True):
        tags = {t for t in re.compile(r"\W+").split(query) if t != ""}
        self._symbols = {s.name: s for s in symbols(tags)}
        tree = self.transform(self._parser.parse(query))
        if simplify:
            tree = simplify_logic(tree)
        print(tree)
        return tree


def query_to_sympy(query):
    try:
        tree = TreeToBoolean().get_sympy(query)
        # noinspection PyProtectedMember
        return ImageDao._get_query(tree)
    except (common.ParseError, common.UnexpectedToken):
        return None


text = "a + -b"
print(query_to_sympy(text))
