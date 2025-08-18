import React, { useState, useEffect } from 'react'
import { http } from './lib/http'
import { Button } from './components/Button'
import { Card, CardContent, CardHeader, CardTitle } from './components/Card'
import { Badge } from './components/Badge'
import { UploadArea } from './components/UploadArea'
import { ProgressBar } from './components/ProgressBar'
import { ThemeToggle } from './components/ThemeToggle'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/Tabs'
import { Select } from './components/Select'

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
  progress?: number
}

type Parser = {
  id: string
  name: string
  description: string
  supported_formats: string[]
}

type Index = {
  id: string
  name: string
  created_at: string
  document_count: number
  parser_id: string
}

export default function App() {
  // Theme state
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('theme') === 'dark' || 
             (!localStorage.getItem('theme') && window.matchMedia('(prefers-color-scheme: dark)').matches)
    }
    return false
  })

  // Tab state
  const [activeTab, setActiveTab] = useState('parser')

  // Parser tab state
  const [uploading, setUploading] = useState<boolean>(false)
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [ingestLogs, setIngestLogs] = useState<IngestLog[]>([])
  const [fileId, setFileId] = useState<string>('')
  const [documentName, setDocumentName] = useState<string>('')
  const [uploadJob, setUploadJob] = useState<JobInfo | null>(null)
  const [selectedParser, setSelectedParser] = useState<string>('default')
  const [availableParsers] = useState<Parser[]>([
    { id: 'default', name: 'Default Parser', description: 'Basic text extraction', supported_formats: ['pdf', 'txt', 'docx'] },
    { id: 'advanced', name: 'Advanced Parser', description: 'OCR and advanced formatting', supported_formats: ['pdf', 'png', 'jpg', 'docx'] },
    { id: 'structured', name: 'Structured Parser', description: 'For tables and structured data', supported_formats: ['csv', 'xlsx', 'json'] }
  ])

  // Indexing tab state
  const [indexName, setIndexName] = useState<string>('')
  const [selectedParserForIndex, setSelectedParserForIndex] = useState<string>('default')
  const [indices, setIndices] = useState<Index[]>([])
  const [indexingJob, setIndexingJob] = useState<JobInfo | null>(null)
  const [indexingProgress, setIndexingProgress] = useState<number>(0)

  // Query tab state
  const [question, setQuestion] = useState<string>('')
  const [answer, setAnswer] = useState<string>('')
  const [contexts, setContexts] = useState<RetrievedContext[]>([])
  const [selectedIndex, setSelectedIndex] = useState<string>('')
  const [integrationCode, setIntegrationCode] = useState<string>('')
  const [apiEndpoint, setApiEndpoint] = useState<string>('')

  // No API key needed anymore

  // Theme effect
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }, [isDark])

  // No API key generation needed

  // Load index
  async function loadIndices() {
    try {
      const res = await http.get('/index')
      setIndices(res.data || [])
    } catch (e: any) {
      console.error('Failed to load index:', e)
    }
  }

  useEffect(() => {
    loadIndices()
  }, [])

  // Upload functionality
  async function doUpload(f: File) {
    setUploading(true)
    setUploadProgress(0)
    try {
      const form = new FormData()
      form.append('file', f)
      form.append('parser_id', selectedParser)
      
      const res = await http.post('/upload', form, {
        onUploadProgress: p => {
          const progress = Math.round((p.progress || 0) * 100)
          setUploadProgress(progress)
          setIngestLogs(prev => [
            ...prev,
            { ts: new Date().toISOString(), level: 'info', message: `Uploaded ${progress}%` }
          ])
        }
      })
      
      setFileId(res.data.file_id)
      setUploadProgress(100)
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'info', 
        message: 'File uploaded successfully' 
      }])
      
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { 
          ts: new Date().toISOString(), 
          level: 'info', 
          message: `Upload job: ${res.data.job_id}` 
        }])
        startPolling(res.data.job_id, setUploadJob)
      }
    } catch (e: any) {
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'error', 
        message: `Upload failed: ${e?.message}` 
      }])
    } finally {
      setUploading(false)
    }
  }

  // Create index
  async function createIndex() {
    if (!indexName || !selectedParserForIndex) return
    
    setIndexingProgress(0)
    try {
      const res = await http.post('/index', { 
        name: indexName, 
        parser_id: selectedParserForIndex 
      })
      
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { 
          ts: new Date().toISOString(), 
          level: 'info', 
          message: `Index creation job started: ${res.data.job_id}` 
        }])
        startPolling(res.data.job_id, setIndexingJob)
      }
      
      // Refresh index list
      loadIndices()
    } catch (e: any) {
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'error', 
        message: `Index creation failed: ${e?.message}` 
      }])
    }
  }

  // Ingest document to index
  async function ingestToIndex() {
    if (!fileId || !documentName || !selectedIndex) return
    
    setIndexingProgress(0)
    setIngestLogs(prev => [...prev, { 
      ts: new Date().toISOString(), 
      level: 'info', 
      message: 'Starting ingestion to index...' 
    }])
    
    try {
      const res = await http.post('/ingest', { 
        file_id: fileId, 
        document_name: documentName,
        index_id: selectedIndex
      })
      
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { 
          ts: new Date().toISOString(), 
          level: 'info', 
          message: `Ingest job started: ${res.data.job_id}` 
        }])
        startPolling(res.data.job_id, setIndexingJob)
      }
    } catch (e: any) {
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'error', 
        message: `Ingestion failed: ${e?.message}` 
      }])
    }
  }

  // Query functionality
  async function ask() {
    if (!question) return
    try {
      const res = await http.post('/query', { 
        question, 
        top_k: 5,
        index_id: selectedIndex 
      })
      setAnswer(res.data.answer)
      setContexts(res.data.contexts)
      
      // Generate integration code
      generateIntegrationCode()
    } catch (e: any) {
      setAnswer('Query failed: ' + e?.message)
      setContexts([])
    }
  }

  // Generate integration code and API endpoint
  function generateIntegrationCode() {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'
    setApiEndpoint(`${backendUrl}/query`)
    
    const curlCode = `curl -X POST "${backendUrl}/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "${question}",
    "top_k": 5,
    "index_id": "${selectedIndex}"
  }'`

    const pythonCode = `import requests

url = "${backendUrl}/query"
headers = {
    "Content-Type": "application/json"
}
data = {
    "question": "${question}",
    "top_k": 5,
    "index_id": "${selectedIndex}"
}

response = requests.post(url, json=data, headers=headers)
result = response.json()`

    const jsCode = `const response = await fetch('${backendUrl}/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    question: '${question}',
    top_k: 5,
    index_id: '${selectedIndex}'
  })
});

const result = await response.json();`

    setIntegrationCode(`# cURL
${curlCode}

# Python
${pythonCode}

# JavaScript
${jsCode}`)
  }

  // Job polling
  async function fetchJob(jobId: string): Promise<JobInfo> {
    const res = await http.get(`/jobs/${jobId}`)
    return res.data as JobInfo
  }

  function startPolling(jobId: string, setter: (j: JobInfo) => void) {
    const poll = async () => {
      try {
        const info = await fetchJob(jobId)
        setter(info)
        
        // Update progress if available
        if (info.progress !== undefined) {
          if (setter === setIndexingJob) {
            setIndexingProgress(info.progress)
          }
        }
        
        if (info.status === 'processing') {
          setTimeout(poll, 1500)
        } else if (info.status === 'completed') {
          setIngestLogs(prev => [...prev, { 
            ts: new Date().toISOString(), 
            level: 'info', 
            message: `${info.type} completed` 
          }])
          if (setter === setIndexingJob) {
            setIndexingProgress(100)
            loadIndices() // Refresh indices list
          }
        } else if (info.status === 'failed') {
          setIngestLogs(prev => [...prev, { 
            ts: new Date().toISOString(), 
            level: 'error', 
            message: `${info.type} failed: ${info.message || ''}` 
          }])
        }
      } catch (e: any) {
        setIngestLogs(prev => [...prev, { 
          ts: new Date().toISOString(), 
          level: 'error', 
          message: `Job polling error: ${e?.message}` 
        }])
      }
    }
    poll()
  }



  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-7xl mx-auto p-6 space-y-8">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Doc KB
            </h1>
            <p className="text-gray-600 dark:text-gray-400">Document Knowledge Base System</p>
          </div>
          <ThemeToggle isDark={isDark} onToggle={() => setIsDark(!isDark)} />
        </header>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="parser">Parser</TabsTrigger>
            <TabsTrigger value="indexing">Index</TabsTrigger>
            <TabsTrigger value="query">Query & Test</TabsTrigger>
          </TabsList>

          <TabsContent value="parser">
            <Card>
              <CardHeader>
                <CardTitle>Document Parser</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Select Parser</label>
                    <Select
                      value={selectedParser}
                      onChange={(e) => setSelectedParser(e.target.value)}
                      options={availableParsers.map(p => ({ value: p.id, label: `${p.name} - ${p.description}` }))}
                    />
                  </div>
                  
                  <UploadArea onFile={doUpload} disabled={uploading} />
                  
                  {uploading && (
                    <ProgressBar 
                      value={uploadProgress} 
                      label="Upload Progress" 
                      variant="default"
                    />
                  )}
                  
                  <div className="flex gap-3 items-center">
                    <input
                      className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 flex-1"
                      placeholder="Document Name"
                      value={documentName}
                      onChange={e => setDocumentName(e.target.value)}
                    />
                  </div>
                  
                  <div className="text-sm space-y-1">
                    {uploadJob && (
                      <div className="flex items-center gap-2">
                        <span>Upload</span>
                        <Badge color={uploadJob.status === 'completed' ? 'green' : uploadJob.status === 'failed' ? 'red' : 'blue'}>
                          {uploadJob.status}
                        </Badge>
                      </div>
                    )}
                  </div>
                  
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 h-48 overflow-auto text-sm">
                    <div className="font-medium mb-2">Parser Logs</div>
                    {ingestLogs.length === 0 ? (
                      <div className="text-gray-500 dark:text-gray-400">No logs yet...</div>
                    ) : (
                      ingestLogs.map((l, i) => (
                        <div key={i} className={`mb-1 ${l.level === 'error' ? 'text-red-600' : 'text-gray-700 dark:text-gray-300'}`}>
                          <span className="text-gray-500 dark:text-gray-400 text-xs">[{new Date(l.ts).toLocaleTimeString()}]</span> {l.message}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="indexing">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Create New Index</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Index Name</label>
                        <input
                          className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 w-full"
                          placeholder="Enter index name"
                          value={indexName}
                          onChange={e => setIndexName(e.target.value)}
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-2">Select Parser</label>
                        <Select
                          value={selectedParserForIndex}
                          onChange={(e) => setSelectedParserForIndex(e.target.value)}
                          options={availableParsers.map(p => ({ value: p.id, label: p.name }))}
                        />
                      </div>
                    </div>
                    
                    <Button 
                      onClick={createIndex}
                      disabled={!indexName || !selectedParserForIndex}
                    >
                      Create Index
                    </Button>
                    
                    {indexingProgress > 0 && (
                      <ProgressBar 
                        value={indexingProgress} 
                        label="Index Creation Progress" 
                        variant="default"
                      />
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Add Document to Index</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Select Index</label>
                      <Select
                        value={selectedIndex}
                        onChange={(e) => setSelectedIndex(e.target.value)}
                        options={[
                          { value: '', label: 'Select an index...' },
                          ...indices.map(idx => ({ value: idx.id, label: `${idx.name} (${idx.document_count} docs)` }))
                        ]}
                      />
                    </div>
                    
                    <Button 
                      onClick={ingestToIndex}
                      disabled={!fileId || !documentName || !selectedIndex}
                    >
                      Add Document to Index
                    </Button>
                    
                    {indexingJob && indexingJob.type === 'ingest' && (
                      <div className="space-y-2">
                        <ProgressBar 
                          value={indexingJob.progress || 0} 
                          label="Indexing Progress" 
                          variant={indexingJob.status === 'completed' ? 'success' : indexingJob.status === 'failed' ? 'error' : 'default'}
                        />
                        <div className="flex items-center gap-2 text-sm">
                          <span>Indexing</span>
                          <Badge color={indexingJob.status === 'completed' ? 'green' : indexingJob.status === 'failed' ? 'red' : 'blue'}>
                            {indexingJob.status}
                          </Badge>
                          {indexingJob.indexing_status && (
                            <>
                              <span>·</span>
                              <Badge color={indexingJob.indexing_status === 'completed' ? 'green' : indexingJob.indexing_status === 'failed' ? 'red' : 'yellow'}>
                                {indexingJob.indexing_status}
                              </Badge>
                            </>
                          )}
                          {typeof indexingJob.num_chunks === 'number' && indexingJob.status === 'completed' && (
                            <span className="text-gray-600 dark:text-gray-400">
                              · Chunks: <span className="font-medium">{indexingJob.num_chunks}</span>
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Existing Index</CardTitle>
                </CardHeader>
                <CardContent>
                  {indices.length === 0 ? (
                    <div className="text-gray-500 dark:text-gray-400 text-center py-8">
                      No index created yet. Create your first index above.
                    </div>
                  ) : (
                    <div className="grid gap-4">
                      {indices.map((index) => (
                        <div key={index.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                          <div>
                            <h4 className="font-medium">{index.name}</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {index.document_count} documents · Created {new Date(index.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge color="blue">{index.parser_id}</Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="query">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Query Knowledge Base</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium mb-2">Select Index</label>
                      <Select
                        value={selectedIndex}
                        onChange={(e) => setSelectedIndex(e.target.value)}
                        options={[
                          { value: '', label: 'Select an index...' },
                          ...indices.map(idx => ({ value: idx.id, label: `${idx.name} (${idx.document_count} docs)` }))
                        ]}
                      />
                    </div>
                    
                    <div className="flex gap-3">
                      <input
                        className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 flex-1"
                        placeholder="Your question"
                        value={question}
                        onChange={e => setQuestion(e.target.value)}
                        onKeyPress={e => e.key === 'Enter' && ask()}
                      />
                      <Button onClick={ask} disabled={!question || !selectedIndex}>Ask</Button>
                    </div>
                    
                    {answer && (
                      <div className="space-y-4">
                        <div>
                          <div className="font-semibold mb-2">Answer</div>
                          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 whitespace-pre-wrap">
                            {answer}
                          </div>
                        </div>
                        
                        <div>
                          <div className="font-semibold mb-2">Retrieved Contexts</div>
                          <div className="grid md:grid-cols-2 gap-4">
                            {contexts.map((c) => (
                              <div key={c.chunk_id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                                <div className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                                  Score: {c.score.toFixed(4)} | {JSON.stringify(c.metadata)}
                                </div>
                                <div className="text-sm whitespace-pre-wrap">{c.text}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {integrationCode && (
                <Card>
                  <CardHeader>
                    <CardTitle>Integration Code & API Usage</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">API Endpoint</label>
                        <div className="bg-gray-100 dark:bg-gray-800 rounded px-3 py-2 text-sm font-mono">
                          {apiEndpoint}
                        </div>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium mb-2">Integration Code Examples</label>
                        <div className="bg-gray-900 text-gray-100 rounded-lg p-4 text-sm font-mono whitespace-pre-wrap overflow-x-auto">
                          {integrationCode}
                        </div>
                      </div>
                      
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        <p><strong>Note:</strong> Adjust parameters as needed for your integration.</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}