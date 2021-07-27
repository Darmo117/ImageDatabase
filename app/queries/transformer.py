import re

import lark
import sympy as sp

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

    def tag(self, tag):
        return self._symbol(str(tag))

    def metatag_plain(self, metatag, value):
        return self._metatag(metatag, value, 'plain')

    def metatag_regex(self, metatag, value):
        return self._metatag(metatag, value, 'regex')

    def _metatag(self, metatag, value, mode: str):
        metatag = str(metatag)
        # Remove enclosing / or "
        value = str(value)[1:-1]
        if mode == 'plain':
            value = value.replace(r'\"', '"')
        if not da.ImageDao.check_metatag_value(metatag, value, mode):
            raise ValueError(_t('query_parser.error.invalid_metatag_value', value=value, metatag=metatag))
        return self._symbol(f'{metatag}:{mode}:{value}')

    negation = sp.Not

    @staticmethod
    def _symbol(name: str):
        """Creates a new Sympy symbol. Escapes special characters from name: colon, space, comma and parentheses."""
        return sp.symbols(re.sub('([: ,()])', r'\\\1', name))

    def get_sympy(self, query: str, simplify: bool = True) -> sp.Basic:
        """Converts the given string query into a SymPy expression.

        :param query: The query to convert.
        :param simplify: If true (default) the result will be simplified using boolean logic.
        :return: A SymPy expression.
        """
        parsed_query = self._parser.parse(query)
        # noinspection PyUnresolvedReferences
        bool_expr = self.transform(parsed_query)

        if simplify:
            bool_expr = sp.simplify_logic(bool_expr)

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
