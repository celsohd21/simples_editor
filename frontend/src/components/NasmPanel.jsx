import { useEffect, useRef } from 'react'
import * as monaco from 'monaco-editor'

/**
 * Painel NASM read-only baseado no Monaco Editor.
 *
 * Props:
 *   value: string - Código assembly a exibir
 */
export default function NasmPanel({ value = '' }) {
  const editorRef = useRef(null)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!containerRef.current) return

    const editor = monaco.editor.create(containerRef.current, {
      value: value,
      language: 'nasm',
      theme: 'nasm-dark',
      readOnly: true,
      automaticLayout: true,
      minimap: {
        enabled: false,
      },
      fontSize: 13,
      fontFamily: "'Fira Code', 'Monaco', 'Courier New', monospace",
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      wordWrap: 'off',
      contextmenu: false,
      rulers: [],
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
      },
      overviewRulerLanes: 0,
      hideCursorInOverviewRuler: true,
      overviewRulerBorder: false,
      renderLineHighlight: 'none',
      cursorStyle: 'line',
      renderWhitespace: 'selection',
      bracketPairColorization: {
        enabled: true,
      },
    })

    editorRef.current = editor

    return () => {
      editor.dispose()
    }
  }, [])

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
        overflow: 'hidden',
      }}
    />
  )
}
