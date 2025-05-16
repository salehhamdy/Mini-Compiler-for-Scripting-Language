from typing import List, Optional
import Compiler_Project_phase1 as lexer
from ast_nodes import (
    Node, Program, LetStatement, BinaryOperation,
    Number, Identifier, IfStatement, CallStatement
)


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        """Parse the program and return AST"""
        statements = []

        # Skip any initial whitespace tokens
        while self.current < len(self.tokens) and self.tokens[self.current][0] == 'whitespace':
            self.current += 1

        # Expect BEGIN
        if not self.match('begin'):
            self.error("Expected 'BEGIN' at start of program")

        while not self.is_at_end() and not self.check('end'):
            # Skip whitespace between statements
            while self.current < len(self.tokens) and self.tokens[self.current][0] == 'whitespace':
                self.current += 1

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        # Expect END
        if not self.match('end'):
            self.error("Expected 'END' at end of program")

        return Program(statements)

    def parse_statement(self) -> Optional[Node]:
        """Parse a single statement"""
        # Skip whitespace before statement
        while self.current < len(self.tokens) and self.tokens[self.current][0] == 'whitespace':
            self.current += 1

        if self.match('let'):
            return self.parse_let_statement()
        elif self.match('if'):
            return self.parse_if_statement()
        elif self.match('call'):
            return self.parse_call_statement()
        # Add other statement types as needed
        return None

    def parse_let_statement(self) -> LetStatement:
        """Parse a let statement"""
        if not self.check('identifier'):
            self.error("Expected identifier after 'LET'")
        identifier = self.advance()[1]  # Get the lexeme

        if not self.match('equal'):
            self.error("Expected '=' after identifier in LET statement")

        expr = self.parse_expression()
        return LetStatement(identifier, expr)

    def parse_if_statement(self) -> IfStatement:
        """Parse an if statement"""
        condition = self.parse_condition()

        # Skip whitespace before THEN
        while self.current < len(self.tokens) and self.tokens[self.current][0] == 'whitespace':
            self.current += 1

        # Debug print
        print(f"Current token after condition: {
              self.tokens[self.current] if not self.is_at_end() else 'END'}")

        if not self.match('then'):
            self.error("Expected 'THEN' after condition in IF statement")

        then_statements = []
        while not self.check('else') and not self.check('endif') and not self.is_at_end():
            stmt = self.parse_statement()
            if stmt:
                then_statements.append(stmt)

        else_statements = []
        if self.match('else'):
            while not self.check('endif') and not self.is_at_end():
                stmt = self.parse_statement()
                if stmt:
                    else_statements.append(stmt)

        if not self.match('endif'):
            self.error("Expected 'ENDIF' at end of IF statement")

        return IfStatement(condition, then_statements, else_statements if else_statements else None)

    def parse_call_statement(self) -> CallStatement:
        """Parse a function call"""
        if not self.check('identifier'):
            self.error("Expected function name after 'CALL'")
        function_name = self.advance()[1]  # Get the lexeme

        if not self.match('left_paren'):
            self.error("Expected '(' after function name in CALL statement")

        arguments = []
        if not self.check('right_paren'):
            while True:
                arguments.append(self.parse_expression())
                if not self.match('comma'):
                    break

        if not self.match('right_paren'):
            self.error("Expected ')' after arguments in CALL statement")

        return CallStatement(function_name, arguments)

    def parse_expression(self) -> Node:
        """Parse an expression"""
        left = self.parse_term()

        while self.match_any(['operator']):
            operator = self.previous()[1]
            if operator not in ['+', '-']:
                self.current -= 1  # Put back the operator token
                break
            right = self.parse_term()
            left = BinaryOperation(left, operator, right)

        return left

    def parse_term(self) -> Node:
        """Parse a term"""
        left = self.parse_factor()

        while self.match_any(['operator']):
            operator = self.previous()[1]
            if operator not in ['*', '/']:
                self.current -= 1  # Put back the operator token
                break
            right = self.parse_factor()
            left = BinaryOperation(left, operator, right)

        return left

    def parse_factor(self) -> Node:
        """Parse a factor"""
        if self.match('number'):
            return Number(self.previous()[1])
        elif self.match('identifier'):
            return Identifier(self.previous()[1])
        elif self.match('left_paren'):
            expr = self.parse_expression()
            if not self.match('right_paren'):
                self.error("Expected ')' after expression")
            return expr
        self.error("Expected number, identifier, or '('")

    def parse_condition(self) -> Node:
        """Parse a condition"""
        left = self.parse_expression()

        if self.match_any(['operator', 'equal', 'not_equal']):
            operator = self.previous()[1]
            right = self.parse_expression()
            return BinaryOperation(left, operator, right)

        return left

    # Helper methods
    def match(self, expected_type: str) -> bool:
        """Check if current token matches expected type"""
        if self.check(expected_type):
            self.advance()
            return True
        return False

    def match_any(self, types: List[str]) -> bool:
        """Check if current token matches any of the expected types"""
        if self.is_at_end():
            return False
        current_type = self.tokens[self.current][0]
        for t in types:
            if current_type == t:
                self.advance()
                return True
        return False

    def check(self, expected_type: str) -> bool:
        """Check if current token is of expected type without consuming"""
        if self.is_at_end():
            return False
        return self.tokens[self.current][0] == expected_type

    def advance(self) -> tuple:
        """Consume current token and return it"""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def previous(self) -> tuple:
        """Get the previously consumed token"""
        return self.tokens[self.current - 1]

    def is_at_end(self) -> bool:
        """Check if we've reached end of tokens"""
        return self.current >= len(self.tokens)

    def error(self, message: str):
        """Handle parsing errors"""
        if self.is_at_end():
            raise Exception(f"Parse error at end of input: {message}")
        raise Exception(f"Parse error at token {
                        self.tokens[self.current]}: {message}")


def main():
    # Test the parser with the same example from phase 1
    source_code = """
    BEGIN
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
    END
    """

    # First tokenize using the lexer from phase 1
    lex = lexer.Lexer(source_code)
    tokens = lex.tokenize()

    # Debug print tokens
    print("Tokens:")
    for token in tokens:
        print(token)

    # Then parse the tokens
    parser = Parser(tokens)
    try:
        ast = parser.parse()
        print("\nParse Tree:")
        print(ast)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
