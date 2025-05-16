# Abdulhady Ibrahim Abdulsattar 211000768
# Ahmed Hany Zein 211002141
# Ahmed Yousef ElSayed 211001765
# Omar Khaled Abbas 211001979
class Lexer:
    def __init__(self, source_code):  # Fixed constructor
        self.source_code = source_code
        self.current_char = ''
        self.position = -1
        self.current_line = 1
        self.current_column = 0
        self.tokens = []
        self.symbol_table = {}
        self.advance()

        # Define the sets of language components
        self.keywords = [
            'LET', 'IF', 'THEN', 'ELSE', 'ENDIF', 'WHILE', 'DO', 'ENDWHILE',
            'FOR', 'TO', 'STEP', 'ENDFOR', 'FUNC', 'BEGIN', 'RETURN', 'END',
            'CALL', 'IN', 'RANGE', 'REPEAT', 'UNTIL'
        ]

        self.logical_operators = ['AND', 'OR', 'NOT']
        self.arithmetic_operators = ['+', '-', '*', '/']
        self.relational_operators = ['=', '!=', '>', '<']
        self.compound_operators = ['+=', '-=', '*=', '/=', '++', '--']
        self.delimiters = ['(', ')', '[', ']', '{', '}', ',', ':']

    def advance(self):
        self.position += 1
        if self.position < len(self.source_code):
            self.current_char = self.source_code[self.position]
            if self.current_char == '\n':
                self.current_line += 1
                self.current_column = 0
            else:
                self.current_column += 1
        else:
            self.current_char = None  # Indicates end of input

    def peek(self):
        peek_position = self.position + 1
        if peek_position < len(self.source_code):
            return self.source_code[peek_position]
        else:
            return None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comment(self):
        self.advance()  # Skip the opening '{'
        while self.current_char is not None:
            if self.current_char == '}':
                self.advance()
                return
            else:
                self.advance()
        self.error("Unclosed comment")

    def error(self, message):
        raise Exception(f'Lexing error at line {self.current_line}, column {
                        self.current_column}: {message}')

    def tokenize(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
            elif self.current_char == '{':
                self.skip_comment()
            elif self.current_char.isalpha() or self.current_char == '_':
                token = self.identify_keyword_or_identifier()
                self.tokens.append(token)
            elif self.current_char.isdigit():
                token = self.number()
                self.tokens.append(token)
            elif self.current_char in self.arithmetic_operators:
                token = self.arithmetic_operator()
                self.tokens.append(token)
            elif self.current_char in ['!', '=', '>', '<']:
                token = self.relational_operator()
                self.tokens.append(token)
            elif self.current_char == ',':
                self.tokens.append(('comma', ','))
                self.advance()
            elif self.current_char == ':':
                self.tokens.append(('colon', ':'))
                self.advance()
            elif self.current_char in self.delimiters:
                token = self.delimiter()
                self.tokens.append(token)
                self.advance()
            else:
                self.error(f"Unexpected character '{self.current_char}'")
        return self.tokens

    def identify_keyword_or_identifier(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        upper_result = result.upper()
        if upper_result in self.keywords:
            return (upper_result.lower(), result)
        elif upper_result in self.logical_operators:
            return ('operator', upper_result.lower())
        else:
            self.add_to_symbol_table(result)
            return ('identifier', result)

    def number(self):
        result = ''
        has_decimal_point = False
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            if self.current_char == '.':
                if has_decimal_point:
                    self.error(
                        "Invalid number format with multiple decimal points")
                has_decimal_point = True
            result += self.current_char
            self.advance()
        return ('number', result)

    def arithmetic_operator(self):
        result = self.current_char
        next_char = self.peek()

        # Check for compound operators (e.g., +=, ++)
        if next_char is not None and (result + next_char) in self.compound_operators:
            result += next_char
            self.advance()
            self.advance()
            return ('compound_operator', result)
        elif result in self.arithmetic_operators:
            self.advance()
            return ('operator', result)
        else:
            self.error(f"Invalid arithmetic operator '{result}'")

    def relational_operator(self):
        result = self.current_char
        next_char = self.peek()

        if result == '!' and next_char == '=':
            result += next_char
            self.advance()
            self.advance()
            return ('not_equal', result)
        elif result == '=':
            self.advance()
            return ('equal', result)
        elif result in ['>', '<']:
            self.advance()
            return ('operator', result)
        else:
            self.error(f"Invalid relational operator '{result}'")

    def delimiter(self):
        char = self.current_char
        token_type = ''
        if char == '(':
            token_type = 'left_paren'
        elif char == ')':
            token_type = 'right_paren'
        elif char == '[':
            token_type = 'left_bracket'
        elif char == ']':
            token_type = 'right_bracket'
        elif char == '{':
            token_type = 'left_brace'
        elif char == '}':
            token_type = 'right_brace'
        else:
            token_type = 'delimiter'
        return (token_type, char)

    def add_to_symbol_table(self, identifier):
        if identifier not in self.symbol_table:
            self.symbol_table[identifier] = {
                'name': identifier, 'type': 'unknown'}

    def update_symbol_table_types(self):
        index = 0
        while index < len(self.tokens):
            token, lexeme = self.tokens[index]
            if token == 'let':
                next_token, next_lexeme = self.tokens[index + 1]
                if next_token == 'identifier':
                    self.symbol_table[next_lexeme]['type'] = 'integer'
            elif token == 'func':
                next_token, next_lexeme = self.tokens[index + 1]
                if next_token == 'identifier':
                    function_name = next_lexeme
                    self.symbol_table[function_name]['type'] = 'function'
                    if self.tokens[index + 2][0] == 'left_paren':
                        params = []
                        param_index = index + 3
                        while self.tokens[param_index][0] != 'right_paren':
                            param_token, param_lexeme = self.tokens[param_index]
                            if param_token == 'identifier':
                                params.append(param_lexeme)
                            param_index += 1
                        self.symbol_table[function_name]['parameters'] = params
            elif token == 'call':
                next_token, next_lexeme = self.tokens[index + 1]
                if next_token == 'identifier':
                    function_name = next_lexeme
                    if function_name not in self.symbol_table:
                        self.symbol_table[function_name] = {
                            'name': function_name}
                    self.symbol_table[function_name]['type'] = 'function'
                    if index + 2 < len(self.tokens) and self.tokens[index + 2][0] == 'left_paren':
                        args = []
                        arg_index = index + 3
                        while arg_index < len(self.tokens) and self.tokens[arg_index][0] != 'right_paren':
                            arg_token, arg_lexeme = self.tokens[arg_index]
                            if arg_token == 'identifier':
                                args.append(arg_lexeme)
                            arg_index += 1
                        self.symbol_table[function_name]['parameters'] = args
            index += 1

    def print_tokens(self):
        print("Tokens:")
        for token, lexeme in self.tokens:
            print(f'Token: {token}, Lexeme: {lexeme}')

    def print_symbol_table(self):
        print("\nSymbol Table:")
        for name, attributes in self.symbol_table.items():
            if attributes['type'] == 'function':
                params = ', '.join(attributes.get('parameters', []))
                if params:
                    print(f'Name: {attributes["name"]}, Type: {
                          attributes["type"]} (with parameters: {params})')
                else:
                    print(f'Name: {attributes["name"]}, Type: {
                          attributes["type"]}')
            else:
                print(f'Name: {attributes["name"]}, Type: {
                      attributes["type"]}')


if __name__ == '__main__':
    source_code = """
    LET a = 5
    LET b = 10
    IF a < b 
    THEN
        LET c = a + b
        LET d = c * 2
    ELSE
        LET e = a - b
    ENDIF
    CALL myFunction(a, b)
    """
    lexer = Lexer(source_code)
    try:
        lexer.tokenize()
        lexer.update_symbol_table_types()
        lexer.print_tokens()
        lexer.print_symbol_table()
    except Exception as e:
        print(e)
