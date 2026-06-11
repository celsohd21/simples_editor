import { useState, useEffect, useRef, useCallback } from 'react'
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels'
import Editor from './Editor'
import NasmPanel from './NasmPanel'
import './EditorPage.css'

const MOCK_NASM = `; Generated NASM Assembly
section .data
    msg db "Ola, SIMPLES!", 0

section .text
    global _start
_start:
    mov rax, 1
    mov rdi, 1
    mov rsi, msg
    mov rdx, 13
    syscall
    mov rax, 60
    mov rdi, 0
    syscall`

function mockCompile(source) {
  const lines = source.split('\n')
  const errors = []

  const cleaned = source
    .split('\n')
    .map((l) => l.replace(/{[^}]*}/g, '').trim())
    .filter((l) => l.length > 0 && !l.startsWith('//'))

  if (cleaned.length === 0) {
    return { errors, nasm: '', terminal: '[!] Nenhum codigo para compilar.\n' }
  }

  cleaned.forEach((line, i) => {
    if (line.length > 80) {
      errors.push({
        line: i + 1,
        column: 81,
        message: 'Linha muito longa (>80 caracteres)',
        severity: 'warning',
      })
    }
  })

  const hasPrograma = cleaned.some((l) => /\bprograma\b/i.test(l))
  const hasInicio = cleaned.some((l) => /\binicio\b/i.test(l))
  const hasFim = cleaned.some((l) => /\bfim\b/i.test(l))

  if (cleaned.some((l) => /\binicio\b/i.test(l)) && !hasFim) {
    errors.push({
      line: null,
      column: null,
      message: 'Bloco "inicio" sem "fim" correspondente — esperado "fim" no final do programa',
      severity: 'error',
    })
  }

  if (cleaned.some((l) => /\bfim\b/i.test(l)) && !hasInicio) {
    errors.push({
      line: null,
      column: null,
      message: '"fim" sem "inicio" correspondente',
      severity: 'error',
    })
  }

  if (hasPrograma && !hasInicio) {
    errors.push({
      line: null,
      column: null,
      message: 'Esperado "inicio" apos "programa"',
      severity: 'error',
    })
  }

  if (hasInicio && !hasPrograma && !hasFim) {
    errors.push({
      line: null,
      column: null,
      message: 'Programa deve comecar com "programa <nome>"',
      severity: 'error',
    })
  }

  const declaredVars = new Set()
  const usedVars = new Set()

  cleaned.forEach((line, i) => {
    const declMatch = line.match(
      /\b(inteiro|real|caractere|booleano)\s+([a-zA-Z_]\w*)/i
    )
    if (declMatch) {
      declaredVars.add(declMatch[2].toLowerCase())
    }

    const useMatch = line.match(/\b(leia|escreva)\s+([a-zA-Z_]\w*)/i)
    if (useMatch) {
      usedVars.add(useMatch[2].toLowerCase())
    }
  })

  usedVars.forEach((v) => {
    if (!declaredVars.has(v)) {
      const lineNum =
        cleaned.findIndex(
          (l) =>
            new RegExp(`\\b(leia|escreva)\\s+${v}\\b`, 'i').test(l)
        ) + 1
      errors.push({
        line: lineNum > 0 ? lineNum : null,
        column: null,
        message: `Variavel "${v}" nao declarada`,
        severity: 'error',
      })
    }
  })

  const hasErrors = errors.some((e) => e.severity === 'error')
  const warnings = errors.filter((e) => e.severity === 'warning')
  const errs = errors.filter((e) => e.severity === 'error')

  if (!hasErrors) {
    const nasm = MOCK_NASM
    const termLines = [
      '[OK] Compilacao concluida com sucesso!',
      `[i] Linhas: ${lines.length}`,
      `[i] Avisos: ${warnings.length}`,
      `[i] Erros: ${errs.length}`,
      '',
      '$ ./output',
      'Ola, SIMPLES!',
      '',
      '[OK] Execucao finalizada (codigo de saida: 0)',
    ]
    const terminal = termLines.join('\n')
    return { errors, nasm, terminal }
  }

  const termLines = [
    '[FALHA] Erros de compilacao encontrados:',
    ...errs.map(
      (e) =>
        `  ${e.line ? `Linha ${e.line}` : '---'}: ${e.message}`
    ),
    '',
    `[i] Total: ${errs.length} erro(s), ${warnings.length} aviso(s)`,
  ]
  const terminal = termLines.join('\n')

  return { errors, nasm: '', terminal }
}

/**
 * Página principal com o Monaco Editor integrado.
 * Componentes da página:
 * - Editor de código (esquerda)
 * - Painel NASM (direita)
 * - Terminal (inferior)
 */
export default function EditorPage({ onLogout }) {
  const [code, setCode] = useState(
    `programa Exemplo\ninicio\n  inteiro x\n  leia x\n  escreva x\nfim`
  )
  const [savedCode, setSavedCode] = useState(code)
  const [isRunning, setIsRunning] = useState(false)
  const [namsCollapsed, setNasmCollapsed] = useState(false)
  const [nasmOutput, setNasmOutput] = useState('')
  const [terminalOutput, setTerminalOutput] = useState('')
  const [compilationErrors, setCompilationErrors] = useState([])
  const resizerRef = useRef(null)

  // Salva o código em localStorage
  useEffect(() => {
    const handleSave = (e) => {
      setSavedCode(code)
      console.log('Código salvo:', code)
    }
    window.addEventListener('editor:save', handleSave)
    return () => window.removeEventListener('editor:save', handleSave)
  }, [code])

  const handleRun = useCallback(() => {
    setIsRunning(true)
    setCompilationErrors([])
    setNasmOutput('🔄 Compilando...')
    setTerminalOutput('🔄 Compilando...')

    setTimeout(() => {
      const result = mockCompile(code)
      setCompilationErrors(result.errors)
      setNasmOutput(result.nasm)
      setTerminalOutput(result.terminal)
      setIsRunning(false)
    }, 1500)
  }, [code])

  const handleClear = () => {
    if (confirm('Deseja limpar o editor?')) {
      setCode('')
    }
  }

  const handleReset = () => {
    if (confirm('Deseja restaurar o código de exemplo?')) {
      setCode(`// Bem-vindo ao Simples Editor!\n// Escreva código SIMPLES aqui\n\nleia x\nescreva x\n`)
    }
  }

  const handleResizerDoubleClick = () => {
    setNasmCollapsed(!namsCollapsed)
  }

  const handleLogout = () => {
    onLogout()
  }

  return (
    <div className="editor-page">
      {/* Header */}
      <header className="editor-header">
        <div className="header-left">
          <h1>Simples Editor</h1>
          <span className="status-badge">Pronto</span>
        </div>
        <div className="header-right">
          <button
            className="btn btn-primary"
            onClick={handleRun}
            disabled={isRunning}
            title="Ctrl+Enter ou clique aqui"
          >
            {isRunning ? '▌ Executando...' : '▶ Run'}
          </button>
          <button className="btn btn-secondary" onClick={handleClear} title="Limpa o editor">
            Limpar
          </button>
          <button className="btn btn-secondary" onClick={handleReset} title="Restaura exemplo">
            Reset
          </button>
          <button className="btn btn-logout" onClick={handleLogout} title="Fazer logout">
            Logout
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="editor-main">
        <PanelGroup direction="vertical">
          {/* Top: Editor + NASM (Horizontal Layout) */}
          <Panel defaultSize={70} minSize={40}>
            <PanelGroup direction="horizontal">
              {/* Left Panel - Editor */}
              <Panel defaultSize={40} minSize={30}>
                <div className="editor-container">
                  <div className="panel-header">
                    <span>📝 Editor</span>
                    <span className="file-name">código.simples</span>
                  </div>
                  <Editor
                    value={code}
                    onChange={setCode}
                    language="simples"
                    theme="vs-dark"
                    readOnly={false}
                    minimap={true}
                    markers={compilationErrors}
                  />
                </div>
              </Panel>

              {/* Resizer with Double-Click Handler */}
              <PanelResizeHandle 
                className="resizer" 
                ref={resizerRef}
                onDoubleClick={handleResizerDoubleClick}
              />

              {/* Right Panel - NASM */}
              <Panel 
                defaultSize={60} 
                minSize={namsCollapsed ? 0 : 20}
                collapsible={true}
                onCollapse={() => setNasmCollapsed(true)}
                onExpand={() => setNasmCollapsed(false)}
              >
                <div className="nasm-container">
                  <div className="panel-header">
                    <span>⚙️ NASM Assembly</span>
                  </div>
                  {nasmOutput ? (
                    <NasmPanel value={nasmOutput} />
                  ) : (
                    <div className="nasm-content">
                      <p className="placeholder-text">NASM será exibido aqui após compilação</p>
                      <p className="placeholder-hint">(Clique em Run para compilar)</p>
                    </div>
                  )}
                </div>
              </Panel>
            </PanelGroup>
          </Panel>

          {/* Vertical Resizer between Editor+NASM and Terminal */}
          <PanelResizeHandle className="resizer resizer-vertical" />

          {/* Bottom Panel - Terminal */}
          <Panel defaultSize={30} minSize={10}>
            <div className="terminal-container">
              <div className="panel-header">
                <span>💻 Terminal</span>
              </div>
              <div className="terminal-content">
                {terminalOutput ? (
                  <pre className="terminal-pre">{terminalOutput}</pre>
                ) : (
                  <>
                    <p className="placeholder-text">Terminal será exibido aqui após execução</p>
                    <p className="placeholder-hint">(Clique em Run para compilar)</p>
                  </>
                )}
              </div>
            </div>
          </Panel>
        </PanelGroup>
      </main>

      {/* Status Bar */}
      <div className="status-bar">
        <span>Linhas: {code.split('\n').length}</span>
        <span>•</span>
        <span>Caracteres: {code.length}</span>
        <span>•</span>
        <span>Salvo: {savedCode === code ? 'Sim ✓' : 'Não ✗'}</span>
        <span className="status-right">UTF-8 • CRLF • Simples</span>
      </div>
    </div>
  )
}
