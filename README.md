# Mini Compiler for a Scripting Language
*A Compiler Design project – Fall 2024*

---

## Table of Contents
1. [Project Overview](#project-overview)  
2. [Features & Roadmap](#features--roadmap)  
3. [Directory Layout](#directory-layout)  
4. [Getting Started](#getting-started)  
5. [Usage](#usage)  
6. [Example](#example)  
7. [Contributing](#contributing)  
8. [License](#license)  

---

## Project Overview
This project develops a **mini compiler** that performs:

| Phase | Goal | Deadline |
|-------|------|----------|
| **Phase 1** | **Lexical Analysis** – tokenize source, build a symbol table | **25 Nov 2024** |
| **Phase 2** | **Syntax Analysis** – top-down recursive-descent parser, produce a parse tree | **6 Jan 2025** |
| **Phase 3** | **Semantic Analysis** – (bonus) type checking, symbol-table validation | _same week as Phase 2 discussion_ |

The compiler targets a *case-insensitive* scripting language with LET/IF/WHILE/FOR… blocks, list literals, compound assignments, and function calls.

> **Academic Integrity**  
> Any plagiarism will result in forfeiting all project marks.

---

## Features & Roadmap
- **Lexical Scanner**
  - Custom tokenizer (no flex/lex or similar generators).
  - Handles comments `{ … }`, operators `+ - * /`, relational `= > < !=`, and logical `and or not`.
- **Recursive-Descent Parser**
  - Grammar rooted at `Program → begin statements_block end`.
  - Emits an easily traver­sable parse tree (e.g., JSON or DOT).
- **Semantic Checks** (phase 3 bonus)
  - Undeclared-identifier detection, type compatibility, function call arity.
- **Extensible Roadmap**
  - Code-generation backend (possible future phase).
  - Continuous-integration workflow with unit tests.

---

## Directory Layout
```
mini-compiler/
├── docs/                  # PDFs, specs, and design notes
│   ├── Phase-01.pdf
│   └── Phase-0203.pdf
├── phase1-lexer/          # Scanner implementation + tests
├── phase2-parser/         # Parser, AST definitions
├── phase3-semantics/      # Semantic-analysis modules
├── examples/              # Sample source programs
└── README.md
```

---

## Getting Started
### Prerequisites
- **Python ≥ 3.11** (or any language your team selects)
- `pip install -r requirements.txt` (if applicable)

### Building from Source
```bash
# 1. Clone repo
git clone https://github.com/<your-org>/mini-compiler.git
cd mini-compiler

# 2. (Optional) set up virtualenv
python -m venv .venv && source .venv/bin/activate

# 3. Run unit tests
pytest
```

---

## Usage
Run each phase independently or in a pipeline:

```bash
# Lexical analysis only
python phase1-lexer/scanner.py  source.lang  -o tokens.json

# Parse tokens and emit parse tree
python phase2-parser/parser.py  tokens.json  -o tree.dot

# Full pipeline convenience script
python main.py  examples/demo.lang  --visualize
```

Pass `--help` to any script for flags such as `--trace`, `--dump-symbol-table`, or `--format=pretty`.

---

## Example
Input (`examples/demo.lang`)
```lang
LET a = 5
LET b = 10
IF a < b THEN
    LET c = a + b
ELSE
    LET c = a - b
ENDIF
CALL myFunction(a, b)
```

Tokenizer → Parser → Parse-tree (snippet)
```
Program
└── statements_block
    ├── declare_statement  a = 5
    ├── declare_statement  b = 10
    ├── if_statement
    │   ├── condition  a < b
    │   ├── then_block (LET c = a + b)
    │   └── else_block (LET c = a - b)
    └── call_statement  myFunction(a, b)
```

---

## Contributing
1. Fork the project ➜ create feature branch `git checkout -b feat/my-feature`  
2. Commit with conventional messages (`feat:`, `fix:`…)  
3. Open a Pull Request; at least **two** peers must review.  
4. All teammates are expected to demo and explain their code during discussion week.

---

## License
Distributed for educational purposes.  
Include your university’s honor-code statement or choose an OSS license (e.g., MIT) if appropriate.
