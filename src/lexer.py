from tokens import *
import struct
from errors import LexError, SyntaxError
from typing import List

class Lexer:
    def __init__(self, code: str):
        self.code = code
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.TI: List[str] = []
        self.TN: List[str] = []
        self.logs: List[str] = []

    def log(self, message: str):
        self.logs.append(f"[строка {self.line}, столбец {self.col}] {message}")

    def advance(self, num_chars: int = 1):
        for _ in range(num_chars):
            if self.pos >= len(self.code):
                return
            char = self.code[self.pos]
            self.pos += 1
            if char == '\n':
                self.line += 1
                self.col = 1
            else:
                self.col += 1
            
    def peek(self, num_chars: int = 0):
        if self.pos + num_chars >= len(self.code):
            return '\0'
        return self.code[self.pos + num_chars]

    def skip_whitespace(self):
        while self.peek().isspace():
            self.advance()

    def read_letter_lexeme(self):
        start_line = self.line
        start_col = self.col
        
        buffer = ''
        char = self.peek()
        while char.isalnum() or char == '_':
            if not (char.isascii() and (char == '_' or char.isalnum())):
                raise LexError(self.line, f"Недопустимый символ '{char}' в идентификаторе")
            buffer += char
            self.log(f"{char} -> {buffer}")
            self.advance()
            char = self.peek()

        if not buffer:
            raise LexError(self.line, "Пустой идентификатор")

        if buffer in LETTER_SEPARATORS:
            self.tokens.append(Token(TokenType.SEPARATOR, buffer, start_line, start_col))
            self.log(f"SEPARATOR: {buffer}")
            return
        elif buffer in KEYWORDS:
            self.tokens.append(Token(TokenType.KEYWORD, buffer, start_line, start_col))
            self.log(f"KEYWORD: {buffer}")
            return
        else:
            self.tokens.append(Token(TokenType.IDENTIFIER, buffer, start_line, start_col))
            self.log(f"IDENTIFIER: {buffer}")
            if buffer not in self.TI:
                self.TI.append(buffer)

    def read_symbolic_separator(self):
        remaining_code = self.code[self.pos:]
        for sep in sorted(SYMBOL_SEPARATORS, key=len, reverse=True):
            if remaining_code.startswith(sep):
                start_line = self.line
                start_col = self.col
                self.tokens.append(Token(TokenType.SEPARATOR, sep, start_line, start_col))
                self.advance(len(sep))
                return True
    
    def read_number(self):
        start_line = self.line
        start_col = self.col
        raw_value = '' # Сырое значение токена/строка
        state = 'START'
        self.log(f'START state')
        while True:
            current_char = self.peek()
            if current_char == '\0':
                break
            self.log(f'{raw_value} + {current_char}')
            if state == 'START':
                if current_char.isdigit():
                    digit = int(current_char)
                    raw_value += current_char
                    self.advance()
                    if digit in (0, 1):
                        state = 'B'
                    elif digit in range(0, 8):
                        state = '8cc'
                    else:
                        state = '10cc'
                elif current_char == '.':
                    raw_value += current_char
                    self.advance()
                    state = 'float'
                else:
                    break
            elif state == "B":
                if current_char in '01':
                    raw_value += current_char; self.advance()
                elif current_char in '234567':
                    raw_value += current_char; self.advance(); state = "8cc"
                elif current_char in '89':
                    raw_value += current_char; self.advance(); state = "10cc"
                elif current_char == '.':
                    raw_value += current_char; self.advance(); state = "float"
                elif current_char in 'Ee':
                    raw_value += current_char; self.advance(); state = "exp_sign"
                elif current_char in 'Bb':
                    raw_value += current_char; self.advance(); state = "B_end"
                elif current_char in 'Oo':
                    raw_value += current_char; self.advance(); state = "8_end"
                elif current_char in 'Dd':
                    raw_value += current_char; self.advance(); state = "10_end"
                elif current_char in 'ABCDEF':
                    raw_value += current_char.upper(); self.advance(); state = "16cc"
                elif current_char in 'Hh':
                    raw_value += 'H'; self.advance(); state = "16_end"
                elif current_char in ' \t\n\r;,:(){}~+-*/': 
                    break
                else:
                    raise LexError(self.line, f"Недопустимый символ '{current_char}' в числе")
            elif state == "8cc":
                if current_char in '01234567':
                    raw_value += current_char; self.advance()
                elif current_char in '89':
                    raw_value += current_char; self.advance(); state = "10cc"
                elif current_char == '.':
                    raw_value += current_char; self.advance(); state = "float"
                elif current_char in 'Ee':
                    raw_value += current_char; self.advance(); state = "exp_sign"
                elif current_char in 'Oo':
                    raw_value += current_char; self.advance(); state = "8_end"
                elif current_char in 'Dd':
                    raw_value += current_char; self.advance(); state = "10_end"
                elif current_char in 'ABCDEF':
                    raw_value += current_char.upper(); self.advance(); state = "16cc"
                elif current_char in 'Hh':
                    raw_value += 'H'; self.advance(); state = "16_end"
                elif current_char in ' \t\n\r;,:(){}~+-*/': 
                    break
                else:
                    raise LexError(self.line, f"Недопустимый символ '{current_char}' в числе")
            elif state == "10cc":
                if current_char.isdigit():
                    raw_value += current_char; self.advance()
                elif current_char == '.':
                    raw_value += current_char; self.advance(); state = "float"
                elif current_char in 'Ee':
                    raw_value += current_char; self.advance(); state = "exp_sign"
                elif current_char in 'Dd':
                    raw_value += current_char; self.advance(); state = "10_end"
                elif current_char in 'ABCDEF':
                    raw_value += current_char.upper(); self.advance(); state = "16cc"
                elif current_char in 'Hh':
                    raw_value += 'H'; self.advance(); state = "16_end"
                elif current_char in ' \t\n\r;,:(){}~+-*/': 
                    break
                else:
                    raise LexError(self.line, f"Недопустимый символ '{current_char}' в числе")
            elif state == "16cc":
                if current_char in '0123456789ABCDEF':
                    raw_value += current_char.upper(); self.advance()
                elif current_char in 'Hh':
                    raw_value += 'H'; self.advance(); state = "16_end"
                elif current_char in ' \t\n\r;,:(){}~+-*/': 
                    break
                else:
                    raise LexError(self.line, f"Недопустимый символ '{current_char}' в числе")
            elif state == "float":
                if current_char.isdigit():
                    raw_value += current_char; self.advance()
                elif current_char in 'Ee':
                    raw_value += current_char; self.advance(); state = "exp_sign"
                elif current_char in ' \t\n\r;,:(){}~+-*/': 
                    if raw_value == '.':
                        raise LexError(self.line, "Недопустимый формат числа")
                    break
                else:
                    raise LexError(self.line, f"Недопустимый символ '{current_char}' в числе")
            elif state == "exp_sign":
                if current_char in '+-':
                    raw_value += current_char; self.advance(); state = "exp_digits"
                elif current_char.isdigit():
                    raw_value += '+'; state = "exp_digits"
                else:
                    raise LexError(self.line, "Ожидалась цифра в экспоненте числа")
            elif state == "exp_digits":
                if current_char.isdigit():
                    raw_value += current_char; self.advance()
                elif current_char in ' \t\n\r;,:(){}~+-*/':
                    break
                else:
                    raise LexError(self.line, f"Порядок должен быть целым числом в числе с экспонентой")
            elif state in ["B_end", "8_end", "10_end", "16_end"]:
                if current_char in ' \t\n\r;,:(){}~+-*/': 
                    break
                else:
                    raise LexError(self.line, f"Недопустимый символ '{current_char}' после суффикса основания числа")
            else:
                break
            
        clean_raw = raw_value.upper()
        base = 10
        is_float = False
        if clean_raw.endswith('B'):
            base, clean_raw = 2, clean_raw[:-1]
        elif clean_raw.endswith('O'):
            base, clean_raw = 8, clean_raw[:-1]
        elif clean_raw.endswith('D'):
            base, clean_raw = 10, clean_raw[:-1]
        elif clean_raw.endswith('H'):
            base, clean_raw = 16, clean_raw[:-1]
        if '.' in clean_raw or 'E' in clean_raw or 'e' in clean_raw:
            is_float = True
        
        try:
            if is_float:
                value = float(clean_raw if clean_raw else '0.0') # Переводим str в float
                packed = struct.pack('f', value) # Упаковываем float в 4 байта
                bits = ''.join(f'{byte:08b}' for byte in packed) # Преобразуем байты в биты
                display = f"{bits} ({clean_raw})" # Форматируем вывод
            else:
                if clean_raw == '':
                    raise LexError(self.line, "Пустое значение числа")
                elif base == 10 and len(clean_raw) > 1 and clean_raw[0] == '0':
                    raise LexError(self.line, "Недопустимый формат числа")
                value = int(clean_raw, base)
                bits = bin(value)[2:] # Преобразуем в биты
                display = f"{bits} ({clean_raw})" # Форматируем вывод
        except Exception as e:
            raise LexError(self.line, f"Ошибка системы счисления при разборе числа {clean_raw}")
        
        if display not in self.TN:
            self.TN.append(display)
        self.tokens.append(Token(TokenType.NUMBER, display, start_line, start_col, raw_value))
        self.log(f"NUMBER: {display}")

    def read_comment(self):
        self.log("Начало комментария")
        self.tokens.append(Token(TokenType.SEPARATOR, '(*', self.line, self.col))
        self.log("SEPARATOR: (*")
        self.advance(2)
        while self.pos < len(self.code):
            if self.peek() == '*' and self.peek(1) == ')':
                self.tokens.append(Token(TokenType.SEPARATOR, '*)', self.line, self.col))
                self.log("SEPARATOR: *)")
                self.advance(2)
                return
            self.advance()
        self.log(f"Несанкционированный конец файла в комментарии, начатом на строке {self.line}")
                    
    def tokenize(self):
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens.clear()
        self.TI.clear()
        self.TN.clear()
        self.logs.clear()
        
        while self.pos < len(self.code):
            current_char = self.code[self.pos]
            if current_char == '\n':
                self.tokens.append(Token(TokenType.SEPARATOR, '\n', self.line, self.col))
                self.advance()
            elif current_char == ' ':
                self.tokens.append(Token(TokenType.SEPARATOR, ' ', self.line, self.col))
                self.advance()
            elif current_char.isspace():
                self.skip_whitespace()
            elif current_char == '(' and self.peek(1) == '*':
                self.read_comment()
            elif current_char.isalpha():
                self.read_letter_lexeme()
            elif current_char in SYMBOL_SEPARATORS:
                self.read_symbolic_separator()
            elif current_char.isdigit() or current_char == '.':
                self.read_number()
            else:
                raise LexError(self.line, f"Недопустимый символ '{current_char}'")
        
        print("\n".join(self.logs))
        return self.tokens