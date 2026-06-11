#include "ast.h"
#include <stdlib.h>
#include <string.h>

ASTNode *ast_alloc(NodeType type) {
    ASTNode *node = calloc(1, sizeof(ASTNode));
    if (!node) return NULL;
    node->type = type;
    if (type == NODE_STMT_LIST) {
        node->data.stmt_list.capacity = 4;
        node->data.stmt_list.stmts = calloc(node->data.stmt_list.capacity, sizeof(ASTNode *));
        node->data.stmt_list.count = 0;
    }
    return node;
}

static void free_stmts(ASTNode *list) {
    if (!list || list->type != NODE_STMT_LIST) return;
    for (int i = 0; i < list->data.stmt_list.count; i++) {
        ast_free(list->data.stmt_list.stmts[i]);
    }
    free(list->data.stmt_list.stmts);
}

void ast_free(ASTNode *node) {
    if (!node) return;
    switch (node->type) {
        case NODE_PROGRAM:
            free(node->data.program.name);
            ast_free(node->data.program.body);
            break;
        case NODE_DECL:
            free(node->data.decl.name);
            free(node->data.decl.type_name);
            break;
        case NODE_ASSIGN:
            free(node->data.assign.name);
            ast_free(node->data.assign.expr);
            break;
        case NODE_READ:
            free(node->data.read.name);
            break;
        case NODE_WRITE_EXPR:
            ast_free(node->data.write_expr.expr);
            break;
        case NODE_WRITE_STR:
            free(node->data.write_str.value);
            break;
        case NODE_IF:
            ast_free(node->data.if_stmt.cond);
            ast_free(node->data.if_stmt.then_body);
            ast_free(node->data.if_stmt.else_body);
            break;
        case NODE_WHILE:
            ast_free(node->data.while_stmt.cond);
            ast_free(node->data.while_stmt.body);
            break;
        case NODE_FOR:
            free(node->data.for_stmt.var);
            ast_free(node->data.for_stmt.start);
            ast_free(node->data.for_stmt.end);
            ast_free(node->data.for_stmt.step);
            ast_free(node->data.for_stmt.body);
            break;
        case NODE_BINOP:
            ast_free(node->data.binop.left);
            ast_free(node->data.binop.right);
            break;
        case NODE_UNOP:
            ast_free(node->data.unop.operand);
            break;
        case NODE_IDENT:
            free(node->data.ident.name);
            break;
        case NODE_STRING:
            free(node->data.string.value);
            break;
        case NODE_STMT_LIST:
            free_stmts(node);
            break;
        default: break;
    }
    free(node);
}

void stmt_list_add(ASTNode *list, ASTNode *stmt) {
    if (!list || list->type != NODE_STMT_LIST) return;
    if (list->data.stmt_list.count >= list->data.stmt_list.capacity) {
        list->data.stmt_list.capacity *= 2;
        list->data.stmt_list.stmts = realloc(list->data.stmt_list.stmts,
            list->data.stmt_list.capacity * sizeof(ASTNode *));
    }
    list->data.stmt_list.stmts[list->data.stmt_list.count++] = stmt;
}
