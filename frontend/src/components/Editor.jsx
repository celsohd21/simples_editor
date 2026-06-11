import { useEffect, useRef } from 'react'
import * as monaco from 'monaco-editor'

const MARKER_OWNER = 'simples-compiler'

export default function Editor({
  value = '',
  onChange = () => {},
  language = 'simples',
  theme = 'vs-dark',
  readOnly = false,
  minimap = true,
  markers = [],
}) {
  const editorRef = useRef(null)
  const containerRef = useRef(null)
  const markersRef = useRef(null)
  markersRef.current = markers

  useEffect(() => {
    if (!containerRef.current) return

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
      contextmenu: true,
      rulers: [80, 120],
      scrollbar: {
        vertical: 'auto',
        horizontal: 'auto',
      },
    })

    editorRef.current = editor

    editor.onDidChangeModelContent(() => {
      const newValue = editor.getValue()
      onChange(newValue)
    })

    editor.addCommand(
      monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS,
      () => {
        const event = new CustomEvent('editor:save', {
          detail: { code: editor.getValue() },
        })
        window.dispatchEvent(event)
      }
    )

    return () => {
      editor.dispose()
    }
  }, [])

  useEffect(() => {
    if (editorRef.current && editorRef.current.getValue() !== value) {
      editorRef.current.setValue(value)
    }
  }, [value])

  useEffect(() => {
    const editor = editorRef.current
    if (!editor) return

    const model = editor.getModel()
    if (!model) return

    const m = markersRef.current

    if (!m || m.length === 0) {
      monaco.editor.setModelMarkers(model, MARKER_OWNER, [])
      return
    }

    const monacoMarkers = m.map((err) => ({
      severity:
        err.severity === 'warning'
          ? monaco.MarkerSeverity.Warning
          : monaco.MarkerSeverity.Error,
      message: err.message,
      startLineNumber: err.line || 1,
      startColumn: err.column || 1,
      endLineNumber: err.endLine || err.line || 1,
      endColumn: err.endColumn || (err.column || 1) + 1,
    }))

    monaco.editor.setModelMarkers(model, MARKER_OWNER, monacoMarkers)
  }, [markers])

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
