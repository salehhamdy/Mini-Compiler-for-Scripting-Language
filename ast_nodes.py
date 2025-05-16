from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Node:
    def __str__(self, level=0):
        return "|-- " + f"{self.__class__.__name__}\n"


@dataclass
class Program(Node):
    statements: List[Node]

    def __str__(self, level=0):
        result = "Program\n"
        result += "|-- statements_block\n"
        for stmt in self.statements:
            lines = stmt.__str__(0).split('\n')
            for line in lines:
                if line:  # Skip empty lines
                    result += "|   |-- " + line.lstrip("|-- ") + "\n"
        result += "|-- End\n"
        return result


@dataclass
class LetStatement(Node):
    identifier: str
    expression: Node

    def __str__(self, level=0):
        result = "declare_statement\n"
        result += "|-- let: LET\n"
        result += f"|-- id: {self.identifier}\n"
        result += "|-- equal: =\n"
        if isinstance(self.expression, BinaryOperation):
            result += "|-- expression\n"
            result += "|   |-- " + self.expression.left.__str__(0)
            result += "|   |-- operation: " + self.expression.operator + "\n"
            result += "|   |-- " + self.expression.right.__str__(0)
        else:
            result += "|-- " + self.expression.__str__(0)
        return result


@dataclass
class BinaryOperation(Node):
    left: Node
    operator: str
    right: Node

    def __str__(self, level=0):
        result = "expression\n"
        result += "|-- " + self.left.__str__(0)
        result += f"|-- operation: {self.operator}\n"
        result += "|-- " + self.right.__str__(0)
        return result


@dataclass
class Number(Node):
    value: str

    def __str__(self, level=0):
        return f"number: {self.value}\n"


@dataclass
class Identifier(Node):
    name: str

    def __str__(self, level=0):
        return f"id: {self.name}\n"


@dataclass
class IfStatement(Node):
    condition: Node
    then_branch: List[Node]
    else_branch: Optional[List[Node]] = None

    def __str__(self, level=0):
        result = "if_statement\n"
        result += "|-- if: IF\n"
        result += "|-- condition\n"
        if isinstance(self.condition, BinaryOperation):
            result += "|   |-- expression\n"
            result += "|   |   |-- " + self.condition.left.__str__(0)
            result += "|   |   |-- operation: " + self.condition.operator + "\n"
            result += "|   |   |-- " + self.condition.right.__str__(0)
        else:
            result += "|   |-- " + self.condition.__str__(0)
        result += "|-- then_statement\n"
        result += "|   |-- then: THEN\n"
        result += "|   |-- statements\n"
        for stmt in self.then_branch:
            stmt_lines = stmt.__str__(0).split('\n')
            for line in stmt_lines:
                if line:  # Skip empty lines
                    result += "|   |   |-- " + line.lstrip("|-- ") + "\n"
        if self.else_branch:
            result += "|-- else_statement\n"
            result += "|   |-- else: ELSE\n"
            result += "|   |-- statements\n"
            for stmt in self.else_branch:
                stmt_lines = stmt.__str__(0).split('\n')
                for line in stmt_lines:
                    if line:  # Skip empty lines
                        result += "|   |   |-- " + line.lstrip("|-- ") + "\n"
        result += "|-- endif: ENDIF\n"
        return result


@dataclass
class CallStatement(Node):
    function_name: str
    arguments: List[Node]

    def __str__(self, level=0):
        result = "call_statement\n"
        result += "|-- call: CALL\n"
        result += f"|-- id: {self.function_name}\n"
        result += "|-- left_paren: (\n"
        result += "|-- args\n"
        for i, arg in enumerate(self.arguments):
            result += "|   |-- " + arg.__str__(0)
            if i < len(self.arguments) - 1:
                result += "|   |-- comma: ,\n"
        result += "|-- right_paren: )\n"
        return result
