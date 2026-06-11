import * as monaco from 'monaco-editor'

const nasmKeywords = [
  'db', 'dw', 'dd', 'dq', 'dt', 'resb', 'resw', 'resd', 'resq',
  'global', 'extern', 'section', 'segment', 'absolute', 'align',
  'bits', 'use16', 'use32', 'use64', 'default', 'cpu',
  'org', 'end', 'equ', 'times', 'dup', 'struc', 'endstruc',
  'macro', 'endmacro', 'imacro', 'endimacro',
  'if', 'elif', 'else', 'endif', 'ifdef', 'ifndef',
  'define', 'undef', 'defstr', 'deftok', 'strlen',
  '%assign', '%define', '%undef', '%defstr', '%deftok', '%strlen',
  '%if', '%elif', '%else', '%endif', '%ifdef', '%ifndef', '%ifctx', '%ifidn', '%ifidni',
  '%macro', '%endmacro', '%imacro', '%rep', '%endrep', '%exitrep',
  '%include', '%push', '%pop', '%repl', '%rotate',
  '%pathsearch', '%substr', '%xdefine',
]

const nasmRegisters = [
  'al', 'ah', 'ax', 'eax', 'rax',
  'bl', 'bh', 'bx', 'ebx', 'rbx',
  'cl', 'ch', 'cx', 'ecx', 'rcx',
  'dl', 'dh', 'dx', 'edx', 'rdx',
  'sil', 'spl', 'bpl', 'dil',
  'si', 'di', 'bp', 'sp',
  'esi', 'edi', 'ebp', 'esp',
  'rsi', 'rdi', 'rbp', 'rsp',
  'r8', 'r9', 'r10', 'r11', 'r12', 'r13', 'r14', 'r15',
  'r8b', 'r9b', 'r10b', 'r11b', 'r12b', 'r13b', 'r14b', 'r15b',
  'r8w', 'r9w', 'r10w', 'r11w', 'r12w', 'r13w', 'r14w', 'r15w',
  'r8d', 'r9d', 'r10d', 'r11d', 'r12d', 'r13d', 'r14d', 'r15d',
  'cs', 'ds', 'es', 'fs', 'gs', 'ss',
  'cr0', 'cr1', 'cr2', 'cr3', 'cr4',
  'dr0', 'dr1', 'dr2', 'dr3', 'dr6', 'dr7',
  'st0', 'st1', 'st2', 'st3', 'st4', 'st5', 'st6', 'st7',
  'mm0', 'mm1', 'mm2', 'mm3', 'mm4', 'mm5', 'mm6', 'mm7',
  'xmm0', 'xmm1', 'xmm2', 'xmm3', 'xmm4', 'xmm5', 'xmm6', 'xmm7',
]

const nasmInstructions = [
  'aaa', 'aad', 'aam', 'aas', 'adc', 'add', 'and', 'arpl',
  'bound', 'bsf', 'bsr', 'bswap', 'bt', 'btc', 'btr', 'bts',
  'call', 'cbw', 'cdq', 'cdqe', 'clc', 'cld', 'cli', 'clts',
  'cmc', 'cmp', 'cmpsb', 'cmpsd', 'cmpsq', 'cmpsw', 'cmpxchg',
  'cmpxchg8b', 'cpuid', 'cqo', 'cwd', 'cwde', 'daa', 'das',
  'dec', 'div', 'enter', 'hlt', 'idiv', 'imul', 'in', 'inc',
  'insb', 'insd', 'insw', 'int', 'into', 'invd', 'invlpg', 'iret',
  'iretd', 'ja', 'jae', 'jb', 'jbe', 'jc', 'jcxz', 'je',
  'jecxz', 'jg', 'jge', 'jl', 'jle', 'jmp', 'jna', 'jnae',
  'jnb', 'jnbe', 'jnc', 'jne', 'jng', 'jnge', 'jnl', 'jnle',
  'jno', 'jnp', 'jns', 'jnz', 'jo', 'jp', 'jpe', 'jpo',
  'js', 'jz', 'lahf', 'lar', 'lds', 'lea', 'leave', 'les',
  'lfs', 'lgdt', 'lgs', 'lidt', 'lldt', 'lmsw', 'lock', 'lodsb',
  'lodsd', 'lodsq', 'lodsw', 'loop', 'loope', 'loopne', 'loopnz',
  'loopz', 'lsl', 'lss', 'ltr', 'mov', 'movsb', 'movsd', 'movsq',
  'movsw', 'movsx', 'movzx', 'mul', 'neg', 'nop', 'not', 'or',
  'out', 'outsb', 'outsd', 'outsw', 'pop', 'popa', 'popad',
  'popf', 'popfd', 'push', 'pusha', 'pushad', 'pushf', 'pushfd',
  'rcl', 'rcr', 'rdmsr', 'rdpmc', 'rdtsc', 'rep', 'repe',
  'repne', 'repnz', 'repz', 'ret', 'retf', 'retn', 'rol', 'ror',
  'rsm', 'sahf', 'sal', 'sar', 'sbb', 'scasb', 'scasd', 'scasq',
  'scasw', 'seta', 'setae', 'setb', 'setbe', 'setc', 'sete',
  'setg', 'setge', 'setl', 'setle', 'setna', 'setnae', 'setnb',
  'setnbe', 'setnc', 'setne', 'setng', 'setnge', 'setnl', 'setnle',
  'setno', 'setnp', 'setns', 'setnz', 'seto', 'setp', 'setpe',
  'setpo', 'sets', 'setz', 'sgdt', 'shl', 'shld', 'shr', 'shrd',
  'sidt', 'sldt', 'smsw', 'stc', 'std', 'sti', 'stosb', 'stosd',
  'stosq', 'stosw', 'str', 'sub', 'syscall', 'sysenter',
  'sysexit', 'sysret', 'test', 'ud2', 'verr', 'verw',
  'wait', 'wbinvd', 'wrmsr', 'xadd', 'xchg', 'xlat', 'xlatb',
  'xor',
  'fabs', 'fadd', 'faddp', 'fbld', 'fbstp', 'fchs', 'fclex',
  'fcmovb', 'fcmovbe', 'fcmove', 'fcmovnb', 'fcmovnbe',
  'fcmovne', 'fcmovnu', 'fcmovu', 'fcom', 'fcomp', 'fcompp',
  'fcos', 'fdiv', 'fdivp', 'fdivr', 'fdivrp', 'ffree', 'fiadd',
  'ficom', 'ficomp', 'fidiv', 'fidivr', 'fild', 'fimul',
  'fincstp', 'finit', 'fist', 'fistp', 'fisub', 'fisubr',
  'fld', 'fld1', 'fldcw', 'fldenv', 'fldl2e', 'fldl2t',
  'fldlg2', 'fldln2', 'fldpi', 'fldz', 'fmul', 'fmulp', 'fnclex',
  'fninit', 'fnop', 'fnsave', 'fnstcw', 'fnstenv', 'fnstsw',
  'fpatan', 'fprem', 'fprem1', 'fptan', 'frndint', 'frstor',
  'fsave', 'fscale', 'fsin', 'fsincos', 'fsqrt', 'fst', 'fstp',
  'fstcw', 'fstenv', 'fstsw', 'fsub', 'fsubp', 'fsubr', 'fsubrp',
  'ftst', 'fucom', 'fucomp', 'fucompp', 'fwait', 'fxam', 'fxch',
  'fxrstor', 'fxsave', 'fxtract', 'fyl2x', 'fyl2xp1',
]

export function registerNasmLanguage() {
  monaco.languages.register({ id: 'nasm' })

  monaco.languages.setMonarchTokensProvider('nasm', {
    defaultToken: 'text',
    tokenizer: {
      root: [
        [/;\s*#region\b/, 'comment', 'region'],
        [/;\s*#endregion\b/, 'comment'],

        [/;.*$/, 'comment'],

        [/@?[a-zA-Z_$][\w$.]*:/, 'tag'],

        [/^\s*[a-zA-Z_.][\w$.]*:/, 'tag'],

        [/^\s*\[section\s/, 'key', 'section'],
        [/section\s/, 'key', 'section'],

        [/[a-zA-Z_$][\w$.]*(?=\s+equ\s)/, 'identifier'],

        [/0[xX][0-9a-fA-F]+/, 'number.hex'],
        [/0[bB][01]+/, 'number.bin'],
        [/0[oO][0-7]+/, 'number.octal'],
        [/[0-9]+\.[0-9]*([eE][+-]?[0-9]+)?/, 'number.float'],
        [/[0-9]+/, 'number'],

        [/\$[0-9a-fA-F]+/, 'number.hex'],
        [/[$$][0-9]+/, 'number'],

        [/`[^`]*`/, 'string'],
        [/"[^"]*"/, 'string'],
        [/'.*?'/, 'string'],

        [
          /[a-zA-Z_$][\w$.]*/,
          {
            cases: {
              '@nasmKeywords': 'keyword',
              '@nasmInstructions': 'keyword.instruction',
              '@nasmRegisters': 'register',
              '@default': 'identifier',
            },
          },
        ],

        [/[()\[\]]/, '@brackets'],
        [/[.,:],/, 'delimiter'],
        [/[+\-*/%&|^~!<>]=?/, 'operator'],

        [/[ \t\r\n]+/, 'white'],
      ],

      section: [
        [/\.\w+/, 'constant'],
        [/\s+/, 'white'],
        [/[,\]\[#]/, 'delimiter'],
        [/$/, 'white', '@pop'],
      ],

      region: [
        [/;/, 'comment', '@pop'],
        [/[^;]+/, 'comment'],
      ],
    },
    nasmKeywords,
    nasmInstructions,
    nasmRegisters,
  })

  monaco.editor.defineTheme('nasm-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },
      { token: 'keyword', foreground: '569CD6' },
      { token: 'keyword.instruction', foreground: 'DCDCAA' },
      { token: 'register', foreground: '4FC1FF' },
      { token: 'number', foreground: 'B5CEA8' },
      { token: 'number.hex', foreground: 'B5CEA8' },
      { token: 'number.bin', foreground: 'B5CEA8' },
      { token: 'number.octal', foreground: 'B5CEA8' },
      { token: 'number.float', foreground: 'B5CEA8' },
      { token: 'string', foreground: 'CE9178' },
      { token: 'tag', foreground: 'D7BA7D' },
      { token: 'constant', foreground: '4EC9B0' },
      { token: 'identifier', foreground: '9CDCFE' },
      { token: 'delimiter', foreground: 'D4D4D4' },
      { token: 'operator', foreground: 'D4D4D4' },
    ],
    colors: {
      'editor.background': '#1E1E1E',
      'editor.foreground': '#D4D4D4',
      'editor.lineHighlightBackground': '#2A2D2E',
      'editor.selectionBackground': '#264F78',
    },
  })
}

export function registerNasmAutocomplete() {
  monaco.languages.registerCompletionItemProvider('nasm', {
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      }

      const directives = [
        { label: 'section', detail: 'Define a section (.data, .text, .bss)', insertText: 'section .' },
        { label: 'global', detail: 'Export a symbol', insertText: 'global ' },
        { label: 'extern', detail: 'Import an external symbol', insertText: 'extern ' },
        { label: 'db', detail: 'Define byte(s)', insertText: 'db ' },
        { label: 'dw', detail: 'Define word(s)', insertText: 'dw ' },
        { label: 'dd', detail: 'Define double word(s)', insertText: 'dd ' },
        { label: 'dq', detail: 'Define quad word(s)', insertText: 'dq ' },
        { label: 'resb', detail: 'Reserve byte(s)', insertText: 'resb ' },
        { label: 'resw', detail: 'Reserve word(s)', insertText: 'resw ' },
        { label: 'resd', detail: 'Reserve double word(s)', insertText: 'resd ' },
        { label: 'equ', detail: 'Define constant', insertText: ' equ ' },
        { label: 'times', detail: 'Repeat instruction/data', insertText: 'times ' },
        { label: 'align', detail: 'Align to boundary', insertText: 'align ' },
        { label: 'bits', detail: 'Set BITS mode', insertText: 'bits ' },
        { label: 'segment', detail: 'Synonym for section', insertText: 'segment .' },
        { label: 'macro', detail: 'Start a macro definition', insertText: '%macro ' },
        { label: 'endmacro', detail: 'End a macro definition', insertText: '%endmacro' },
      ]

      const snippets = [
        {
          label: 'section .data',
          detail: 'Data section template',
          insertText: 'section .data\n    ${1:msg} db "${2:Hello, World!}", 0\n    ${3:len} equ $ - ${1:msg}\n',
        },
        {
          label: 'section .text',
          detail: 'Text section with _start',
          insertText: 'section .text\n    global _start\n_start:\n    ${1:mov rax, 60}\n    ${2:xor rdi, rdi}\n    ${3:syscall}\n',
        },
        {
          label: 'syscall write',
          detail: 'Linux syscall write(1, msg, len)',
          insertText: '    mov rax, 1         ; syscall: write\n    mov rdi, 1         ; fd: stdout\n    mov rsi, ${1:msg}   ; buffer\n    mov rdx, ${2:len}   ; length\n    syscall\n',
        },
        {
          label: 'syscall exit',
          detail: 'Linux syscall exit(0)',
          insertText: '    mov rax, 60        ; syscall: exit\n    xor rdi, rdi       ; status: 0\n    syscall\n',
        },
      ]

      return {
        suggestions: [
          ...directives.map((d) => ({
            ...d,
            kind: monaco.languages.CompletionItemKind.Keyword,
            range,
          })),
          ...snippets.map((s) => ({
            ...s,
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range,
          })),
        ],
      }
    },
  })
}
