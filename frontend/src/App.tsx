import React, { useEffect, useMemo, useState } from 'react'
import axios from 'axios'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

type IngestLog = { ts: string, level: 'info'|'error', message: string }

type RetrievedContext = {
  chunk_id: string
  score: number
  text: string
  metadata: Record<string, any>
}

type JobInfo = {
  id: string
  type: string
  status: string
  message?: string
  file_id?: string
  document_name?: string
  num_chunks?: number
  indexing_status?: string
  started_at?: string
  finished_at?: string
}

export default function App() {
  const [apiKey, setApiKey] = useState<string>(localStorage.getItem('kb_api_key') || '')
  const [uploading, setUploading] = useState<boolean>(false)
  const [ingestLogs, setIngestLogs] = useState<IngestLog[]>([])
  const [fileId, setFileId] = useState<string>('')
  const [documentName, setDocumentName] = useState<string>('')
  const [question, setQuestion] = useState<string>('')
  const [answer, setAnswer] = useState<string>('')
  const [contexts, setContexts] = useState<RetrievedContext[]>([])
  const [uploadJob, setUploadJob] = useState<JobInfo | null>(null)
  const [ingestJob, setIngestJob] = useState<JobInfo | null>(null)

  const client = useMemo(() => axios.create({ baseURL: BACKEND_URL }), [])

  useEffect(() => {
    if (apiKey) localStorage.setItem('kb_api_key', apiKey)
  }, [apiKey])

  async function generateKey() {
    const res = await client.post('/auth/generate')
    setApiKey(res.data.api_key)
  }

  async function registerKey() {
    if (!apiKey) return
    await client.post('/auth/register', { api_key: apiKey })
  }

  async function handleUpload(ev: React.ChangeEvent<HTMLInputElement>) {
    const f = ev.target.files?.[0]
    if (!f) return
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', f)
      const res = await client.post('/upload', form, {
        headers: { 'x-api-key': apiKey },
        onUploadProgress: p => {
          setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'info', message: `Uploaded ${Math.round((p.progress || 0)*100)}%` }])
        }
      })
      setFileId(res.data.file_id)
      setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'info', message: 'File uploaded' }])
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'info', message: `Upload job: ${res.data.job_id}` }])
        startPolling(res.data.job_id, setUploadJob)
      }
    } catch (e: any) {
      setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'error', message: `Upload failed: ${e?.message}` }])
    } finally {
      setUploading(false)
    }
  }

  async function ingest() {
    if (!fileId || !documentName) return
    setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'info', message: 'Starting ingestion...' }])
    try {
      const res = await client.post('/ingest', { file_id: fileId, document_name: documentName }, { headers: { 'x-api-key': apiKey }})
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'info', message: `Ingest job started: ${res.data.job_id}` }])
        startPolling(res.data.job_id, setIngestJob)
      }
    } catch (e: any) {
      setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'error', message: `Ingestion failed: ${e?.message}` }])
    }
  }

  async function ask() {
    if (!question) return
    try {
      const res = await client.post('/query', { question, top_k: 5 }, { headers: { 'x-api-key': apiKey }})
      setAnswer(res.data.answer)
      setContexts(res.data.contexts)
    } catch (e: any) {
      setAnswer('Query failed: ' + e?.message)
      setContexts([])
    }
  }

  async function fetchJob(jobId: string): Promise<JobInfo> {
    const res = await client.get(`/jobs/${jobId}`, { headers: { 'x-api-key': apiKey } })
    return res.data as JobInfo
  }

  function startPolling(jobId: string, setter: (j: JobInfo) => void) {
    const poll = async () => {
      try {
        const info = await fetchJob(jobId)
        setter(info)
        if (info.status === 'processing') {
          setTimeout(poll, 1500)
        } else if (info.status === 'completed') {
          setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'info', message: `${info.type} completed` }])
        } else if (info.status === 'failed') {
          setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'error', message: `${info.type} failed: ${info.message || ''}` }])
        }
      } catch (e: any) {
        setIngestLogs(prev => [...prev, { ts: new Date().toISOString(), level: 'error', message: `Job polling error: ${e?.message}` }])
      }
    }
    poll()
  }

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Doc KB</h1>
        <div className="flex gap-2 items-center">
          <input className="border rounded px-2 py-1 w-80" placeholder="API Key" value={apiKey} onChange={e => setApiKey(e.target.value)} />
          <button className="bg-gray-200 px-3 py-1 rounded" onClick={generateKey}>Generate</button>
          <button className="bg-blue-600 text-white px-3 py-1 rounded" onClick={registerKey}>Register</button>
        </div>
      </header>

      <section className="space-y-3">
        <h2 className="font-semibold">Upload & Ingest</h2>
        <div className="flex gap-3 items-center">
          <input type="file" accept="application/pdf" onChange={handleUpload} />
          <input className="border rounded px-2 py-1" placeholder="Document Name" value={documentName} onChange={e => setDocumentName(e.target.value)} />
          <button disabled={uploading || !fileId || !documentName} className="bg-green-600 text-white px-3 py-1 rounded disabled:opacity-50" onClick={ingest}>Ingest</button>
        </div>
        <div className="text-sm space-y-1">
          {uploadJob && (
            <div>Upload status: <span className="font-medium">{uploadJob.status}</span></div>
          )}
          {ingestJob && (
            <div>
              Ingest status: <span className="font-medium">{ingestJob.status}</span>
              {ingestJob.indexing_status && (
                <span> · Indexing: <span className="font-medium">{ingestJob.indexing_status}</span></span>
              )}
              {typeof ingestJob.num_chunks === 'number' && ingestJob.status === 'completed' && (
                <span> · Chunks: <span className="font-medium">{ingestJob.num_chunks}</span></span>
              )}
            </div>
          )}
        </div>
        <div className="bg-gray-100 dark:bg-gray-800 rounded p-3 h-40 overflow-auto text-sm">
          {ingestLogs.map((l, i) => (
            <div key={i} className={l.level === 'error' ? 'text-red-600' : ''}>[{l.ts}] {l.message}</div>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Ask</h2>
        <div className="flex gap-3">
          <input className="border rounded px-2 py-1 flex-1" placeholder="Your question" value={question} onChange={e => setQuestion(e.target.value)} />
          <button className="bg-indigo-600 text-white px-3 py-1 rounded" onClick={ask}>Ask</button>
        </div>
        {answer && (
          <div className="space-y-2">
            <div className="font-semibold">Answer</div>
            <div className="bg-white dark:bg-gray-900 border rounded p-3 whitespace-pre-wrap">{answer}</div>
            <div className="font-semibold">Contexts</div>
            <div className="grid md:grid-cols-2 gap-3">
              {contexts.map((c) => (
                <div key={c.chunk_id} className="bg-white dark:bg-gray-900 border rounded p-3">
                  <div className="text-xs text-gray-500">score: {c.score.toFixed(4)}</div>
                  <div className="text-xs text-gray-500">{JSON.stringify(c.metadata)}</div>
                  <div className="mt-2 text-sm whitespace-pre-wrap">{c.text}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  )
}