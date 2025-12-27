from typing import Dict, List, Optional
from tokens import Token, TokenType
from errors import SyntaxError, SemanticError

class Context:
    def __init__(self):
        self.symbols: Dict[str, str] = {}
        self.tokens: List[Token] = []
        self.pos: int = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def peek(self, offset: int = 1):
        peek_pos = self.pos + offset
        return self.tokens[peek_pos] if peek_pos < len(self.tokens) else None

    def consume(self, type: str, value: Optional[str] = None, skip: bool = True):
        current_token = self.current()
        if not current_token:
            raise SyntaxError(0, "Неожиданный конец файла")
        if current_token.type != type or (value is not None and current_token.value != value):
            got = f"{current_token.type}('{current_token.value}')"
            expected = f"{type}('{value}')" if value is not None else type
            raise SyntaxError(current_token.line, f"Ожидался токен {expected}, но получен {got}")
        self.pos += 1
        return current_token
    
    def skip_layout(self):
        while self.current() and self.current().value in [' ', '\n']:
            self.pos += 1
        if self.current() and self.current().value == '(*':
            while self.current() and self.current().value != '*)':
                self.pos += 1
            if self.current() and self.current().value == '*)':
                self.pos += 1
            self.skip_layout()
    
    def declare_symbol(self, name: str, type: str):
        if name in self.symbols:
            raise SemanticError(f"Переменная '{name}' уже объявлена")
        self.symbols[name] = type

    def get_type(self, name: str):
        if name not in self.symbols:
            raise SemanticError(f"Переменная '{name}' не объявлена")
        return self.symbols[name]
    
    def peek_non_layout(self, start_offset=0):
        i = self.pos + start_offset
        while i < len(self.tokens) and self.tokens[i].value in [' ', '\n']:
            i += 1
        return self.tokens[i] if i < len(self.tokens) else None
    
class Parser:
    def __init__(self, tokens: List[Token]):
        self.ctx = Context()
        self.ctx.tokens = tokens
        self.ctx.pos = 0

    # <программа>::={/ (<описание> | <оператор>) ( : | переход строки) /} end
    def program(self):
        self.ctx.skip_layout()
        while True:
            if self.ctx.current() and self.ctx.current().value == '(*':
                while self.ctx.current() and self.ctx.current().value != '*)':
                    self.ctx.pos += 1
                if self.ctx.current() and self.ctx.current().value == '*)':
                    self.ctx.pos += 1
                self.ctx.skip_layout()
                continue

            if not self.ctx.current() or self.ctx.current().value == 'end':
                break

            if self.is_declaration():
                self.declaration()
            else:
                self.operator()
            
            self.ctx.skip_layout()
              
        self.ctx.consume(TokenType.KEYWORD.value, 'end')

    def is_declaration(self):
        token0, token1 = self.ctx.peek_non_layout(), self.ctx.peek_non_layout(1)
        return (token0 and token0.type == TokenType.IDENTIFIER.value and
                token1 and token1.value in [',', ':'])

    # <описание>::= {<идентификатор> {, <идентификатор> } : <тип> ;}
    def declaration(self):
        names = [self.ctx.consume(TokenType.IDENTIFIER.value).value]
        while self.ctx.current() and self.ctx.current().value == ',':
            self.ctx.skip_layout()
            self.ctx.consume(TokenType.SEPARATOR.value, ',')
            self.ctx.skip_layout()
            names.append(self.ctx.consume(TokenType.IDENTIFIER.value).value)
        self.ctx.skip_layout()
        self.ctx.consume(TokenType.SEPARATOR.value, ':')
        self.ctx.skip_layout()
        token = self.ctx.consume(TokenType.KEYWORD.value)
        if token.value not in ['integer', 'real', 'boolean']:
            raise SyntaxError(token.line, f"Неизвестный тип '{token.value}'")
        for name in names:
            self.ctx.declare_symbol(name, token.value)
        self.ctx.consume(TokenType.SEPARATOR.value, ';')

    #<оператор>::= <составной> | <присваивания> | <условный> | <фиксированного_цикла> | <условного_цикла> | <ввода> | <вывода>
    def operator(self):
        self.ctx.skip_layout()
        token = self.ctx.current()
        if not token:
            raise SyntaxError(0, "Неожиданный конец файла")
        elif token.type == TokenType.IDENTIFIER.value or self.ctx.current().value == 'let':
            self.assignment()
        elif token.value == '{':
            self.compound()
        elif token.value == 'if':
            self.conditional()
        elif token.value == 'for':
            self.fixed_loop()
        elif token.value == 'do':
            self.conditional_loop()
        elif token.value == 'input':
            self.input_op()
        elif token.value == 'output':
            self.output_op()
        else:
            raise SyntaxError(token.line, f"Неожиданный токен '{token.value}'")

    # <составной>::= «{» <оператор> { ; <оператор> } «}»
    def compound(self):
        self.ctx.consume(TokenType.SEPARATOR.value, '{')
        self.ctx.skip_layout()
        self.operator()
        while self.ctx.current() and self.ctx.current().value == ';':
            self.ctx.consume(TokenType.SEPARATOR.value, ';')
            self.ctx.skip_layout()
            self.operator()
        self.ctx.skip_layout()
        self.ctx.consume(TokenType.SEPARATOR.value, '}')

    # <условный>::= if <выражение> then <оператор> [else <оператор>] end_else
    def conditional(self):
        self.ctx.consume(TokenType.KEYWORD.value, 'if')
        self.ctx.skip_layout()
        cond = self.expression()
        if cond['type'] != 'boolean':
            raise SemanticError(self.ctx.current().line, f"Условие if должно быть логическим, получен тип '{cond['type']}'")
        self.ctx.consume(TokenType.KEYWORD.value, 'then')
        self.ctx.skip_layout()
        self.operator()
        self.ctx.skip_layout()
        if self.ctx.current() and self.ctx.current().value == 'else':
            self.ctx.consume(TokenType.KEYWORD.value, 'else')
            self.operator()
        self.ctx.skip_layout()
        self.ctx.consume(TokenType.KEYWORD.value, 'end_else')

    # <фиксированного_цикла>::= for «(» [<выражение>] ; [<выражение>] ; [<выражение>] «)» <оператор>
    def fixed_loop(self):
        self.ctx.consume(TokenType.KEYWORD.value, 'for')
        self.ctx.skip_layout()
        self.ctx.consume(TokenType.SEPARATOR.value, '(')
        if self.ctx.current() and self.ctx.current().value != ';':
            self.ctx.skip_layout()
            self.expression()
            self.ctx.skip_layout()
        self.ctx.consume(TokenType.SEPARATOR.value, ';')
        if self.ctx.current() and self.ctx.current().value != ';':
            self.ctx.skip_layout()
            self.expression()
            self.ctx.skip_layout()
        self.ctx.consume(TokenType.SEPARATOR.value, ';')
        if self.ctx.current() and self.ctx.current().value != ')':
            self.ctx.skip_layout()
            self.expression()
            self.ctx.skip_layout()
        self.ctx.consume(TokenType.SEPARATOR.value, ')')
        self.operator()

    # <условного_цикла>::= do while <выражение> <оператор> loop
    def conditional_loop(self):
        self.ctx.consume(TokenType.KEYWORD.value, 'do')
        self.ctx.skip_layout()
        self.ctx.consume(TokenType.KEYWORD.value, 'while')
        self.ctx.skip_layout()
        self.expression()
        self.operator()
        self.ctx.skip_layout()
        self.ctx.consume(TokenType.KEYWORD.value, 'loop')

    # <ввода>::= input «(»<идентификатор> {пробел <идентификатор>}«)»
    def input_op(self):
        self.ctx.consume(TokenType.KEYWORD.value, 'input')
        self.ctx.consume(TokenType.SEPARATOR.value, '(')
        self.ctx.consume(TokenType.IDENTIFIER.value)
        while self.ctx.current() and self.ctx.current().value == ' ':
            # Здесь нам нужно потребить реальный токен пробела, не пропуская его.
            self.ctx.consume(TokenType.SEPARATOR.value, ' ', skip=False)
            self.ctx.consume(TokenType.IDENTIFIER.value)
        self.ctx.consume(TokenType.SEPARATOR.value, ')')

    # <вывода>::= output «(»<выражение> { пробел <выражение> }«)»
    def output_op(self):
        self.ctx.consume(TokenType.KEYWORD.value, 'output')
        self.ctx.consume(TokenType.SEPARATOR.value, '(')
        self.expression()
        while self.ctx.current() and self.ctx.current().value == ' ':
            self.ctx.consume(TokenType.SEPARATOR.value, ' ')
            self.expression()
        self.ctx.consume(TokenType.SEPARATOR.value, ')')

    # <присваивания> ::= [ let ] <идентификатор> = <выражение>
    def assignment(self):
        if self.ctx.current().value == 'let':
            self.ctx.consume(TokenType.KEYWORD.value, 'let')
        self.ctx.skip_layout()
        name = self.ctx.consume(TokenType.IDENTIFIER.value)
        self.ctx.skip_layout()
        self.ctx.consume(TokenType.SEPARATOR.value, '=')
        self.ctx.skip_layout()
        expr_type = self.expression()
        var_type = self.ctx.get_type(name.value)
        if var_type != expr_type['type']:
            raise SemanticError(name.line, f"Несовпадение типов в присваивании: '{var_type}' и '{expr_type['type']}'")

    # <выражение>::= <операнд>{<операции_группы_отношения> <операнд>}
    def expression(self):
        left = self.operand()
        self.ctx.skip_layout()
        while self.ctx.current() and self.ctx.current().value in ['NE', 'EQ', 'LT', 'LE', 'GT', 'GE']:
            op = self.ctx.consume(TokenType.SEPARATOR.value)
            self.ctx.skip_layout()
            right = self.operand()
            if left['type'] != right['type']:
                raise SemanticError(op.line, f"Несовпадение типов в операции отношения: '{left['type']}' и '{right['type']}'")
            elif left['type'] not in ('integer', 'real', 'boolean'):
                raise SemanticError(op.line, f"Сравнение несравнимых типов: '{left['type']}'")
            left = {'type': 'boolean', 'value': f"{left['value']} {op.value} {right['value']}"}  
        return left
    
    # <операнд>::= <слагаемое> {<операции_группы_сложения> <слагаемое>}
    def operand(self):
        left = self.addend()
        self.ctx.skip_layout()
        while self.ctx.current() and self.ctx.current().value in ['plus', 'min', 'or']:
            op = self.ctx.consume(TokenType.SEPARATOR.value)
            self.ctx.skip_layout()
            right = self.addend()
            if left['type'] != right['type']:
                raise SemanticError(op.line, f"Несовпадение типов в операции сложения: '{left['type']}' и '{right['type']}'")
            left = {'type': left['type'], 'value': f"{left['value']} {op.value} {right['value']}"}  
        return left

    # <слагаемое>::= <множитель> {<операции_группы_умножения><множитель>}
    def addend(self):
        left = self.unary()
        self.ctx.skip_layout()
        while self.ctx.current() and self.ctx.current().value in ['mult', 'div', 'and']:
            op = self.ctx.consume(TokenType.SEPARATOR.value)
            self.ctx.skip_layout()
            right = self.unary()
            if left['type'] != right['type']:
                raise SemanticError(op.line, f"Несовпадение типов в операции умножения: '{left['type']}' и '{right['type']}'")
            if op.value == 'div' and (left['type'] == 'integer' and right['type'] == 'integer'):
                raise SemanticError(op.line, "Операция 'div' недопустима для integer")
            left = {'type': left['type'], 'value': f"{left['value']} {op.value} {right['value']}"}
        return left
    
    # <унарная_операция>::= ~
    def unary(self):
        if self.ctx.current().value == '~':
            op = self.ctx.consume(TokenType.SEPARATOR.value, '~')
            operand = self.unary()
            if operand['type'] != 'boolean':
                raise SemanticError(op.line, f"Несовпадение типов в унарной операции: '{operand['type']}'")
            return {'type': 'boolean', 'value': f"~{operand['value']}"}
        return self.multiplier()
    
    # <множитель>::= <идентификатор> | <число> | <логическая_константа> | <унарная_операция> <множитель> | « (»<выражение>«)»
    def multiplier(self):
        token = self.ctx.current()
        if not token:
            raise SyntaxError(0, "Неожиданный конец файла")
        if token.type == TokenType.IDENTIFIER.value:
            name = self.ctx.consume(TokenType.IDENTIFIER.value).value
            var_type = self.ctx.get_type(name)
            return {'type': var_type, 'value': name}
        elif token.type == TokenType.NUMBER.value:
            value = self.ctx.consume(TokenType.NUMBER.value).value
            raw = token.raw_value
            if '.' in value:
                return {'type': 'real', 'value': raw}
            else:
                return {'type': 'integer', 'value': raw}
        elif token.type == TokenType.KEYWORD.value and token.value in ['true', 'false']:
            value = self.ctx.consume(TokenType.KEYWORD.value).value
            return {'type': 'boolean', 'value': value}
        elif token.value == '(':
            self.ctx.consume(TokenType.SEPARATOR.value, '(')
            expr = self.expression()
            self.ctx.consume(TokenType.SEPARATOR.value, ')')
            return expr
        else:
            raise SyntaxError(token.line, f"Неожиданный токен '{token.value}'")
    
    def parse(self):
        self.program()