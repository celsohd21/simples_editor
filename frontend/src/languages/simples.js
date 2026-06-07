import * as monaco from 'monaco-editor'

/**
 * Registra a linguagem SIMPLES no Monaco Editor com Monarch tokenizer.
 * 
 * Palavras-chave: programa, inicio, fim, leia, escreva, enquanto, para, se, 
 * entao, senao, inteiro, real, caractere, booleano, e, ou, nao, verdadeiro, 
 * falso, div, mod, etc.
 */
export function registerSimplesLanguage() {
  // Registra a linguagem SIMPLES
  monaco.languages.register({ id: 'simples' })

  // Define o tokenizer com Monarch
  monaco.languages.setMonarchTokensProvider('simples', {
    // Palavras-chave da linguagem SIMPLES (27 keywords)
    keywords: [
      'programa',
      'inicio',
      'fim',
      'leia',
      'escreva',
      'enquanto',
      'para',
      'se',
      'entao',
      'senao',
      'inteiro',
      'real',
      'caractere',
      'booleano',
      'e',
      'ou',
      'nao',
      'verdadeiro',
      'falso',
      'div',
      'mod',
      'funcao',
      'retorna',
      'de',
      'ate',
      'passo',
      'faca',
    ],

    // Operadores
    operators: ['+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=', ':='],

    // Símbolos (pontuação)
    symbols: /[=><!~?:&|+\-*\/^%]+/,

    // Tokenizer rules
    tokenizer: {
      root: [
        // Comentários
        [/\{[^}]*\}/, 'comment'],

        // Strings (entre aspas simples ou duplas)
        [/"([^"\\]|\\.)*"/, 'string'],
        [/'([^'\\]|\\.)*'/, 'string'],

        // Números (inteiros e reais)
        [/\b\d+(\.\d+)?\b/, 'number'],

        // Identificadores e palavras-chave
        [
          /[a-zA-Z_]\w*/,
          {
            cases: {
              '@keywords': 'keyword',
              '@default': 'identifier',
            },
          },
        ],

        // Espaço em branco
        [/\s+/, 'white'],

        // Símbolos e operadores
        [/@symbols/, 'operator'],

        // Pontuação
        [/[();,\[\]{}]/, 'delimiter'],
      ],
    },
  })

  // Define o tema com cores para dark theme (compatível com VS Code)
  monaco.editor.defineTheme('simples-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      // Palavras-chave em azul claro
      { token: 'keyword', foreground: '569CD6', fontStyle: 'bold' },

      // Strings em vermelho
      { token: 'string', foreground: 'CE9178' },

      // Números em amarelo/verde
      { token: 'number', foreground: 'B5CEA8' },

      // Identificadores em branco
      { token: 'identifier', foreground: 'D4D4D4' },

      // Operadores em branco
      { token: 'operator', foreground: 'D4D4D4' },

      // Comentários em verde
      { token: 'comment', foreground: '6A9955', fontStyle: 'italic' },

      // Delimitadores em branco
      { token: 'delimiter', foreground: 'D4D4D4' },
    ],
    colors: {
      'editor.foreground': '#D4D4D4',
      'editor.background': '#1E1E1E',
      'editor.selectionBackground': '#264F78',
      'editor.lineNumbersColor': '#858585',
    },
  })
}

/**
 * Registra autocompletar para a linguagem SIMPLES.
 */
export function registerSimplesAutocomplete() {
  monaco.languages.registerCompletionItemProvider('simples', {
    provideCompletionItems: (model, position) => {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      }

      const suggestions = [
        // Estrutura de programa
        {
          label: 'programa',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'programa ${1:nome}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Declara o início de um programa',
          range: range,
        },
        {
          label: 'inicio',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'inicio',
          documentation: 'Marca o início das instruções',
          range: range,
        },
        {
          label: 'fim',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'fim',
          documentation: 'Marca o fim do programa',
          range: range,
        },

        // I/O
        {
          label: 'leia',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'leia ${1:variavel}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Lê um valor da entrada',
          range: range,
        },
        {
          label: 'escreva',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'escreva ${1:expressao}',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Escreve um valor na saída',
          range: range,
        },

        // Controle de fluxo
        {
          label: 'se',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'se ${1:condicao} entao\n\t${2:instrucoes}\nsenao\n\t${3:instrucoes}\nfim se',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Estrutura de decisão',
          range: range,
        },
        {
          label: 'enquanto',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'enquanto ${1:condicao} faca\n\t${2:instrucoes}\nfim enquanto',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Loop enquanto condição é verdadeira',
          range: range,
        },
        {
          label: 'para',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'para ${1:variavel} de ${2:inicio} ate ${3:fim} faca\n\t${4:instrucoes}\nfim para',
          insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
          documentation: 'Loop for com variável de controle',
          range: range,
        },

        // Tipos de dados
        {
          label: 'inteiro',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'inteiro',
          documentation: 'Declara variável inteira',
          range: range,
        },
        {
          label: 'real',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'real',
          documentation: 'Declara variável real (float)',
          range: range,
        },
        {
          label: 'caractere',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'caractere',
          documentation: 'Declara variável caractere (string)',
          range: range,
        },
        {
          label: 'booleano',
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: 'booleano',
          documentation: 'Declara variável booleana',
          range: range,
        },

        // Valores booleanos
        {
          label: 'verdadeiro',
          kind: monaco.languages.CompletionItemKind.Constant,
          insertText: 'verdadeiro',
          documentation: 'Valor booleano verdadeiro',
          range: range,
        },
        {
          label: 'falso',
          kind: monaco.languages.CompletionItemKind.Constant,
          insertText: 'falso',
          documentation: 'Valor booleano falso',
          range: range,
        },

        // Operadores lógicos
        {
          label: 'e',
          kind: monaco.languages.CompletionItemKind.Operator,
          insertText: 'e',
          documentation: 'Operador lógico AND',
          range: range,
        },
        {
          label: 'ou',
          kind: monaco.languages.CompletionItemKind.Operator,
          insertText: 'ou',
          documentation: 'Operador lógico OR',
          range: range,
        },
        {
          label: 'nao',
          kind: monaco.languages.CompletionItemKind.Operator,
          insertText: 'nao',
          documentation: 'Operador lógico NOT',
          range: range,
        },

        // Operadores matemáticos especiais
        {
          label: 'div',
          kind: monaco.languages.CompletionItemKind.Operator,
          insertText: 'div',
          documentation: 'Divisão inteira',
          range: range,
        },
        {
          label: 'mod',
          kind: monaco.languages.CompletionItemKind.Operator,
          insertText: 'mod',
          documentation: 'Módulo (resto da divisão)',
          range: range,
        },
      ]

      return { suggestions: suggestions }
    },
  })
}
