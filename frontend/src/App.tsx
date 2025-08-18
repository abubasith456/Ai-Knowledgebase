import React, { useState } from 'react'
import { http } from './lib/http'
import { Button } from './components/Button'
import { Card, CardContent, CardHeader, CardTitle } from './components/Card'
import { Badge } from './components/Badge'
import { UploadArea } from './components/UploadArea'

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
  const [uploading, setUploading] = useState<boolean>(false)
  const [ingestLogs, setIngestLogs] = useState<IngestLog[]>([])
  const [fileId, setFileId] = useState<string>('')
  const [documentName, setDocumentName] = useState<string>('')
  const [question, setQuestion] = useState<string>('')
  const [answer, setAnswer] = useState<string>('')
  const [contexts, setContexts] = useState<RetrievedContext[]>([])
  const [uploadJob, setUploadJob] = useState<JobInfo | null>(null)
  const [ingestJob, setIngestJob] = useState<JobInfo | null>(null)

  async function doUpload(f: File) {
    setUploading(true)
    try {
      const form = new FormData()
      form.append('file', f)
      const res = await http.post('/upload', form, {
        onUploadProgress: p => {
          setIngestLogs(prev => [
            ...prev,
            { ts: new Date().toISOString(), level: 'info', message: `Uploaded ${Math.round((p.progress || 0) * 100)}%` }
          ])
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
      const res = await http.post('/ingest', { file_id: fileId, document_name: documentName })
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
      const res = await http.post('/query', { question, top_k: 5 })
      setAnswer(res.data.answer)
      setContexts(res.data.contexts)
    } catch (e: any) {
      setAnswer('Query failed: ' + e?.message)
      setContexts([])
    }
  }

  async function fetchJob(jobId: string): Promise<JobInfo> {
    const res = await http.get(`/jobs/${jobId}`)
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
    <div className="max-w-6xl mx-auto p-8 space-y-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Doc KB</h1>
        <div className="text-sm text-gray-500">Production UI</div>
      </header>

      <section className="space-y-3">
        <Card>
          <CardHeader>
            <CardTitle>Upload & Ingest</CardTitle>
          </CardHeader>
          <CardContent>
            <UploadArea onFile={doUpload} disabled={uploading} />
            <div className="flex gap-3 items-center">
              <input
                className="border rounded px-3 py-2 flex-1"
                placeholder="Document Name"
                value={documentName}
                onChange={e => setDocumentName(e.target.value)}
              />
              <Button disabled={uploading || !fileId || !documentName} onClick={ingest}>Start Ingest</Button>
            </div>
            <div className="text-sm space-y-1">
              {uploadJob && (
                <div>Upload <Badge color={uploadJob.status === 'completed' ? 'green' : uploadJob.status === 'failed' ? 'red' : 'blue'}>{uploadJob.status}</Badge></div>
              )}
              {ingestJob && (
                <div>
                  Ingest <Badge color={ingestJob.status === 'completed' ? 'green' : ingestJob.status === 'failed' ? 'red' : 'blue'}>{ingestJob.status}</Badge>
                  {ingestJob.indexing_status && (
                    <span> · Indexing <Badge color={ingestJob.indexing_status === 'completed' ? 'green' : ingestJob.indexing_status === 'failed' ? 'red' : 'yellow'}>{ingestJob.indexing_status}</Badge></span>
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
          </CardContent>
        </Card>
      </section>

      <section className="space-y-3">
        <Card>
          <CardHeader>
            <CardTitle>Ask the Knowledge Base</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-3">
              <input
                className="border rounded px-3 py-2 flex-1"
                placeholder="Your question"
                value={question}
                onChange={e => setQuestion(e.target.value)}
              />
              <Button onClick={ask}>Ask</Button>
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
          </CardContent>
        </Card>
      </section>
    </div>
  )
}