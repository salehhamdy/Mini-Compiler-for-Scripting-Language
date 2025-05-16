from typing import List, Optional
from enum import Enum
from tokens import Token, TokenType
from parse_tree import ParseTreeNode


class SyntaxError(Exception):
    def __init__(self, message: str, line: int, position: int):
        super().__init__(f"Syntax Error at line {line}, position {position}: {message}")
        self.message = message
        self.line = line
        self.position = position


class SyntaxValidator:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0
        self.scope_stack = []
        self.in_function = False
        self.had_return = False
        self.parse_tree = ParseTreeNode("Program")  # Root node for the parse tree

    def validate(self) -> bool:
        while not self._is_at_end():
            statement_node = self._validate_statement()
            if statement_node:
                self.parse_tree.add_child(statement_node)

        if self.scope_stack:
            unclosed_scope = self.scope_stack.pop()
            raise SyntaxError(
                f"Unclosed {unclosed_scope} statement",
                self._peek().line,
                self._peek().position
            )
        return True

    def _validate_statement(self) -> Optional[ParseTreeNode]:
        token = self._peek()

        # Recognize various statements
        validation_map = {
            TokenType.LET: self._validate_let_statement,
            TokenType.IF: self._validate_if_statement,
            TokenType.WHILE: self._validate_while_statement,
            TokenType.FOR: self._validate_for_statement,
            TokenType.DO: self._validate_do_while_statement,
            TokenType.REPEAT: self._validate_repeat_until_statement,
            TokenType.FUNC: self._validate_function_definition,
            TokenType.RETURN: self._validate_return_statement,
        }

        if token.type in validation_map:
            return validation_map[token.type]()

        # Handle assignment statements without 'LET'
        if token.type == TokenType.IDENTIFIER:
            return self._validate_assignment()

        raise SyntaxError(
            f"Unexpected token: {token.lexeme}",
            token.line,
            token.position
        )

    def _validate_assignment(self) -> ParseTreeNode:
        node = ParseTreeNode("Assignment")
        identifier = self._consume(TokenType.IDENTIFIER, "Expected identifier for assignment")
        node.add_child(ParseTreeNode(f"Identifier: {identifier.lexeme}"))

        if self._match(TokenType.EQUAL):
            node.add_child(ParseTreeNode("="))
        elif self._match(TokenType.PLUS_EQUAL):
            node.add_child(ParseTreeNode("+="))
        elif self._match(TokenType.MULTIPLY_EQUAL):
            node.add_child(ParseTreeNode("*="))
        else:
            raise SyntaxError(
                "Expected '=', '+=', or '*=' for assignment",
                self._peek().line,
                self._peek().position
            )

        expression_node = self._validate_expression()
        node.add_child(expression_node)
        return node

    def _validate_let_statement(self) -> ParseTreeNode:
        self._consume(TokenType.LET, "Expected 'LET'")
        identifier = self._consume(TokenType.IDENTIFIER, "Expected identifier after 'LET'")
        self._consume(TokenType.EQUAL, "Expected '=' after identifier")
        expression_node = self._validate_expression()

        node = ParseTreeNode("LetStatement")
        node.add_child(ParseTreeNode(f"Identifier: {identifier.lexeme}"))
        node.add_child(expression_node)
        return node

    def _validate_expression(self) -> ParseTreeNode:
        node = ParseTreeNode("Expression")
        term = self._validate_term()
        node.add_child(term)

        while self._is_arithmetic_operator():
            operator = self._advance()
            node.add_child(ParseTreeNode(f"Operator: {operator.lexeme}"))
            term = self._validate_term()
            node.add_child(term)

        return node


    def _validate_term(self) -> ParseTreeNode:
        if self._match(TokenType.NUMBER):
            return ParseTreeNode(f"Literal: {self._previous().lexeme}")

        if self._match(TokenType.IDENTIFIER):
            return ParseTreeNode(f"Identifier: {self._previous().lexeme}")

        if self._match(TokenType.LEFT_PAREN):
            node = self._validate_expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return node

        raise SyntaxError(
            "Expected a valid term",
            self._peek().line,
            self._peek().position
        )

    def _validate_if_statement(self) -> ParseTreeNode:
        self._consume(TokenType.IF, "Expected 'IF'")
        condition_node = self._validate_condition()  # Validate the condition

        if_node = ParseTreeNode("IfStatement")
        if_node.add_child(condition_node)  # Add the condition to the IF node

        self._consume(TokenType.THEN, "Expected 'THEN' after condition")
        self.scope_stack.append("IF")

        # Parse THEN block
        then_block = self._validate_block(TokenType.ENDIF, TokenType.ELSE)
        then_block_node = ParseTreeNode("ThenBlock")
        then_block_node.add_child(then_block)
        if_node.add_child(then_block_node)

        # Parse ELSE block if present
        if self._match(TokenType.ELSE):
            else_block = self._validate_block(TokenType.ENDIF)
            else_block_node = ParseTreeNode("ElseBlock")
            else_block_node.add_child(else_block)
            if_node.add_child(else_block_node)

        self.scope_stack.pop()
        return if_node



    def _validate_block(self, end_token: TokenType) -> ParseTreeNode:
        block_node = ParseTreeNode("Block")
        while not self._check(end_token):
            block_node.add_child(self._validate_statement())

        self._consume(end_token, f"Expected '{end_token.name}'")
        return block_node

    def _validate_while_statement(self) -> ParseTreeNode:
        self._consume(TokenType.WHILE, "Expected 'WHILE'")
        
        # Validate the condition
        condition_node = self._validate_condition()
        while_node = ParseTreeNode("WhileStatement")
        while_node.add_child(condition_node)  # Add the condition to the WHILE node
        
        # Consume the DO token
        self._consume(TokenType.DO, "Expected 'DO' after condition")
        self.scope_stack.append("WHILE")
        
        # Validate the block inside the WHILE loop
        block_node = self._validate_block(TokenType.ENDWHILE)
        while_node.add_child(block_node)
        
        self.scope_stack.pop()
        return while_node


    def _validate_for_statement(self) -> ParseTreeNode:
        self._consume(TokenType.FOR, "Expected 'FOR'")
        identifier = self._consume(TokenType.IDENTIFIER, "Expected loop variable")
        self._consume(TokenType.EQUAL, "Expected '=' in for loop")
        start_expression = self._validate_expression()
        self._consume(TokenType.TO, "Expected 'TO' in for loop")
        end_expression = self._validate_expression()

        step_expression = None
        if self._match(TokenType.STEP):
            step_expression = self._validate_expression()

        self._consume(TokenType.DO, "Expected 'DO' in for loop")
        self.scope_stack.append("FOR")

        body = self._validate_block(TokenType.ENDFOR)
        self.scope_stack.pop()

        node = ParseTreeNode("ForStatement")
        node.add_child(ParseTreeNode(f"Identifier: {identifier.lexeme}"))
        node.add_child(start_expression)
        node.add_child(end_expression)
        if step_expression:
            node.add_child(step_expression)
        node.add_child(body)
        return node

    def _validate_do_while_statement(self) -> ParseTreeNode:
        self._consume(TokenType.DO, "Expected 'DO'")
        self.scope_stack.append("DO")

        do_while_node = ParseTreeNode("DoWhileStatement")

        # Validate statements inside the DO block
        while not self._check(TokenType.WHILE):
            statement_node = self._validate_statement()
            if statement_node:
                do_while_node.add_child(statement_node)

        self._consume(TokenType.WHILE, "Expected 'WHILE'")
        condition_node = self._validate_condition()  # Validate the WHILE condition
        do_while_node.add_child(condition_node)
        self.scope_stack.pop()

        return do_while_node


    def _validate_repeat_until_statement(self) -> ParseTreeNode:
        self._consume(TokenType.REPEAT, "Expected 'REPEAT'")
        self.scope_stack.append("REPEAT")

        repeat_node = ParseTreeNode("RepeatUntilStatement")
        block_node = ParseTreeNode("Block")

        # Parse the block of statements inside the REPEAT loop
        while not self._check(TokenType.UNTIL):
            statement_node = self._validate_statement()
            if statement_node:
                block_node.add_child(statement_node)

        repeat_node.add_child(block_node)
        
        self._consume(TokenType.UNTIL, "Expected 'UNTIL'")
        condition_node = self._validate_condition()  # Parse the condition after UNTIL
        repeat_node.add_child(condition_node)

        self.scope_stack.pop()
        return repeat_node



    def _validate_function_definition(self) -> ParseTreeNode:
        self._consume(TokenType.FUNC, "Expected 'FUNC'")
        identifier = self._consume(TokenType.IDENTIFIER, "Expected function name")
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after function name")
        parameters_node = self._validate_parameter_list()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters")
        self._consume(TokenType.BEGIN, "Expected 'BEGIN' to start function body")
        
        self.scope_stack.append("FUNC")
        function_node = ParseTreeNode("FunctionDefinition")
        function_node.add_child(ParseTreeNode(f"Identifier: {identifier.lexeme}"))
        function_node.add_child(parameters_node)
        
        self.in_function = True
        self.had_return = False

        body_node = self._validate_block(TokenType.END)
        function_node.add_child(body_node)

        if not self.had_return:
            raise SyntaxError(
                "Function must have at least one RETURN statement",
                self._peek().line,
                self._peek().position
            )

        self.scope_stack.pop()
        self.in_function = False
        self.had_return = False
        return function_node



    def _validate_return_statement(self) -> ParseTreeNode:
        self._consume(TokenType.RETURN, "Expected 'RETURN'")
        return_node = ParseTreeNode("ReturnStatement")
        
        if not self._check(TokenType.END):  # Ensure it's not the end of the block
            expression_node = self._validate_expression()
            return_node.add_child(expression_node)

        self.had_return = True
        return return_node


    def _validate_function_call(self) -> ParseTreeNode:
        self._consume(TokenType.CALL, "Expected 'CALL'")
        function_name = self._consume(TokenType.IDENTIFIER, "Expected function name")
        call_node = ParseTreeNode("FunctionCall")
        call_node.add_child(ParseTreeNode(f"FunctionName: {function_name.lexeme}"))
        
        if self._match(TokenType.LEFT_PAREN):
            parameters_node = self._validate_parameter_list()
            call_node.add_child(parameters_node)
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters")
        return call_node



    def _validate_parameter_list(self) -> ParseTreeNode:
        node = ParseTreeNode("ParameterList")
        
        if not self._check(TokenType.RIGHT_PAREN):  # Ensure the list is not empty
            while True:
                param = self._consume(TokenType.IDENTIFIER, "Expected parameter name")
                node.add_child(ParseTreeNode(f"Parameter: {param.lexeme}"))
                if not self._match(TokenType.COMMA):  # Check for the next parameter
                    break
        return node


    # ----------------------------------------
    # Utility Functions
    # ----------------------------------------

    def _validate_block(self, end_token: TokenType, optional_mid_token: Optional[TokenType] = None) -> ParseTreeNode:
        """
        Validate a block of statements until an end token.
        Args:
            end_token (TokenType): the end token of the block.
            optional_mid_token (Optional[TokenType]): optional token that can appear within the block.
        """
        block_node = ParseTreeNode("Block")
        
        while not self._check(end_token) and (optional_mid_token is None or not self._check(optional_mid_token)):
            statement_node = self._validate_statement()
            if statement_node:
                block_node.add_child(statement_node)  # Correctly add statement nodes to the block

        if optional_mid_token and self._match(optional_mid_token):
            while not self._check(end_token):
                statement_node = self._validate_statement()
                if statement_node:
                    block_node.add_child(statement_node)  # Correctly add statement nodes to the block

        self._consume(end_token, f"Expected '{end_token.name}' to close the block")
        return block_node


    def _validate_condition(self) -> ParseTreeNode:
        condition_node = ParseTreeNode("Condition")  # Create a new Condition node

        # Validate the left-hand side expression
        left_expression = self._validate_expression()
        condition_node.add_child(left_expression)

        # Validate the comparison operator
        if self._peek().type in {TokenType.EQUAL, TokenType.NOT_EQUAL, TokenType.GREATER, TokenType.LESS,
                                TokenType.GREATER_EQUAL, TokenType.SMALLER_EQUAL}:
            operator = self._advance()  # Consume the operator
            condition_node.add_child(ParseTreeNode(f"Operator: {operator.lexeme}"))

            # Validate the right-hand side expression
            right_expression = self._validate_expression()
            condition_node.add_child(right_expression)
        else:
            raise SyntaxError(
                f"Expected a valid comparison operator, but got: {self._peek().lexeme}",
                self._peek().line,
                self._peek().position
            )

        return condition_node


    def _validate_expression(self) -> ParseTreeNode:
        node = ParseTreeNode("Expression")
        term = self._validate_term()
        node.add_child(term)

        while self._is_arithmetic_operator():
            operator = self._advance()
            node.add_child(ParseTreeNode(f"Operator: {operator.lexeme}"))
            term = self._validate_term()
            node.add_child(term)

        return node

    def _validate_term(self) -> ParseTreeNode:
        if self._match(TokenType.NUMBER) or self._match(TokenType.STRING):
            return ParseTreeNode(f"Literal: {self._previous().lexeme}")

        if self._match(TokenType.IDENTIFIER):  # Handle identifiers as valid terms
            return ParseTreeNode(f"Identifier: {self._previous().lexeme}")

        if self._match(TokenType.LEFT_PAREN):  # Handle expressions within parentheses
            node = self._validate_expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return node
        
        if self._match(TokenType.LEFT_BRACKET):
            if not self._check(TokenType.RIGHT_BRACKET):
                self._validate_expression()
                while self._match(TokenType.COMMA):
                    self._validate_expression()
            self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after array elements")
            return
        
        # array access: arr[index] or arr[row][col]
        if self._match(TokenType.IDENTIFIER):
            while self._match(TokenType.LEFT_BRACKET):
                self._validate_expression()
                self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after index")
            return
        
        if self._match(TokenType.LEFT_PAREN):
            self._validate_expression()
            self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression")
            return
        
        if self._match(TokenType.CALL):
            self._consume(TokenType.IDENTIFIER, "Expected function name")
            if self._match(TokenType.LEFT_PAREN):
                self._validate_expression()
                while self._match(TokenType.COMMA):
                    self._validate_expression()
                self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters")
            return
        
        raise SyntaxError("Expected a valid term", self._peek().line, self._peek().position) 
    
    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self.tokens[self.current - 1]

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _check(self, token_type: TokenType) -> bool:
        return not self._is_at_end() and self._peek().type == token_type

    def _match(self, token_type: TokenType) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _consume(self, token_type: TokenType, error_message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise SyntaxError(error_message, self._peek().line, self._peek().position)

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _is_arithmetic_operator(self) -> bool:
        return self._peek().type in {TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE}

    def _is_compound_assignment_ahead(self) -> bool:
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type in {
            TokenType.PLUS_EQUAL,
            TokenType.MINUS_EQUAL,
            TokenType.MULTIPLY_EQUAL,
            TokenType.DIVIDE_EQUAL,
        }

    def _is_increment_decrement(self) -> bool:
        return self._peek().type in {TokenType.INCREMENT, TokenType.DECREMENT}

    def _validate_increment_decrement(self):
        self._consume(TokenType.IDENTIFIER, "Expected identifier before increment/decrement")
        if not self._match(TokenType.INCREMENT) and not self._match(TokenType.DECREMENT):
            raise SyntaxError(
                "Expected '++' or '--'",
                self._peek().line,
                self._peek().position
            )

    def _check_next(self, token_type: TokenType) -> bool:
        """Check if the next token without consuming it."""
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == token_type

    def _validate_parameter_list(self):
        if self._match(TokenType.IDENTIFIER):
            while self._match(TokenType.COMMA):
                self._consume(TokenType.IDENTIFIER, "Expected parameter name after ','")

    def _validate_compound_assignment(self):
        """Validate compound assignment statements like +=, -=, *=, /="""
        self._consume(TokenType.IDENTIFIER, "Expected identifier before compound assignment")
        if not self._match(TokenType.PLUS_EQUAL) and \
        not self._match(TokenType.MINUS_EQUAL) and \
        not self._match(TokenType.MULTIPLY_EQUAL) and \
        not self._match(TokenType.DIVIDE_EQUAL):
            raise SyntaxError(
                "Expected '+=', '-=', '*=' or '/='",
                self._peek().line,
                self._peek().position
            )
        self._validate_expression()
    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1] if self.current > 0 else None
