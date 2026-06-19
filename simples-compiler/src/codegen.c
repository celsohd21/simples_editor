#include "codegen.h"
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

void codegen_init(Codegen *cg) {
    cg->vars = NULL;
    cg->names = NULL;
    cg->count = 0;
    cg->capacity = 0;
    cg->stack_offset = 0;
    cg->string_count = 0;
    cg->label_count = 0;
}

void codegen_free(Codegen *cg) {
    free(cg->vars);
    for (int i = 0; i < cg->count; i++) free(cg->names[i]);
    free(cg->names);
}

int codegen_error_count(Codegen *cg) {
    (void)cg;
    return 0;
}

static int find_var(Codegen *cg, const char *name) {
    for (int i = 0; i < cg->count; i++)
        if (strcmp(cg->names[i], name) == 0) return i;
    return -1;
}

static int add_var(Codegen *cg, const char *name) {
    int idx = find_var(cg, name);
    if (idx >= 0) return idx;
    if (cg->count >= cg->capacity) {
        cg->capacity = cg->capacity ? cg->capacity * 2 : 16;
        cg->vars = realloc(cg->vars, cg->capacity * sizeof(VarEntry));
        cg->names = realloc(cg->names, cg->capacity * sizeof(char *));
    }
    idx = cg->count++;
    cg->stack_offset -= 4;
    cg->vars[idx].offset = cg->stack_offset;
    cg->names[idx] = xstrdup(name);
    return idx;
}

static int next_label(Codegen *cg) {
    return cg->label_count++;
}

// ---- string collection pass ----
typedef struct {
    char *content;
    int len;
} StrEntry;

static StrEntry *strings = NULL;
static int str_count = 0;
static int str_cap = 0;

static void collect_strings_ast(ASTNode *node) {
    if (!node) return;
    switch (node->type) {
        case NODE_WRITE_STR: {
            char *p = node->data.write_str.value;
            int len = 0;
            for (char *s = p + 1; *s && *s != '"'; s++) len++;
            if (str_count >= str_cap) {
                str_cap = str_cap ? str_cap * 2 : 16;
                strings = realloc(strings, str_cap * sizeof(StrEntry));
            }
            char *buf = malloc(len + 1);
            strncpy(buf, p + 1, len);
            buf[len] = '\0';
            strings[str_count].content = buf;
            strings[str_count].len = len;
            str_count++;
            break;
        }
        case NODE_PROGRAM:
            collect_strings_ast(node->data.program.body);
            break;
        case NODE_IF:
            collect_strings_ast(node->data.if_stmt.then_body);
            collect_strings_ast(node->data.if_stmt.else_body);
            break;
        case NODE_WHILE:
            collect_strings_ast(node->data.while_stmt.body);
            break;
        case NODE_FOR:
            collect_strings_ast(node->data.for_stmt.body);
            break;
        case NODE_STMT_LIST:
            for (int i = 0; i < node->data.stmt_list.count; i++)
                collect_strings_ast(node->data.stmt_list.stmts[i]);
            break;
        default: break;
    }
}

// ---- forward decls for codegen pass ----
static void gen_stmt_list(Codegen *cg, ASTNode *list, FILE *out);
static void gen_expr(Codegen *cg, ASTNode *node, FILE *out);

static void emit_data_section(FILE *out) {
    fprintf(out, "section .data\n");
    fprintf(out, "    newline db 10\n");
    fprintf(out, "    minus_sign db '-', 0\n");
    for (int i = 0; i < str_count; i++) {
        fprintf(out, "    str%d db ", i);
        for (int j = 0; j < strings[i].len; j++) {
            char c = strings[i].content[j];
            if (c == '\n') fprintf(out, "10, ");
            else if (c == '\t') fprintf(out, "9, ");
            else fprintf(out, "%d, ", (unsigned char)c);
        }
        fprintf(out, "0\n");
    }
}

static void emit_bss_section(FILE *out) {
    fprintf(out, "section .bss\n");
    fprintf(out, "    buffer resb 16\n");
    fprintf(out, "    input_buffer resb 16\n\n");
}

// ---- code generation ----

static void gen_binop(Codegen *cg, ASTNode *node, FILE *out) {
    gen_expr(cg, node->data.binop.left, out);
    fprintf(out, "    push eax\n");
    gen_expr(cg, node->data.binop.right, out);
    fprintf(out, "    mov ebx, eax\n    pop eax\n");
    switch (node->data.binop.op) {
        case BINOP_ADD: fprintf(out, "    add eax, ebx\n"); break;
        case BINOP_SUB: fprintf(out, "    sub eax, ebx\n"); break;
        case BINOP_MUL: fprintf(out, "    imul eax, ebx\n"); break;
        case BINOP_DIV: fprintf(out, "    xor edx, edx\n    idiv ebx\n"); break;
        case BINOP_EQ:  fprintf(out, "    cmp eax, ebx\n    sete al\n    movzx eax, al\n"); break;
        case BINOP_NE:  fprintf(out, "    cmp eax, ebx\n    setne al\n    movzx eax, al\n"); break;
        case BINOP_LT:  fprintf(out, "    cmp eax, ebx\n    setl al\n    movzx eax, al\n"); break;
        case BINOP_GT:  fprintf(out, "    cmp eax, ebx\n    setg al\n    movzx eax, al\n"); break;
        case BINOP_LE:  fprintf(out, "    cmp eax, ebx\n    setle al\n    movzx eax, al\n"); break;
        case BINOP_GE:  fprintf(out, "    cmp eax, ebx\n    setge al\n    movzx eax, al\n"); break;
        case BINOP_AND: fprintf(out, "    and eax, ebx\n"); break;
        case BINOP_OR:  fprintf(out, "    or eax, ebx\n"); break;
    }
}

static void gen_unop(Codegen *cg, ASTNode *node, FILE *out) {
    gen_expr(cg, node->data.unop.operand, out);
    if (node->data.unop.op == UNOP_NOT)
        fprintf(out, "    test eax, eax\n    sete al\n    movzx eax, al\n");
    else if (node->data.unop.op == UNOP_MINUS)
        fprintf(out, "    neg eax\n");
}

static void gen_expr(Codegen *cg, ASTNode *node, FILE *out) {
    if (!node) return;
    switch (node->type) {
        case NODE_NUMBER:
            fprintf(out, "    mov eax, %d\n", node->data.number.value);
            break;
        case NODE_BOOL:
            fprintf(out, "    mov eax, %d\n", node->data.boolean.value);
            break;
        case NODE_IDENT: {
            int idx = find_var(cg, node->data.ident.name);
            if (idx < 0) {
                fprintf(stderr, "Erro: variavel '%s' nao declarada\n", node->data.ident.name);
                fprintf(out, "    xor eax, eax\n");
            } else {
                fprintf(out, "    mov eax, [ebp%+d]\n", cg->vars[idx].offset);
            }
            break;
        }
        case NODE_BINOP: gen_binop(cg, node, out); break;
        case NODE_UNOP:  gen_unop(cg, node, out); break;
        default: break;
    }
}

static void gen_read_int(Codegen *cg, FILE *out, int offset) {
    int lbl = next_label(cg);
    fprintf(out, "    mov eax, 3\n    mov ebx, 0\n    mov ecx, input_buffer\n");
    fprintf(out, "    mov edx, 16\n    int 0x80\n");
    fprintf(out, "    xor eax, eax\n    xor ebx, ebx\n    mov esi, input_buffer\n");
    fprintf(out, ".conv_%d:\n", lbl);
    fprintf(out, "    movzx ecx, byte [esi]\n");
    fprintf(out, "    cmp ecx, 10\n    je .done_%d\n", lbl);
    fprintf(out, "    cmp ecx, 0\n    je .done_%d\n", lbl);
    fprintf(out, "    sub ecx, '0'\n    imul eax, eax, 10\n    add eax, ecx\n");
    fprintf(out, "    inc esi\n    jmp .conv_%d\n", lbl);
    fprintf(out, ".done_%d:\n    mov [ebp%+d], eax\n", lbl, offset);
}

static void gen_write_int_expr(Codegen *cg, FILE *out) {
    int lbl = next_label(cg);
    fprintf(out, "    test eax, eax\n    jns .pos_%d\n", lbl);
    fprintf(out, "    push eax\n    mov eax, 4\n    mov ebx, 1\n");
    fprintf(out, "    mov ecx, minus_sign\n    mov edx, 1\n    int 0x80\n");
    fprintf(out, "    pop eax\n    neg eax\n");
    fprintf(out, ".pos_%d:\n    xor ecx, ecx\n    mov ebx, 10\n", lbl);
    fprintf(out, ".div_%d:\n    xor edx, edx\n    div ebx\n", lbl);
    fprintf(out, "    push edx\n    inc ecx\n    test eax, eax\n    jnz .div_%d\n", lbl);
    fprintf(out, ".wloop_%d:\n    pop eax\n    add eax, '0'\n    push ecx\n", lbl);
    fprintf(out, "    mov [buffer], eax\n    mov eax, 4\n    mov ebx, 1\n");
    fprintf(out, "    mov ecx, buffer\n    mov edx, 1\n    int 0x80\n");
    fprintf(out, "    pop ecx\n    dec ecx\n    test ecx, ecx\n    jnz .wloop_%d\n", lbl);
}

static void gen_stmt(Codegen *cg, ASTNode *stmt, FILE *out) {
    if (!stmt) return;

    switch (stmt->type) {
        case NODE_DECL:
            add_var(cg, stmt->data.decl.name);
            break;

        case NODE_ASSIGN: {
            int idx = add_var(cg, stmt->data.assign.name);
            gen_expr(cg, stmt->data.assign.expr, out);
            fprintf(out, "    mov [ebp%+d], eax\n", cg->vars[idx].offset);
            break;
        }

        case NODE_READ: {
            int idx = add_var(cg, stmt->data.read.name);
            gen_read_int(cg, out, cg->vars[idx].offset);
            break;
        }

        case NODE_WRITE_EXPR:
            gen_expr(cg, stmt->data.write_expr.expr, out);
            gen_write_int_expr(cg, out);
            break;

        case NODE_WRITE_STR: {
            int sid = 0;
            char *p = stmt->data.write_str.value;
            int plen = 0;
            for (char *s = p + 1; *s && *s != '"'; s++) plen++;
            for (int j = 0; j < str_count; j++) {
                if (plen == strings[j].len &&
                    strncmp(p + 1, strings[j].content, plen) == 0) {
                    sid = j;
                    break;
                }
            }
            fprintf(out, "    mov eax, 4\n    mov ebx, 1\n");
            fprintf(out, "    mov ecx, str%d\n    mov edx, %d\n    int 0x80\n",
                sid, strings[sid].len);
            break;
        }

        case NODE_IF: {
            int e = next_label(cg), d = next_label(cg);
            gen_expr(cg, stmt->data.if_stmt.cond, out);
            fprintf(out, "    test eax, eax\n    jz .else_%d\n", e);
            gen_stmt_list(cg, stmt->data.if_stmt.then_body, out);
            fprintf(out, "    jmp .end_%d\n", d);
            fprintf(out, ".else_%d:\n", e);
            gen_stmt_list(cg, stmt->data.if_stmt.else_body, out);
            fprintf(out, ".end_%d:\n", d);
            break;
        }

        case NODE_WHILE: {
            int s = next_label(cg), d = next_label(cg);
            fprintf(out, ".start_%d:\n", s);
            gen_expr(cg, stmt->data.while_stmt.cond, out);
            fprintf(out, "    test eax, eax\n    jz .end_%d\n", d);
            gen_stmt_list(cg, stmt->data.while_stmt.body, out);
            fprintf(out, "    jmp .start_%d\n", s);
            fprintf(out, ".end_%d:\n", d);
            break;
        }

        case NODE_FOR: {
            int idx = add_var(cg, stmt->data.for_stmt.var);
            int s = next_label(cg), d = next_label(cg);
            gen_expr(cg, stmt->data.for_stmt.start, out);
            fprintf(out, "    mov [ebp%+d], eax\n", cg->vars[idx].offset);
            fprintf(out, ".start_%d:\n", s);
            fprintf(out, "    mov eax, [ebp%+d]\n", cg->vars[idx].offset);
            gen_expr(cg, stmt->data.for_stmt.end, out);
            fprintf(out, "    cmp [ebp%+d], eax\n", cg->vars[idx].offset);
            fprintf(out, "    jg .end_%d\n", d);
            gen_stmt_list(cg, stmt->data.for_stmt.body, out);
            fprintf(out, "    add dword [ebp%+d], 1\n", cg->vars[idx].offset);
            fprintf(out, "    jmp .start_%d\n", s);
            fprintf(out, ".end_%d:\n", d);
            break;
        }

        default: break;
    }
}

static void gen_stmt_list(Codegen *cg, ASTNode *list, FILE *out) {
    if (!list || list->type != NODE_STMT_LIST) return;
    for (int i = 0; i < list->data.stmt_list.count; i++)
        gen_stmt(cg, list->data.stmt_list.stmts[i], out);
}

static void compute_stack_size(Codegen *cg, ASTNode *node) {
    if (!node) return;
    if (node->type == NODE_DECL) {
        add_var(cg, node->data.decl.name);
    } else if (node->type == NODE_STMT_LIST) {
        for (int i = 0; i < node->data.stmt_list.count; i++)
            compute_stack_size(cg, node->data.stmt_list.stmts[i]);
    }
}

void codegen_generate(Codegen *cg, ASTNode *node, FILE *out) {
    if (!node || node->type != NODE_PROGRAM) return;

    collect_strings_ast(node);

    compute_stack_size(cg, node->data.program.body);

    fprintf(out, "; Generated by simplesc - SIMPLES to NASM compiler\n");
    fprintf(out, "; Program: %s\n\n", node->data.program.name);

    emit_data_section(out);
    fprintf(out, "\n");
    emit_bss_section(out);
    fprintf(out, "\n");

    int stack_size = -cg->stack_offset;
    if (stack_size < 0) stack_size = 0;

    fprintf(out, "section .text\n");
    fprintf(out, "    global _start\n\n");
    fprintf(out, "_start:\n");
    fprintf(out, "    mov ebp, esp\n");
    fprintf(out, "    sub esp, %d\n", stack_size);
    fprintf(out, "    and esp, -16\n");

    gen_stmt_list(cg, node->data.program.body, out);

    fprintf(out, "    mov eax, 1\n    xor ebx, ebx\n    int 0x80\n");
}
