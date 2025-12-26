import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from typing import List
from tokens import KEYWORDS, SEPARATORS, Token, TokenType
from lexer import Lexer
from parser import Parser

def _get_token_code(tok: Token, lexer: Lexer) -> int:
    if tok.type == TokenType.KEYWORD:
        return KEYWORDS.index(tok.value) + 1
    elif tok.type == TokenType.SEPARATOR:
        return SEPARATORS.index(tok.value) + 1
    elif tok.type == TokenType.IDENTIFIER:
        return lexer.TI.index(tok.value) + 1
    elif tok.type == TokenType.NUMBER:
        return lexer.TN.index(tok.value) + 1
    return 0

class App:

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Компилятор языка 331233")
        self.root.geometry("1366x768")

        self._style()
        self._toolbar()
        self._layout()
        self._binds()

        self._fill_demo()
        self._update_lines()

    def _style(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#f7f7f7")
        style.configure("TLabel", background="#f7f7f7")
        style.configure("Status.TLabel", anchor="w", padding=6)

    def _toolbar(self):
        bar = ttk.Frame(self.root)
        bar.pack(side="top", fill="x")

        ttk.Button(bar, text="Открыть", command=self._open).pack(side="left", padx=4, pady=4)
        ttk.Button(bar, text="Анализ", command=self._analyze).pack(side="left")

        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Label(bar, text="Лексер + Парсер + Семантика").pack(side="left")

    def _layout(self):
        self.panes = ttk.Panedwindow(self.root, orient="horizontal")
        self.panes.pack(fill="both", expand=True)

        left = ttk.Frame(self.panes)
        self.panes.add(left, weight=3)

        editor_box = ttk.LabelFrame(left, text="Редактор")
        editor_box.pack(fill="both", expand=True, padx=6, pady=6)

        editor_pane = ttk.Panedwindow(editor_box, orient="horizontal")
        editor_pane.pack(fill="both", expand=True)

        self.lines = tk.Text(
            editor_pane,
            width=5,
            padx=6,
            takefocus=0,
            border=0,
            background="#eaeaea",
            state="disabled",
            font=("Consolas", 10)
        )
        editor_pane.add(self.lines, weight=0)

        self.input = ScrolledText(
            editor_pane,
            font=("Consolas", 10),
            wrap="none"
        )
        editor_pane.add(self.input, weight=1)

        out_box = ttk.LabelFrame(left, text="Сообщения компилятора")
        out_box.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        self.output = ScrolledText(out_box, height=8, font=("Consolas", 10))
        self.output.pack(fill="both", expand=True)

        right = ttk.Frame(self.panes)
        self.panes.add(right, weight=2)

        tabs = ttk.Notebook(right)
        tabs.pack(fill="both", expand=True, padx=6, pady=6)

        tab_kw = ttk.Frame(tabs)
        tab_sep = ttk.Frame(tabs)
        tab_id = ttk.Frame(tabs)
        tab_num = ttk.Frame(tabs)

        tabs.add(tab_kw, text="Ключевые слова")
        tabs.add(tab_sep, text="Разделители")
        tabs.add(tab_id, text="Идентификаторы")
        tabs.add(tab_num, text="Числа")

        self._table(tab_kw, [(i + 1, w) for i, w in enumerate(KEYWORDS)])
        self._table(tab_sep, [(i + 1, s) for i, s in enumerate(SEPARATORS)])
        self.tree_ti = self._table(tab_id, [])
        self.tree_tn = self._table(tab_num, [])

        self.status = ttk.Label(self.root, text="Готово", style="Status.TLabel")
        self.status.pack(side="bottom", fill="x")

    def _binds(self):
        self.input.bind("<KeyRelease>", self._update_lines)
        self.input.bind("<MouseWheel>", self._sync_scroll)
        self.lines.bind("<MouseWheel>", lambda e: "break")

        for w in (self.input, self.output):
            w.bind("<Control-c>", lambda e, x=w: self._copy(x))
            w.bind("<Control-C>", lambda e, x=w: self._copy(x))

    def _table(self, parent: ttk.Frame, data: List[tuple]):
        tree = ttk.Treeview(parent, columns=("№", "Значение"), show="headings")
        tree.heading("№", text="№", anchor="center")
        tree.heading("Значение", text="Значение", anchor="w")
        tree.column("№", width=50, anchor="center")
        tree.column("Значение", anchor="w")

        vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for row in data:
            tree.insert("", "end", values=row)

        return tree

    def _copy(self, widget):
        try:
            text = widget.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
        except tk.TclError:
            pass
        return "break"

    def _update_lines(self, event=None):
        self.lines.config(state="normal")
        self.lines.delete("1.0", tk.END)
        count = int(self.input.index("end-1c").split(".")[0])
        for i in range(1, count + 1):
            self.lines.insert(tk.END, f"{i}\n")
        self.lines.config(state="disabled")

    def _sync_scroll(self, event=None):
        self.lines.yview_moveto(self.input.yview()[0])

    def _open(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if not path:
            return
        try:
            with open(path, encoding="ascii") as f:
                self.input.delete("1.0", tk.END)
                self.input.insert("1.0", f.read())
            self._update_lines()
            self.status.config(text=f"Открыт файл: {path}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _analyze(self):
        self.output.delete("1.0", tk.END)
        for tree in (self.tree_ti, self.tree_tn):
            tree.delete(*tree.get_children())

        code = self.input.get("1.0", tk.END).strip()
        if not code:
            self.output.insert(tk.END, "⚠️ Код пуст.\n")
            return

        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()

            for tok in tokens:
                n = {
                    TokenType.KEYWORD: 1,
                    TokenType.SEPARATOR: 2,
                    TokenType.IDENTIFIER: 3,
                    TokenType.NUMBER: 4
                }[tok.type]
                z = _get_token_code(tok, lexer)
                if not tok.value.isspace():
                    self.output.insert(
                        tk.END,
                        f"({n}, {z}) — {tok.value} [строка {tok.line}]\n"
                    )

            for i, x in enumerate(lexer.TI, 1):
                self.tree_ti.insert("", "end", values=(i, x))
            for i, x in enumerate(lexer.TN, 1):
                self.tree_tn.insert("", "end", values=(i, x))

            parser = Parser(tokens)
            parser.parse()

            self.output.insert(tk.END, "\n✅ Успешно: лексика, синтаксис, семантика.\n")
            self.status.config(text="Анализ завершён успешно")

        except Exception as e:
            self.output.delete("1.0", tk.END)

            self.output.insert(
                tk.END,
                f"❌ Ошибка компиляции:\n{e}\n"
            )

            self.status.config(text="Ошибка анализа")

    def _fill_demo(self):
        self.input.insert("1.0", """(* comment *)
a, b, c : integer;
x, y : real;
bool_var, flag : boolean;
                          
binnum, octnum, hexnum : integer;
                          
expintnum : integer;
exprealnum : real;
                          
a = 10
b = 20
let c = a plus b
                          
binnum = 1010b
octnum = 12o
hexnum = 1ACh
                          
expintnum = 1E3
exprealnum = 3.14E2

x = 3.14
y = x mult 2.0

flag = true
bool_var = ~flag 

if a LT b then
{
    output(a min b);
    (* comment *)
    flag = false
}
else
{
    input(a b);
    output(a plus b)
}
end_else
for (a ; b ; c)
{
    x = x div 2.0
}

do while flag
{
    a = a min 1
}
loop
(* comment *)
output(flag)
end
""")

if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()