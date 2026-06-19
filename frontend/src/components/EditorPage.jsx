import { useState, useEffect, useRef, useCallback } from 'react'
import { PanelGroup, Panel, PanelResizeHandle } from 'react-resizable-panels'
import Editor from './Editor'
import NasmPanel from './NasmPanel'
import './EditorPage.css'

/**
 * Página principal com o Monaco Editor integrado.
 * Componentes da página:
 * - Editor de código (esquerda)
 * - Painel NASM (direita)
 * - Terminal (inferior)
 */
export default function EditorPage({ onLogout }) {
  const [code, setCode] = useState(
    'programa HelloWorld\ninicio\n  escreva "Ola, SIMPLES!"\nfim'
  )

  const handleExample = (name) => {
    const examples = {
      hello: 'programa HelloWorld\ninicio\n  escreva "Ola, SIMPLES!"\nfim',
      soma: 'programa Soma\ninicio\n  inteiro a\n  inteiro b\n  inteiro resultado\n  leia a\n  leia b\n  resultado := a + b\n  escreva resultado\nfim',
      condicional: 'programa Condicional\ninicio\n  inteiro x\n  leia x\n  se x > 0 entao\n    escreva "positivo"\n  senao\n    escreva "negativo ou zero"\n  fimse\nfim',
      contagem: 'programa Contagem\ninicio\n  inteiro i\n  i := 1\n  enquanto i <= 5 faca\n    escreva i\n    i := i + 1\n  fimenquanto\nfim',
    }
    if (examples[name]) setCode(examples[name])
  }
  const [savedCode, setSavedCode] = useState(code)
  const [isRunning, setIsRunning] = useState(false)
  const [namsCollapsed, setNasmCollapsed] = useState(false)
  const [nasmOutput, setNasmOutput] = useState('')
  const [terminalOutput, setTerminalOutput] = useState('')
  const [compilationErrors, setCompilationErrors] = useState([])
  const [stdinInput, setStdinInput] = useState('')
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

  const handleRun = useCallback(async () => {
    setIsRunning(true)
    setCompilationErrors([])
    setNasmOutput('')
    setTerminalOutput('🔄 Compilando...')

    try {
      const token = localStorage.getItem('auth_token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = 'Bearer ' + token

      const response = await fetch('/api/run', {
        method: 'POST',
        headers,
        body: JSON.stringify({ code, stdin: stdinInput }),
      })

      const result = await response.json()

      if (result.ok) {
        setNasmOutput(result.nasm || '')
        setCompilationErrors([])

        setTerminalOutput((result.stdout || '') + (result.stderr || ''))
      } else {
        const errs = result.errors || []
        const markers = errs.map((e) => ({
          line: e.line || 1,
          column: e.column || 1,
          message: e.message,
          severity: e.phase === 'warning' ? 'warning' : 'error',
        }))
        setCompilationErrors(markers)
        setTerminalOutput(errs.map((e) => `${e.phase}:${e.line}:${e.column}: ${e.message}`).join('\n'))
        if (result.nasm) setNasmOutput(result.nasm)
      }
    } catch (err) {
      setCompilationErrors([])
      setNasmOutput('')
      setTerminalOutput('[ERRO] Nao foi possivel conectar ao servidor de compilacao.\n' + err.message)
    } finally {
      setIsRunning(false)
    }
  }, [code])

  const handleClear = () => {
    if (confirm('Deseja limpar o editor?')) {
      setCode('')
    }
  }

  const handleReset = () => {
    if (confirm('Deseja restaurar o código de exemplo?')) {
      setCode('programa Soma\ninicio\n  inteiro a\n  inteiro b\n  inteiro resultado\n  leia a\n  leia b\n  resultado := a + b\n  escreva resultado\nfim')
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
                    <p className="placeholder-hint">(Clique em Run para executar)</p>
                  </>
                )}
              </div>
              <div className="terminal-stdin">
                <span className="stdin-label">stdin:</span>
                <input
                  type="text"
                  className="stdin-input"
                  placeholder="Entrada para o programa (leia)"
                  value={stdinInput}
                  onChange={(e) => setStdinInput(e.target.value)}
                  disabled={isRunning}
                />
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
