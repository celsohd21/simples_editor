import { useEffect, useRef } from 'react'
import * as monaco from 'monaco-editor'

/**
 * Componente do Editor Monaco para código SIMPLES.
 * 
 * Props:
 *   value: string - Código a exibir
 *   onChange: function - Callback quando código muda
 *   language: string - Linguagem (padrão: 'simples')
 *   theme: string - Tema (padrão: 'vs-dark')
 *   readOnly: boolean - Se é somente leitura (padrão: false)
 */
export default function Editor({
  value = '',
  onChange = () => {},
  language = 'simples',
  theme = 'vs-dark',
  readOnly = false,
  minimap = true,
}) {
  const editorRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    // Cria a instância do editor
    const editor = monaco.editor.create(containerRef.current, {
      value: value,
      language: language,
      theme: language === 'simples' ? 'simples-dark' : theme,
      readOnly: readOnly,
      automaticLayout: true,
      minimap: {
        enabled: minimap,
      },
      fontSize: 14,
      fontFamily: "'Fira Code', 'Monaco', 'Courier New', monospace",
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      wordWrap: 'off',
      formatOnPaste: true,
      formatOnType: true,
      quickSuggestions: {
        other: true,
        comments: false,
        strings: true,
      },
      suggestOnTriggerCharacters: true,
      acceptSuggestionOnCommitCharacter: true,
      // Atalhos padrão
      contextmenu: true,
      rulers: [80, 120],
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
      },
    })

    editorRef.current = editor

    // Listener para mudanças de código
    editor.onDidChangeModelContent(() => {
      const newValue = editor.getValue()
      onChange(newValue)
    })

    // Listener para Ctrl+S (salvar)
    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
      () => {
        // Dispatch evento customizado para salvar
        const event = new CustomEvent('editor:save', {
          detail: { code: editor.getValue() },
        })
        window.dispatchEvent(event)
      }
    )

    // Cleanup
    return () => {
      editor.dispose()
    }
  }, [])

  // Atualiza o valor quando prop muda (de fora)
  useEffect(() => {
    if (editorRef.current && editorRef.current.getValue() !== value) {
      editorRef.current.setValue(value)
    }
  }, [value])

  return (
    <div
      ref={containerRef}
      style={{
        width: '100%',
        height: '100%',
        border: '1px solid #333',
        borderRadius: '4px',
        overflow: 'hidden',
      }}
    />
  )
}
