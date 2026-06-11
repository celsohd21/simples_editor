#include "parser.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static char *xstrdup(const char *s) {
    if (!s) return NULL;
    size_t len = strlen(s);
    char *d = malloc(len + 1);
    if (d) { memcpy(d, s, len); d[len] = '\0'; }
    return d;
}

static ASTNode *parse_stmt_list(Parser *p);
static ASTNode *parse_expr(Parser *p);
static ASTNode *parse_rel_expr(Parser *p);
static ASTNode *parse_add_expr(Parser *p);
static ASTNode *parse_term(Parser *p);
static ASTNode *parse_factor(Parser *p);

void parser_init(Parser *p, Lexer *lex) {
    p->lex = lex;
    p->error_count = 0;
}

void parser_error(Parser *p, const char *msg) {
    fprintf(stderr, "Erro sintatico (linha %d): %s (encontrado '%s')\n",
        p->lex->current.line, msg, p->lex->current.lexeme);
    p->error_count++;
}

static int consume(Parser *p, TokenType type, const char *msg) {
    if (p->lex->current.type == type) {
        lexer_advance(p->lex);
        return 1;
    }
    parser_error(p, msg);
    return 0;
}

static ASTNode *parse_program(Parser *p) {
    consume(p, TOK_PROGRAMA, "Esperado 'programa'");
    if (p->lex->current.type != TOK_IDENT) {
        parser_error(p, "Esperado nome do programa");
        return NULL;
    }
    ASTNode *prog = ast_alloc(NODE_PROGRAM);
    prog->data.program.name = xstrdup(p->lex->current.lexeme);
    lexer_advance(p->lex);

    consume(p, TOK_INICIO, "Esperado 'inicio'");
    ASTNode *body = parse_stmt_list(p);
    consume(p, TOK_FIM, "Esperado 'fim'");

    prog->data.program.body = body;
    return prog;
}

static ASTNode *parse_decl(Parser *p) {
    ASTNode *node = ast_alloc(NODE_DECL);
    const char *type_names[] = {"inteiro", "real", "caractere", "booleano"};
    TokenType types[] = {TOK_INTEIRO, TOK_REAL, TOK_CARACTERE, TOK_BOOLEANO};
    node->data.decl.type_name = NULL;
    for (int i = 0; i < 4; i++) {
        if (p->lex->current.type == types[i]) {
            node->data.decl.type_name = xstrdup(type_names[i]);
            lexer_advance(p->lex);
            break;
        }
    }
    if (!node->data.decl.type_name) {
        parser_error(p, "Esperado tipo (inteiro/real/caractere/booleano)");
        ast_free(node);
        return NULL;
    }
    if (p->lex->current.type != TOK_IDENT) {
        parser_error(p, "Esperado nome de variavel");
        ast_free(node);
        return NULL;
    }
    node->data.decl.name = xstrdup(p->lex->current.lexeme);
    lexer_advance(p->lex);
    return node;
}

static ASTNode *parse_stmt(Parser *p) {
    switch (p->lex->current.type) {
        case TOK_INTEIRO:
        case TOK_REAL:
        case TOK_CARACTERE:
        case TOK_BOOLEANO:
            return parse_decl(p);

        case TOK_LEIA: {
            lexer_advance(p->lex);
            if (p->lex->current.type != TOK_IDENT) {
                parser_error(p, "Esperado nome de variavel apos 'leia'");
                return NULL;
            }
            ASTNode *node = ast_alloc(NODE_READ);
            node->data.read.name = xstrdup(p->lex->current.lexeme);
            lexer_advance(p->lex);
            return node;
        }

        case TOK_ESCREVA: {
            lexer_advance(p->lex);
            if (p->lex->current.type == TOK_STRING) {
                ASTNode *node = ast_alloc(NODE_WRITE_STR);
                node->data.write_str.value = xstrdup(p->lex->current.lexeme);
                lexer_advance(p->lex);
                return node;
            }
            ASTNode *node = ast_alloc(NODE_WRITE_EXPR);
            node->data.write_expr.expr = parse_expr(p);
            return node;
        }

        case TOK_SE: {
            lexer_advance(p->lex);
            ASTNode *node = ast_alloc(NODE_IF);
            node->data.if_stmt.cond = parse_expr(p);
            consume(p, TOK_ENTAO, "Esperado 'entao' apos condicao");
            node->data.if_stmt.then_body = parse_stmt_list(p);
            if (p->lex->current.type == TOK_SENAO) {
                lexer_advance(p->lex);
                node->data.if_stmt.else_body = parse_stmt_list(p);
            } else {
                node->data.if_stmt.else_body = NULL;
            }
            consume(p, TOK_FIMSE, "Esperado 'fimse'");
            return node;
        }

        case TOK_ENQUANTO: {
            lexer_advance(p->lex);
            ASTNode *node = ast_alloc(NODE_WHILE);
            node->data.while_stmt.cond = parse_expr(p);
            consume(p, TOK_FACA, "Esperado 'faca' apos condicao");
            node->data.while_stmt.body = parse_stmt_list(p);
            consume(p, TOK_FIMENQUANTO, "Esperado 'fimenquanto'");
            return node;
        }

        case TOK_PARA: {
            lexer_advance(p->lex);
            ASTNode *node = ast_alloc(NODE_FOR);
            if (p->lex->current.type != TOK_IDENT) {
                parser_error(p, "Esperado nome de variavel apos 'para'");
                ast_free(node);
                return NULL;
            }
            node->data.for_stmt.var = xstrdup(p->lex->current.lexeme);
            lexer_advance(p->lex);
            consume(p, TOK_DE, "Esperado 'de' apos variavel");
            node->data.for_stmt.start = parse_expr(p);
            consume(p, TOK_ATE, "Esperado 'ate'");
            node->data.for_stmt.end = parse_expr(p);
            if (p->lex->current.type == TOK_PASSO) {
                lexer_advance(p->lex);
                node->data.for_stmt.step = parse_expr(p);
            } else {
                node->data.for_stmt.step = NULL;
            }
            consume(p, TOK_FACA, "Esperado 'faca'");
            node->data.for_stmt.body = parse_stmt_list(p);
            consume(p, TOK_FIMPARA, "Esperado 'fimpara'");
            return node;
        }

        default: {
            if (p->lex->current.type == TOK_IDENT) {
                char *name = xstrdup(p->lex->current.lexeme);
                lexer_advance(p->lex);
                if (p->lex->current.type == TOK_ATRIB) {
                    lexer_advance(p->lex);
                    ASTNode *node = ast_alloc(NODE_ASSIGN);
                    node->data.assign.name = name;
                    node->data.assign.expr = parse_expr(p);
                    return node;
                }
                parser_error(p, "Esperado ':=' apos identificador");
                free(name);
                return NULL;
            }
            parser_error(p, "Esperado inicio de instrucao");
            return NULL;
        }
    }
}

static ASTNode *parse_stmt_list(Parser *p) {
    ASTNode *list = ast_alloc(NODE_STMT_LIST);
    while (p->lex->current.type != TOK_FIM &&
           p->lex->current.type != TOK_SENAO &&
           p->lex->current.type != TOK_FIMSE &&
           p->lex->current.type != TOK_FIMENQUANTO &&
           p->lex->current.type != TOK_FIMPARA &&
           p->lex->current.type != TOK_EOF) {
        ASTNode *stmt = parse_stmt(p);
        if (stmt) stmt_list_add(list, stmt);
        else {
            lexer_advance(p->lex);
        }
    }
    return list;
}

ASTNode *parser_parse(Parser *p) {
    if (p->lex->current.type == TOK_EOF) {
        fprintf(stderr, "Erro: codigo fonte vazio\n");
        return NULL;
    }
    return parse_program(p);
}

static ASTNode *parse_expr(Parser *p) {
    ASTNode *left = parse_rel_expr(p);
    while (p->lex->current.type == TOK_E || p->lex->current.type == TOK_OU) {
        BinOpType op = (p->lex->current.type == TOK_E) ? BINOP_AND : BINOP_OR;
        lexer_advance(p->lex);
        ASTNode *right = parse_rel_expr(p);
        ASTNode *node = ast_alloc(NODE_BINOP);
        node->data.binop.op = op;
        node->data.binop.left = left;
        node->data.binop.right = right;
        left = node;
    }
    return left;
}

static ASTNode *parse_rel_expr(Parser *p) {
    ASTNode *left = parse_add_expr(p);
    TokenType t = p->lex->current.type;
    if (t == TOK_IGUAL || t == TOK_DIF || t == TOK_MENOR ||
        t == TOK_MAIOR || t == TOK_MENORIG || t == TOK_MAIORIG) {
        lexer_advance(p->lex);
        BinOpType op;
        if (t == TOK_IGUAL) op = BINOP_EQ;
        else if (t == TOK_DIF) op = BINOP_NE;
        else if (t == TOK_MENOR) op = BINOP_LT;
        else if (t == TOK_MAIOR) op = BINOP_GT;
        else if (t == TOK_MENORIG) op = BINOP_LE;
        else op = BINOP_GE;
        ASTNode *right = parse_add_expr(p);
        ASTNode *node = ast_alloc(NODE_BINOP);
        node->data.binop.op = op;
        node->data.binop.left = left;
        node->data.binop.right = right;
        return node;
    }
    return left;
}

static ASTNode *parse_add_expr(Parser *p) {
    ASTNode *left = parse_term(p);
    while (p->lex->current.type == TOK_MAIS || p->lex->current.type == TOK_MENOS) {
        BinOpType op = (p->lex->current.type == TOK_MAIS) ? BINOP_ADD : BINOP_SUB;
        lexer_advance(p->lex);
        ASTNode *right = parse_term(p);
        ASTNode *node = ast_alloc(NODE_BINOP);
        node->data.binop.op = op;
        node->data.binop.left = left;
        node->data.binop.right = right;
        left = node;
    }
    return left;
}

static ASTNode *parse_term(Parser *p) {
    ASTNode *left = parse_factor(p);
    while (p->lex->current.type == TOK_MULT || p->lex->current.type == TOK_DIV) {
        BinOpType op = (p->lex->current.type == TOK_MULT) ? BINOP_MUL : BINOP_DIV;
        lexer_advance(p->lex);
        ASTNode *right = parse_factor(p);
        ASTNode *node = ast_alloc(NODE_BINOP);
        node->data.binop.op = op;
        node->data.binop.left = left;
        node->data.binop.right = right;
        left = node;
    }
    return left;
}

static Token copy_token(Token *src) {
    Token t = *src;
    t.lexeme = xstrdup(src->lexeme);
    return t;
}

static ASTNode *parse_factor(Parser *p) {
    Token t = copy_token(&p->lex->current);
    lexer_advance(p->lex);

    switch (t.type) {
        case TOK_NUMBER: {
            ASTNode *node = ast_alloc(NODE_NUMBER);
            node->data.number.value = atoi(t.lexeme);
            free(t.lexeme);
            return node;
        }
        case TOK_IDENT: {
            ASTNode *node = ast_alloc(NODE_IDENT);
            node->data.ident.name = t.lexeme;
            return node;
        }
        case TOK_STRING: {
            ASTNode *node = ast_alloc(NODE_STRING);
            node->data.string.value = t.lexeme;
            return node;
        }
        case TOK_VERDADEIRO: {
            ASTNode *node = ast_alloc(NODE_BOOL);
            node->data.boolean.value = 1;
            free(t.lexeme);
            return node;
        }
        case TOK_FALSO: {
            ASTNode *node = ast_alloc(NODE_BOOL);
            node->data.boolean.value = 0;
            free(t.lexeme);
            return node;
        }
        case TOK_NAO: {
            ASTNode *node = ast_alloc(NODE_UNOP);
            node->data.unop.op = UNOP_NOT;
            free(t.lexeme);
            node->data.unop.operand = parse_factor(p);
            return node;
        }
        case TOK_MENOS: {
            ASTNode *node = ast_alloc(NODE_UNOP);
            node->data.unop.op = UNOP_MINUS;
            free(t.lexeme);
            node->data.unop.operand = parse_factor(p);
            return node;
        }
        case TOK_ABREPAR: {
            ASTNode *node = parse_expr(p);
            if (p->lex->current.type != TOK_FECHAPAR) {
                parser_error(p, "Esperado ')'");
            } else {
                lexer_advance(p->lex);
            }
            free(t.lexeme);
            return node;
        }
        default:
            parser_error(p, "Expressao invalida");
            free(t.lexeme);
            return NULL;
    }
}
