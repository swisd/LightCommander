import sys

from v2.basic import TT_MUL, TT_DIV, TT_PLUS, TT_MINUS

# read arguments
# program_path = sys.argv[1]

##########################
# CONSTANTS
##########################

DIGITS = '1234567890'


##########################
# ERRORS
##########################

class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'{self.error_name}: {self.details}'
        result += f'\nFile {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        return result

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end,"Illegal Character", details)


##########################
# POSITION
##########################

class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == "\n":
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

##########################
# TOKENS
##########################

TOKEN_INT          = 'TOKEN_INT'
TOKEN_FLOAT        = 'TOKEN_FLOAT'
TOKEN_BOOL         = 'TOKEN_BOOL'
TOKEN_STR          = 'TOKEN_STR'
TOKEN_LPAREN       = 'TOKEN_LPAREN'
TOKEN_RPAREN       = 'TOKEN_RPAREN'
TOKEN_LCURLBRACKET = 'TOKEN_LCURLBRACKET'
TOKEN_RCURLBRACKET = 'TOKEN_RCURLBRACKET'
TOKEN_LBRACKET     = 'TOKEN_LBRACKET'
TOKEN_RBRACKET     = 'TOKEN_RBRACKET'
TOKEN_COLON        = 'TOKEN_COLON'
TOKEN_EQU          = 'TOKEN_EQU'
TOKEN_PLUS         = 'TOKEN_PLUS'
TOKEN_MINUS        = 'TOKEN_MINUS'
TOKEN_MUL          = 'TOKEN_MUL'
TOKEN_DIV          = 'TOKEN_DIV'
TOKEN_EOF          = 'TOKEN_EOF'

class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

##########################
# Lexer
##########################

class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.idx] if self.pos.idx < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == "(":
                tokens.append(Token(TOKEN_LPAREN))
                self.advance()
            elif self.current_char == ")":
                tokens.append(Token(TOKEN_RPAREN))
                self.advance()
            elif self.current_char == "{":
                tokens.append(Token(TOKEN_LCURLBRACKET))
                self.advance()
            elif self.current_char == "}":
                tokens.append(Token(TOKEN_RCURLBRACKET))
                self.advance()
            elif self.current_char == "[":
                tokens.append(Token(TOKEN_LBRACKET))
                self.advance()
            elif self.current_char == "]":
                tokens.append(Token(TOKEN_RBRACKET))
                self.advance()
            elif self.current_char == ":":
                tokens.append(Token(TOKEN_COLON))
                self.advance()
            elif self.current_char == "=":
                tokens.append(Token(TOKEN_EQU))
                self.advance()
            elif self.current_char == "+":
                tokens.append(Token(TOKEN_PLUS))
                self.advance()
            elif self.current_char == "-":
                tokens.append(Token(TOKEN_MINUS))
                self.advance()
            elif self.current_char == "*":
                tokens.append(Token(TOKEN_MUL))
                self.advance()
            elif self.current_char == "/":
                tokens.append(Token(TOKEN_DIV))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, "'" + char + "'")

        return tokens, None


    def make_number(self):
        num_str = ''
        dot_count = 0

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()

        if dot_count == 0:
            return Token(TOKEN_INT, int(num_str))
        else:
            return Token(TOKEN_FLOAT, float(num_str))


##########################
# NODES
##########################

class NumberNode:
    def __init__(self, tok):
        self.tok = tok

    def __repr__(self):
        return f'{self.tok}'

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'



##########################
# PARSER
##########################

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_idx = -1
        self.advance()

    def advance(self):
        self.tok_idx += 1
        if self.tok_idx < len(self.tokens):
            self.current_tok = self.tokens[self.tok_idx]
        return self.current_tok

    def factor(self):
        tok = self.current_tok

        if tok.type in (TOKEN_INT, TOKEN_FLOAT):
            self.advance()
            return NumberNode(tok)

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def expr(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

    def bin_op(self, func, ops):
        left = self.factor()

        while self.current_tok in (TOKEN_DIV, TOKEN_MUL):
            op_tok = self.current_tok
            self.advance()
            right = self.factor()
            left = BinOpNode(left, op_tok, right)

        return left
    # todo: continue: https://youtu.be/RriZ4q4z9gU?list=PLZQftyCk7_SdoVexSmwy_tBgs7P0b97yD&t=450

##########################
# RUN
##########################

def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error
