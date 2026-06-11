#ifndef AST_H
#define AST_H

typedef enum {
    NODE_PROGRAM,
    NODE_DECL,
    NODE_ASSIGN,
    NODE_READ,
    NODE_WRITE_EXPR,
    NODE_WRITE_STR,
    NODE_IF,
    NODE_WHILE,
    NODE_FOR,
    NODE_BINOP,
    NODE_UNOP,
    NODE_NUMBER,
    NODE_IDENT,
    NODE_STRING,
    NODE_BOOL,
    NODE_STMT_LIST,
} NodeType;

typedef enum {
    BINOP_ADD, BINOP_SUB, BINOP_MUL, BINOP_DIV,
    BINOP_EQ, BINOP_NE, BINOP_LT, BINOP_GT, BINOP_LE, BINOP_GE,
    BINOP_AND, BINOP_OR,
} BinOpType;

typedef enum {
    UNOP_NOT, UNOP_MINUS,
} UnOpType;

typedef struct ASTNode {
    NodeType type;
    union {
        struct { char *name; struct ASTNode *body; } program;
        struct { char *name; char *type_name; } decl;
        struct { char *name; struct ASTNode *expr; } assign;
        struct { char *name; } read;
        struct { struct ASTNode *expr; } write_expr;
        struct { char *value; } write_str;
        struct { struct ASTNode *cond; struct ASTNode *then_body; struct ASTNode *else_body; } if_stmt;
        struct { struct ASTNode *cond; struct ASTNode *body; } while_stmt;
        struct { char *var; struct ASTNode *start; struct ASTNode *end; struct ASTNode *step; struct ASTNode *body; } for_stmt;
        struct { BinOpType op; struct ASTNode *left; struct ASTNode *right; } binop;
        struct { UnOpType op; struct ASTNode *operand; } unop;
        struct { int value; } number;
        struct { char *name; } ident;
        struct { char *value; } string;
        struct { int value; } boolean;
        struct { struct ASTNode **stmts; int count; int capacity; } stmt_list;
    } data;
} ASTNode;

ASTNode *ast_alloc(NodeType type);
void ast_free(ASTNode *node);
void stmt_list_add(ASTNode *list, ASTNode *stmt);

#endif
