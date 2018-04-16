import re

from lark import Lark, InlineTransformer, common, lexer
from sympy import Not, And, Or, symbols, simplify_logic

from app.data_access import ImageDao


class TreeToBoolean(InlineTransformer):
    def __init__(self):
        with open("app/queries/grammar.g") as f:
            grammar = "\n".join(f.readlines())

        self._parser = Lark(grammar, start="query")
        self._symbols = {}

    # noinspection PyMethodMayBeStatic
    def conjunction(self, *args):
        # Filter out whitespace
        return And(*filter(lambda arg: not isinstance(arg, lexer.Token), args))

    # noinspection PyMethodMayBeStatic
    def disjunction(self, *args):
        # Filter out whitespace
        return Or(*filter(lambda arg: not isinstance(arg, lexer.Token), args))

    # noinspection PyMethodMayBeStatic
    def group(self, *args):
        # Filter out whitespace
        return [arg for arg in args if not isinstance(arg, lexer.Token)][0]

    negation = Not

    def tag(self, tag):
        return self._symbols[str(tag)]

    def metatag(self, metatag, value):
        metatag = str(metatag)
        if not ImageDao.metatag_exists(metatag):
            raise common.ParseError("Unknown metatag '{}'!".format(metatag))
        if not ImageDao.check_metatag_value(metatag, value):
            raise ValueError("Invalid value '{}' for metatag '{}'!".format(value, metatag))
        return self._symbols[metatag + ":" + str(value)]

    def get_sympy(self, query, simplify=True):
        # Escape ':' because of 'symbols' function.
        tags = {t.replace(":", "\\:") for t in re.compile(r"[^\w:]+").split(query) if t != ""}
        self._symbols = {s.name: s for s in symbols(tags)}
        tree = self.transform(self._parser.parse(query))
        if simplify:
            tree = simplify_logic(tree)
        return tree


transformer = None


def query_to_sympy(query):
    """Converts a query to a SymPy boolean expression."""
    global transformer

    if transformer is None:
        transformer = TreeToBoolean()

    try:
        return transformer.get_sympy(query)
    except common.ParseError as e:
        if "[" in e.args[0]:  # Lark parse errors are not very readable, just send a simple error message.
            raise ValueError("Syntax error!")
        raise ValueError(e)
    except lexer.UnexpectedInput as e:
        raise ValueError("Illegal character '{}'!".format(e.context[0]))
