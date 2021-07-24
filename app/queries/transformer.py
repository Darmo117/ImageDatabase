import re

import lark
import sympy as sp
from sympy.logic import boolalg as ba

from .. import data_access as da
from ..i18n import translate as _t


class _TreeToBoolean(lark.InlineTransformer):
    """This class is the lexer for the tag query language.
    It converts a string query into a SymPy expression.
    """

    def __init__(self):
        with open('app/queries/grammar.lark') as f:
            grammar = '\n'.join(f.readlines())
        self._parser = lark.Lark(grammar, parser='lalr', lexer='contextual', start='query')

    def conjunction(self, *args):
        # Filter out whitespace
        return sp.And(*self._filter_whitespace(args))

    def disjunction(self, *args):
        # Filter out whitespace
        return sp.Or(*self._filter_whitespace(args))

    def group(self, *args):
        # Filter out whitespace
        return self._filter_whitespace(args)[0]

    @staticmethod
    def _filter_whitespace(args: tuple) -> list:
        return [arg for arg in args if not isinstance(arg, lark.lexer.Token)]

    # noinspection PyMethodMayBeStatic
    def tag(self, tag):
        return sp.symbols(str(tag))

    # noinspection PyMethodMayBeStatic
    def metatag(self, metatag, value):
        metatag = str(metatag)
        value = str(value)
        if not da.ImageDao.check_metatag_value(metatag, value):
            raise ValueError(_t('query_parser.error.invalid_metatag_value'))
        # Double-escape backslash
        return sp.symbols(metatag + r'\:' + value.replace('\\', r'\\'))

    negation = sp.Not

    def get_sympy(self, query: str, simplify: bool = True) -> sp.Basic:
        """Converts the given string query into a SymPy expression.

        :param query: The query to convert.
        :param simplify: If true (default) the result will be simplified using boolean logic.
        :return: The SymPy expression.
        """
        parsed_query = self._parser.parse(query)
        # noinspection PyUnresolvedReferences
        bool_expr = self.transform(parsed_query)

        if simplify:
            if ba.is_dnf(bool_expr):
                form = 'dnf'
            elif ba.is_cnf(bool_expr):
                form = 'cnf'
            else:
                form = None
            bool_expr = sp.simplify_logic(bool_expr, form=form)

        return bool_expr


_transformer = None


def query_to_sympy(query: str, simplify: bool = True) -> sp.Basic:
    """Converts a query into a simplified SymPy boolean expression.

    :param query: The query to convert.
    :param simplify: If true the query will be simplified once it is converted into a SymPy expression.
    :return: The simplified SymPy expression.
    """
    global _transformer

    if _transformer is None:
        _transformer = _TreeToBoolean()

    try:
        return _transformer.get_sympy(query, simplify=simplify)
    except lark.ParseError as e:
        message = str(e)
        # Lark parse errors are not very readable, just send a simpler error message if possible.
        if match := re.match(r"^Unexpected token Token\('[\w$]+', '(.+?)'\)", message):
            raise ValueError(_t('query_parser.error.syntax_error', token=match[1]))
        elif '$END' in message:
            raise ValueError(_t('query_parser.error.syntax_error_eol'))
        raise ValueError(e)
    except lark.UnexpectedInput as e:
        c = query[e.pos_in_stream]
        raise ValueError(_t('query_parser.error.illegal_character', char=c, code=hex(ord(c))[2:].upper().rjust(4, '0')))
