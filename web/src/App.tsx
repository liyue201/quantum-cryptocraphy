import { useEffect, useMemo, useRef, useState } from 'react'
import Editor from '@monaco-editor/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { BookMeta, Chapter, RunResult, getChapter, getMeta, listChapters, runCode } from './api'

// UI copy (Chinese only)
const UI = {
  brand: '量子密码学',
  partPrefix: '第 ',
  partSuffix: ' 篇 · ',
  preface: '前言',
  unit: ' 节',
  loading: '正在加载章节…',
  dragW: '拖动调整宽度',
  collapse: '收起示例',
  playground: '可运行示例',
  running: '运行中…',
  run: '▶ 运行',
  output: '输出',
  runHint: '点击「运行」查看结果。',
  sideToggle: '示例代码',
  sideToggleTitle: '展开示例代码',
  themeDark: '切换到深色',
  themeLight: '切换到浅色',
  github: '在 GitHub 上查看源码',
}

// Returns the part name from book metadata (-1 = preface)
function partName(meta: BookMeta, part: number): string {
  const d = meta.parts?.[String(part)]
  const name = d ? d.zh : ''
  return part === -1 ? name || UI.preface : `${UI.partPrefix}${part}${UI.partSuffix}${name}`
}

// Empty placeholder used before meta finishes loading, so rendering never fails
const emptyMeta: BookMeta = { title_zh: '', title_en: '', subtitle_zh: '', subtitle_en: '', github: '', parts: {} }

export default function App() {
  const [meta, setMeta] = useState<BookMeta | null>(null)
  const [chapters, setChapters] = useState<Chapter[]>([])
  const [current, setCurrent] = useState<Chapter | null>(null)
  const [code, setCode] = useState('')
  const [result, setResult] = useState<RunResult | null>(null)
  const [running, setRunning] = useState(false)

  // Example panel is expanded by default, but takes little space (width adjustable by dragging the divider)
  const [expanded, setExpanded] = useState(true)
  const [playPct, setPlayPct] = useState(40)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [outputOpen, setOutputOpen] = useState(false)

  // Part group collapse: by default only the "preface" and the current part (part 0) are expanded
  const [openParts, setOpenParts] = useState<Set<number>>(() => new Set([-1, 0]))

  // Sync the theme to the root data-theme attribute, triggering the CSS variable switch
  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  const midRef = useRef<HTMLElement>(null)

  useEffect(() => {
    listChapters()
      .then((cs) => {
        setChapters(cs)
        if (cs.length > 0) select(cs[0].id)
      })
      .catch((e) => console.error(e))

    getMeta()
      .then((m) => {
        setMeta(m)
        document.title = `${m.title_zh || '量子密码学'} · ${m.subtitle_zh || '在线交互书'}`
      })
      .catch((e) => console.error(e))
  }, [])

  async function select(id: string) {
    const ch = await getChapter(id)
    setCurrent(ch)
    setCode(ch.example)
    setResult(null)
    // When a chapter is selected, automatically expand its part
    setOpenParts((prev) => new Set(prev).add(ch.part))
  }

  function togglePart(part: number) {
    setOpenParts((prev) => {
      const n = new Set(prev)
      if (n.has(part)) n.delete(part)
      else n.add(part)
      return n
    })
  }

  async function handleRun() {
    setRunning(true)
    setResult(null)
    try {
      const res = await runCode(code, current?.lang || 'py')
      setResult(res)
      setOutputOpen(true) // auto-expand the output after running
    } catch (e) {
      setResult({ stdout: '', stderr: String(e), exit_code: -1, elapsed_ms: 0 })
      setOutputOpen(true)
    } finally {
      setRunning(false)
    }
  }

  // Drag the middle divider to adjust the width ratio between the body and example panel
  function onDividerDown(e: React.MouseEvent) {
    e.preventDefault()
    const mid = midRef.current
    if (!mid) return
    const startX = e.clientX
    const startPct = playPct
    const onMove = (ev: MouseEvent) => {
      const rect = mid.getBoundingClientRect()
      if (rect.width === 0) return
      const next = Math.min(78, Math.max(24, startPct - ((ev.clientX - startX) / rect.width) * 100))
      setPlayPct(next)
    }
    const onUp = () => {
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
      document.body.style.cursor = ''
    }
    document.body.style.cursor = 'col-resize'
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }

  const groups = useMemo(() => {
    const map = new Map<number, Chapter[]>()
    for (const c of chapters) {
      const arr = map.get(c.part) ?? []
      arr.push(c)
      map.set(c.part, arr)
    }
    return [...map.entries()].sort((a, b) => a[0] - b[0])
  }, [chapters])

  // Only show the "run live example" panel when the chapter has example code (pure-text chapters like the preface hide it)
  const hasExample = !!current && current.example.trim().length > 0

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand-row">
          <div className="brand">
            <span className="brand-title">{meta ? meta.title_zh : UI.brand}</span>
            {meta && <span className="brand-sub">{meta.subtitle_zh}</span>}
          </div>
        </div>
        {groups.map(([part, items]) => (
          <div key={part} className="part">
            <button className="part-title" onClick={() => togglePart(part)}>
              <span className="caret">{openParts.has(part) ? '▾' : '▸'}</span>
              <span className="part-name">{partName(meta ?? emptyMeta, part)}</span>
              <span className="part-count">
                {items.length}
                {UI.unit}
              </span>
            </button>
            {openParts.has(part) &&
              items.map((c) => (
                <button
                  key={c.id}
                  className={`chapter ${current?.id === c.id ? 'active' : ''}`}
                  onClick={() => select(c.id)}
                >
                  {c.title_zh}
                </button>
              ))}
          </div>
        ))}
      </aside>

      <main ref={midRef} className="mid">
        <section className="article">
          <div className="article-topbar">
            <div className="controls">
              <button
                className="theme-btn"
                onClick={() => setTheme((th) => (th === 'dark' ? 'light' : 'dark'))}
                title={theme === 'dark' ? UI.themeLight : UI.themeDark}
              >
                {theme === 'dark' ? '☀' : '☾'}
              </button>
              {meta?.github && (
                <a
                  className="theme-btn github-link"
                  href={meta.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  title={UI.github}
                  aria-label={UI.github}
                >
                  <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true">
                    <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z" />
                  </svg>
                </a>
              )}
            </div>
          </div>
          {current ? (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {current.content_zh}
            </ReactMarkdown>
          ) : (
            <p className="muted">{UI.loading}</p>
          )}
        </section>

        {expanded && hasExample && (
          <>
            <div className="divider" onMouseDown={onDividerDown} title={UI.dragW} />
            <section className="playground" style={{ flexBasis: `${playPct}%` }}>
              <div className="toolbar">
                <button className="icon-btn" onClick={() => setExpanded(false)} title={UI.collapse}>
                  ➤
                </button>
                <span className="toolbar-title">{UI.playground}</span>
                <button className="run-btn" onClick={handleRun} disabled={running || !current}>
                  {running ? UI.running : UI.run}
                </button>
              </div>
              <div className="editor-wrap">
                <Editor
                  height="100%"
                  defaultLanguage={current?.lang === 'py' || current?.lang === 'python' ? 'python' : 'go'}
                  theme={theme === 'dark' ? 'vs-dark' : 'light'}
                  value={code}
                  onChange={(v) => setCode(v ?? '')}
                  options={{ minimap: { enabled: false }, fontSize: 13 }}
                />
              </div>
              <div className={`output ${outputOpen ? '' : 'collapsed'}`}>
                <div className="output-head" onClick={() => setOutputOpen((o) => !o)}>
                  <button className="icon-btn">{outputOpen ? '▾' : '▸'}</button>
                  <span className="toolbar-title">{UI.output}</span>
                  {result && (
                    <span className="out-meta">
                      exit {result.exit_code} · {result.elapsed_ms} ms
                    </span>
                  )}
                </div>
                {outputOpen && (
                  <pre className="output-body">
                    {result
                      ? `${result.stderr ? 'stderr:\n' + result.stderr + '\n' : ''}${result.stdout}${
                          result.error ? '\n' + result.error : ''
                        }`
                      : UI.runHint}
                  </pre>
                )}
              </div>
            </section>
          </>
        )}
      </main>

      {/* Expand entry in the collapsed state (only when the chapter has an example) */}
      {!expanded && hasExample && (
        <button className="side-toggle" onClick={() => setExpanded(true)} title={UI.sideToggleTitle}>
          {UI.sideToggle}
        </button>
      )}
    </div>
  )
}