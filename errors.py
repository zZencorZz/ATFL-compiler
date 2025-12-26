class CompilerError(Exception):
    def __init__(self, line: int, msg: str, kind: str = "") -> None:
        self.line = line
        self.msg = msg
        prefix = f"{kind}: " if kind else ""
        super().__init__(f"[строка {line}] {prefix}{msg}")

class LexError(CompilerError):
    def __init__(self, line: int, msg: str) -> None:
        super().__init__(line, msg, "лексическая")

class SyntaxError(CompilerError):
    def __init__(self, line: int, msg: str) -> None:
        super().__init__(line, msg, "синтаксическая")

class SemanticError(CompilerError):
    def __init__(self, line: int, msg: str) -> None:
        super().__init__(line, msg, "семантическая")    