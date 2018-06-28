import typing as typ

import lark
import sympy as sp

import app.data_access as da


class TreeToBoolean(lark.InlineTransformer):
    """
    This class is the lexer for the tag query language.
    It converts a string query into a SymPy expression.
    """

    def __init__(self):
        with open("app/queries/grammar.lark") as f:
            grammar = "\n".join(f.readlines())
        self._parser = lark.Lark(grammar, start="query")
        self._symbols = {}

    # noinspection PyMethodMayBeStatic
    def conjunction(self, *args):
        # Filter out whitespace
        return sp.And(*filter(lambda arg: not isinstance(arg, lark.lexer.Token), args))

    # noinspection PyMethodMayBeStatic
    def disjunction(self, *args):
        # Filter out whitespace
        return sp.Or(*filter(lambda arg: not isinstance(arg, lark.lexer.Token), args))

    # noinspection PyMethodMayBeStatic
    def group(self, *args):
        # Filter out whitespace
        return [arg for arg in args if not isinstance(arg, lark.lexer.Token)][0]

    # noinspection PyMethodMayBeStatic
    def tag(self, tag):
        return sp.symbols(str(tag))

    # noinspection PyMethodMayBeStatic
    def metatag(self, metatag, value):
        metatag = str(metatag)
        if not da.ImageDao.check_metatag_value(metatag, value):
            raise ValueError("Invalid value '{}' for metatag '{}'!".format(value, metatag))
        return sp.symbols(metatag + "\:" + str(value))

    negation = sp.Not

    def get_sympy(self, query: str, simplify=True) \
            -> typ.Union[sp.Symbol, sp.Or, sp.And, sp.Not, sp.boolalg.BooleanAtom]:
        """
        Converts the given string query into a SymPy expression.

        :param query: The query to convert.
        :param simplify: If true (default) the result will be simplified using boolean logic.
        :return: The SymPy expression.
        """
        tree = self.transform(self._parser.parse(query))
        if simplify:
            tree = sp.simplify_logic(tree)
        return tree


transformer = None


def query_to_sympy(query: str) -> typ.Union[sp.Symbol, sp.Or, sp.And, sp.Not, sp.boolalg.BooleanAtom]:
    """
    Converts a query into a simplified SymPy boolean expression.

    :param query: The query to convert.
    :return: The simplified SymPy expression.
    """
    global transformer

    if transformer is None:
        transformer = TreeToBoolean()

    try:
        return transformer.get_sympy(query)
    except lark.common.ParseError as e:
        if "[" in e.args[0]:  # Lark parse errors are not very readable, just send a simple error message.
            raise ValueError("Syntax error!")
        raise ValueError(e)
    except lark.lexer.UnexpectedInput as e:
        raise ValueError("Illegal character '{}'!".format(e.context[0]))
