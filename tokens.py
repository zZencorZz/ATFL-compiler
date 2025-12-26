from typing import NamedTuple, Optional
from enum import StrEnum

KEYWORDS = [
    'true',
    'false',
    'end',
    'integer',
    'real',
    'boolean',
    'let',
    'if',
    'then',
    'else',
    'end_else',
    'for',
    'do',
    'while',
    'loop',
    'input',
    'output',
]

SEPARATORS = [
    'NE',
    'EQ',
    'LT',
    'LE',
    'GT',
    'GE',
    'plus',
    'min',
    'or',
    'mult',
    'div',
    'and',
    '~',
    '(',
    ')',
    ':',
    ',',
    ';',
    '{',
    '}',
    '=',
    '(*',
    '*)',
    ' ',
    '\n',
]

LETTER_SEPARATORS = [sep for sep in SEPARATORS if sep.isalpha()]
SYMBOL_SEPARATORS = [sep for sep in SEPARATORS if not sep.isalpha()]

class TokenType(StrEnum):
    KEYWORD = 'KEYWORD'
    IDENTIFIER = 'IDENTIFIER'
    NUMBER = 'NUMBER'
    SEPARATOR = 'SEPARATOR'

class Token(NamedTuple):
    type: TokenType
    value: str          # для NUMBER: "bits (raw)", для прочих — как есть
    line: int
    col: int
    raw_value: Optional[str] = None  # только для NUMBER