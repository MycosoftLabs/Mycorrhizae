"""
HPL Interpreter - Hypha Programming Language Execution Engine

Executes HPL programs with biological metaphor semantics.
"""

from typing import Any, Dict, List, Optional

from .lexer import HPLLexer, Token, TokenType
from .builtins import HPLBuiltins, SensorContext


class HPLInterpreter:
    """
    Interpreter for the Hypha Programming Language.
    
    Executes HPL programs with support for:
    - Variable declarations (hypha)
    - Sensor reading (sense)
    - Signal emission (emit)
    - Conditional logic (branch)
    - Loops (grow)
    - Cleanup (decay)
    """
    
    def __init__(self, context: SensorContext, emit_callback=None):
        self.context = context
        self.builtins = HPLBuiltins(context, emit_callback)
        self.variables: Dict[str, Any] = {}
        self.tokens: List[Token] = []
        self.pos = 0
    
    @property
    def current_token(self) -> Optional[Token]:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 1) -> Optional[Token]:
        """Peek at token ahead."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]
    
    def advance(self) -> Optional[Token]:
        """Advance to next token."""
        token = self.current_token
        self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        """Expect and consume a token of specific type."""
        token = self.current_token
        if not token or token.type != token_type:
            raise SyntaxError(f"Expected {token_type}, got {token}")
        self.advance()
        return token
    
    def skip_newlines(self) -> None:
        """Skip newline and comment tokens."""
        while self.current_token and self.current_token.type in (TokenType.NEWLINE, TokenType.COMMENT):
            self.advance()
    
    def execute(self, source: str) -> Dict[str, Any]:
        """
        Execute an HPL program.
        
        Returns the execution context including outputs and alerts.
        """
        lexer = HPLLexer(source)
        self.tokens = lexer.tokenize()
        self.pos = 0
        self.variables = {}
        
        # Execute statements
        while self.current_token and self.current_token.type != TokenType.EOF:
            self.skip_newlines()
            
            if not self.current_token or self.current_token.type == TokenType.EOF:
                break
            
            self.execute_statement()
        
        return {
            "variables": self.variables,
            "outputs": self.context.outputs,
            "alerts": self.context.alerts,
        }
    
    def execute_statement(self) -> Any:
        """Execute a single statement."""
        token = self.current_token
        
        if not token:
            return None
        
        # Variable declaration: hypha name = value
        if token.type == TokenType.HYPHA:
            return self.execute_hypha()
        
        # Sensor read: sense("sensor_id")
        if token.type == TokenType.SENSE:
            return self.execute_sense()
        
        # Signal emit: emit("channel", payload)
        if token.type == TokenType.EMIT:
            return self.execute_emit()
        
        # Conditional: branch condition { ... }
        if token.type == TokenType.BRANCH:
            return self.execute_branch()
        
        # Loop: grow name { ... }
        if token.type == TokenType.GROW:
            return self.execute_grow()
        
        # Final output: fruit("name", value)
        if token.type == TokenType.FRUIT:
            return self.execute_fruit()
        
        # Cleanup: decay("name")
        if token.type == TokenType.DECAY:
            return self.execute_decay()
        
        # Function call or expression
        if token.type == TokenType.IDENTIFIER:
            return self.execute_expression()
        
        # Skip unknown
        self.advance()
        return None
    
    def execute_hypha(self) -> Any:
        """Execute hypha (variable declaration)."""
        self.expect(TokenType.HYPHA)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.ASSIGN)
        value = self.execute_expression()
        
        self.variables[name] = value
        self.context.set_variable(name, value)
        
        return value
    
    def execute_sense(self) -> Optional[float]:
        """Execute sense (sensor read)."""
        self.expect(TokenType.SENSE)
        self.expect(TokenType.LPAREN)
        
        sensor_id = self.expect(TokenType.STRING).value
        
        field = "value"
        if self.current_token and self.current_token.type == TokenType.COMMA:
            self.advance()
            field = self.expect(TokenType.STRING).value
        
        self.expect(TokenType.RPAREN)
        
        return self.builtins.sense(sensor_id, field)
    
    def execute_emit(self) -> None:
        """Execute emit (signal output)."""
        self.expect(TokenType.EMIT)
        self.expect(TokenType.LPAREN)
        
        channel = self.expect(TokenType.STRING).value
        self.expect(TokenType.COMMA)
        payload = self.parse_object()
        
        self.expect(TokenType.RPAREN)
        
        self.builtins.emit(channel, payload)
    
    def execute_branch(self) -> Any:
        """Execute branch (conditional)."""
        self.expect(TokenType.BRANCH)
        
        condition = self.execute_expression()
        
        self.expect(TokenType.LBRACE)
        
        result = None
        if condition:
            # Execute block
            while self.current_token and self.current_token.type != TokenType.RBRACE:
                self.skip_newlines()
                if self.current_token.type == TokenType.RBRACE:
                    break
                result = self.execute_statement()
        else:
            # Skip block
            depth = 1
            while depth > 0 and self.current_token:
                if self.current_token.type == TokenType.LBRACE:
                    depth += 1
                elif self.current_token.type == TokenType.RBRACE:
                    depth -= 1
                self.advance()
            return None
        
        self.expect(TokenType.RBRACE)
        
        return result
    
    def execute_grow(self) -> List[float]:
        """Execute grow (accumulation loop)."""
        self.expect(TokenType.GROW)
        
        name = self.expect(TokenType.IDENTIFIER).value
        value = self.execute_expression()
        
        return self.builtins.grow(name, value)
    
    def execute_fruit(self) -> Dict[str, Any]:
        """Execute fruit (final output)."""
        self.expect(TokenType.FRUIT)
        self.expect(TokenType.LPAREN)
        
        name = self.expect(TokenType.STRING).value
        self.expect(TokenType.COMMA)
        value = self.execute_expression()
        
        self.expect(TokenType.RPAREN)
        
        return self.builtins.fruit(name, value)
    
    def execute_decay(self) -> None:
        """Execute decay (cleanup)."""
        self.expect(TokenType.DECAY)
        self.expect(TokenType.LPAREN)
        
        name = self.expect(TokenType.STRING).value
        
        self.expect(TokenType.RPAREN)
        
        self.builtins.decay(name)
    
    def execute_expression(self) -> Any:
        """Execute an expression."""
        return self.parse_comparison()
    
    def parse_comparison(self) -> Any:
        """Parse comparison expression."""
        left = self.parse_additive()
        
        while self.current_token and self.current_token.type in (
            TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE
        ):
            op = self.advance()
            right = self.parse_additive()
            
            if op.type == TokenType.EQ:
                left = left == right
            elif op.type == TokenType.NE:
                left = left != right
            elif op.type == TokenType.LT:
                left = left < right
            elif op.type == TokenType.GT:
                left = left > right
            elif op.type == TokenType.LE:
                left = left <= right
            elif op.type == TokenType.GE:
                left = left >= right
        
        return left
    
    def parse_additive(self) -> Any:
        """Parse additive expression (+, -)."""
        left = self.parse_multiplicative()
        
        while self.current_token and self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            right = self.parse_multiplicative()
            
            if op.type == TokenType.PLUS:
                left = left + right
            else:
                left = left - right
        
        return left
    
    def parse_multiplicative(self) -> Any:
        """Parse multiplicative expression (*, /, %)."""
        left = self.parse_primary()
        
        while self.current_token and self.current_token.type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance()
            right = self.parse_primary()
            
            if op.type == TokenType.STAR:
                left = left * right
            elif op.type == TokenType.SLASH:
                left = left / right if right != 0 else 0
            else:
                left = left % right if right != 0 else 0
        
        return left
    
    def parse_primary(self) -> Any:
        """Parse primary expression (literal, variable, function call)."""
        token = self.current_token
        
        if not token:
            return None
        
        # Number literal
        if token.type == TokenType.NUMBER:
            self.advance()
            return float(token.value) if "." in token.value else int(token.value)
        
        # String literal
        if token.type == TokenType.STRING:
            self.advance()
            return token.value
        
        # Parenthesized expression
        if token.type == TokenType.LPAREN:
            self.advance()
            value = self.execute_expression()
            self.expect(TokenType.RPAREN)
            return value
        
        # Object literal
        if token.type == TokenType.LBRACE:
            return self.parse_object()
        
        # sense() call
        if token.type == TokenType.SENSE:
            return self.execute_sense()
        
        # Variable or function call
        if token.type == TokenType.IDENTIFIER:
            name = self.advance().value
            
            # Function call
            if self.current_token and self.current_token.type == TokenType.LPAREN:
                return self.execute_function_call(name)
            
            # Variable reference
            return self.variables.get(name, self.context.get_variable(name))
        
        return None
    
    def parse_object(self) -> Dict[str, Any]:
        """Parse object literal."""
        self.expect(TokenType.LBRACE)
        
        obj = {}
        
        while self.current_token and self.current_token.type != TokenType.RBRACE:
            self.skip_newlines()
            
            if self.current_token.type == TokenType.RBRACE:
                break
            
            # Key
            if self.current_token.type == TokenType.STRING:
                key = self.advance().value
            elif self.current_token.type == TokenType.IDENTIFIER:
                key = self.advance().value
            else:
                break
            
            self.expect(TokenType.COLON)
            value = self.execute_expression()
            obj[key] = value
            
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RBRACE)
        
        return obj
    
    def execute_function_call(self, name: str) -> Any:
        """Execute a function call."""
        self.expect(TokenType.LPAREN)
        
        args = []
        while self.current_token and self.current_token.type != TokenType.RPAREN:
            args.append(self.execute_expression())
            
            if self.current_token and self.current_token.type == TokenType.COMMA:
                self.advance()
        
        self.expect(TokenType.RPAREN)
        
        # Built-in functions
        if hasattr(self.builtins, name):
            func = getattr(self.builtins, name)
            return func(*args)
        
        return None
