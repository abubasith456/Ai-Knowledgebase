import React, { useState, useEffect } from 'react'
import { http } from './lib/http'
import { Button } from './components/Button'
import { Card, CardContent, CardHeader, CardTitle } from './components/Card'
import { Badge } from './components/Badge'
import { UploadArea } from './components/UploadArea'
import { ProgressBar } from './components/ProgressBar'
import { ThemeToggle } from './components/ThemeToggle'
import { Tabs, TabsList, TabsTrigger, TabsContent } from './components/Tabs'

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
  job_name?: string
}

type Index = {
  id: string
  name: string
  created_at: string
  document_count: number
  parser_id: string
}

type DocumentInfo = {
  id: string
  name: string
  created_at: string
  num_chunks: number
  index_id: string
}

type ChunkMode = 'auto' | 'manual'

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
  const [activeTab, setActiveTab] = useState('upload')

  // Upload & Process tab state
  const [uploading, setUploading] = useState<boolean>(false)
  const [uploadProgress, setUploadProgress] = useState<number>(0)
  const [ingestLogs, setIngestLogs] = useState<IngestLog[]>([])
  const [fileId, setFileId] = useState<string>('')
  const [documentName, setDocumentName] = useState<string>('')
  const [uploadJob, setUploadJob] = useState<JobInfo | null>(null)
  const [processingJob, setProcessingJob] = useState<JobInfo | null>(null)
  
  // Index creation
  const [indexName, setIndexName] = useState<string>('')
  const [creatingIndex, setCreatingIndex] = useState<boolean>(false)
  
  // Chunking settings
  const [chunkMode, setChunkMode] = useState<ChunkMode>('auto')
  const [chunkSize, setChunkSize] = useState<number>(1000)
  const [chunkOverlap, setChunkOverlap] = useState<number>(200)
  
  // Index selection
  const [selectedIndex, setSelectedIndex] = useState<string>('')
  const [indices, setIndices] = useState<Index[]>([])
  const [indexDocuments, setIndexDocuments] = useState<DocumentInfo[]>([])
  const [documentNameExists, setDocumentNameExists] = useState<boolean>(false)

  // Query tab state
  const [question, setQuestion] = useState<string>('')
  const [answer, setAnswer] = useState<string>('')
  const [contexts, setContexts] = useState<RetrievedContext[]>([])
  const [queryIndex, setQueryIndex] = useState<string>('')
  const [topK, setTopK] = useState<number>(5)
  const [integrationCode, setIntegrationCode] = useState<string>('')
  const [apiEndpoint, setApiEndpoint] = useState<string>('')

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

  // Load indices
  async function loadIndices() {
    try {
      const res = await http.get('/index')
      setIndices(res.data || [])
    } catch (e: any) {
      console.error('Failed to load indices:', e)
    }
  }

  // Load documents in an index
  async function loadIndexDocuments(indexId: string) {
    try {
      const res = await http.get(`/index/${indexId}/documents`)
      setIndexDocuments(res.data || [])
    } catch (e: any) {
      console.error('Failed to load index documents:', e)
      setIndexDocuments([])
    }
  }

  // Check if document name exists
  async function checkDocumentName(indexId: string, docName: string) {
    if (!indexId || !docName) {
      setDocumentNameExists(false)
      return
    }
    try {
      const res = await http.get(`/check-document-name/${indexId}/${encodeURIComponent(docName)}`)
      setDocumentNameExists(res.data.exists)
    } catch (e: any) {
      console.error('Failed to check document name:', e)
      setDocumentNameExists(false)
    }
  }

  useEffect(() => {
    loadIndices()
  }, [])

  // Check document name when it changes
  useEffect(() => {
    if (selectedIndex && documentName) {
      checkDocumentName(selectedIndex, documentName)
    } else {
      setDocumentNameExists(false)
    }
  }, [selectedIndex, documentName])

  // Load documents when index changes
  useEffect(() => {
    if (selectedIndex) {
      loadIndexDocuments(selectedIndex)
    } else {
      setIndexDocuments([])
    }
  }, [selectedIndex])

  // Upload functionality
  async function doUpload(f: File) {
    setUploading(true)
    setUploadProgress(0)
    try {
      const form = new FormData()
      form.append('file', f)
      
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
      // Automatically set document name from filename
      if (res.data.document_name) {
        setDocumentName(res.data.document_name)
      }
      setUploadProgress(100)
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'info', 
        message: `File uploaded successfully: ${res.data.document_name || f.name}` 
      }])
      
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { 
          ts: new Date().toISOString(), 
          level: 'info', 
          message: `Upload job started: ${res.data.job_id}` 
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

  // Process document (parse and index)
  async function processDocument() {
    if (!fileId || !documentName || !selectedIndex) return
    
    if (documentNameExists) {
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'error', 
        message: `Document name "${documentName}" already exists in this index. Please choose a different name.` 
      }])
      return
    }
    
    setIngestLogs(prev => [...prev, { 
      ts: new Date().toISOString(), 
      level: 'info', 
      message: 'Starting document processing...' 
    }])
    
    try {
      const payload: any = {
        file_id: fileId,
        document_name: documentName,
        index_id: selectedIndex,
        chunk_mode: chunkMode
      }
      
      if (chunkMode === 'manual') {
        payload.chunk_size = chunkSize
        payload.chunk_overlap = chunkOverlap
      }
      
      const res = await http.post('/ingest', payload)
      
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { 
          ts: new Date().toISOString(), 
          level: 'info', 
          message: `Processing job started: ${res.data.job_id}` 
        }])
        startPolling(res.data.job_id, setProcessingJob)
      }
    } catch (e: any) {
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'error', 
        message: `Processing failed: ${e?.message}` 
      }])
    }
  }

  // Create index
  async function createIndex() {
    if (!indexName) return
    
    setCreatingIndex(true)
    try {
      const res = await http.post('/index', { 
        name: indexName
      })
      
      if (res.data.job_id) {
        setIngestLogs(prev => [...prev, { 
          ts: new Date().toISOString(), 
          level: 'info', 
          message: `Index creation job started: ${res.data.job_id}` 
        }])
        startPolling(res.data.job_id, setProcessingJob)
      }
      
      // Refresh index list
      loadIndices()
      setIndexName('') // Clear the input
    } catch (e: any) {
      setIngestLogs(prev => [...prev, { 
        ts: new Date().toISOString(), 
        level: 'error', 
        message: `Index creation failed: ${e?.message}` 
      }])
    } finally {
      setCreatingIndex(false)
    }
  }

  // Query functionality
  async function ask() {
    if (!question || !queryIndex) return
    try {
      const res = await http.post('/query', { 
        question, 
        top_k: topK,
        index_id: queryIndex 
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
    "top_k": ${topK},
    "index_id": "${queryIndex}"
  }'`

    const pythonCode = `import requests

url = "${backendUrl}/query"
headers = {
    "Content-Type": "application/json"
}
data = {
    "question": "${question}",
    "top_k": ${topK},
    "index_id": "${queryIndex}"
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
    top_k: ${topK},
    index_id: '${queryIndex}'
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
        
        if (info.status === 'processing') {
          setTimeout(poll, 1500)
        } else if (info.status === 'completed') {
          setIngestLogs(prev => [...prev, { 
            ts: new Date().toISOString(), 
            level: 'info', 
            message: `${info.type} completed successfully` 
          }])
          if (setter === setProcessingJob) {
            // Refresh documents list after successful processing
            if (selectedIndex) {
              loadIndexDocuments(selectedIndex)
            }
            // Switch to query tab
            setActiveTab('query')
            setQueryIndex(selectedIndex)
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
            <p className="text-gray-600 dark:text-gray-400">Document Knowledge Base with Advanced Chunking</p>
          </div>
          <ThemeToggle isDark={isDark} onToggle={() => setIsDark(!isDark)} />
        </header>

        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            <TabsTrigger value="upload">Upload & Process</TabsTrigger>
            <TabsTrigger value="query">Query</TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Create Index (Optional)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                      <div className="text-sm text-blue-800 dark:text-blue-200">
                        <strong>Index Creation:</strong> Create a new index to organize your documents. You can skip this if you want to use an existing index.
                      </div>
                    </div>
                    
                    <div className="flex gap-3">
                      <input
                        className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 flex-1"
                        placeholder="Enter index name (e.g., Research Papers, Legal Documents)"
                        value={indexName}
                        onChange={e => setIndexName(e.target.value)}
                        onKeyPress={e => e.key === 'Enter' && createIndex()}
                      />
                      <Button 
                        onClick={createIndex}
                        disabled={!indexName || creatingIndex}
                      >
                        {creatingIndex ? 'Creating...' : 'Create Index'}
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Step 1: Upload Document</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <UploadArea onFile={doUpload} disabled={uploading} />
                    
                    {uploading && (
                      <ProgressBar 
                        value={uploadProgress} 
                        label="Upload Progress" 
                        variant="default"
                      />
                    )}
                    
                    {uploadJob && (
                      <div className="flex items-center gap-2 text-sm">
                        <span>{uploadJob.job_name || 'Upload'}</span>
                        <Badge color={uploadJob.status === 'completed' ? 'green' : uploadJob.status === 'failed' ? 'red' : 'blue'}>
                          {uploadJob.status}
                        </Badge>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {fileId && (
                <Card>
                  <CardHeader>
                    <CardTitle>Step 2: Configure Processing</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium mb-2">Document Name</label>
                        <input
                          className={`border rounded px-3 py-2 w-full ${
                            documentNameExists 
                              ? 'border-red-500 bg-red-50 dark:bg-red-900/20' 
                              : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
                          }`}
                          placeholder="Enter document name"
                          value={documentName}
                          onChange={e => setDocumentName(e.target.value)}
                        />
                        {documentNameExists && (
                          <p className="text-red-600 dark:text-red-400 text-sm mt-1">
                            This document name already exists in the selected index
                          </p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">Select Index</label>
                        <select
                          className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 w-full"
                          value={selectedIndex}
                          onChange={(e) => setSelectedIndex(e.target.value)}
                        >
                          <option value="">Select an index...</option>
                          {indices.map(idx => (
                            <option key={idx.id} value={idx.id}>
                              {idx.name} ({idx.document_count} docs)
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label className="block text-sm font-medium mb-2">Chunking Mode</label>
                        <div className="space-y-2">
                          <label className="flex items-center">
                            <input
                              type="radio"
                              value="auto"
                              checked={chunkMode === 'auto'}
                              onChange={(e) => setChunkMode(e.target.value as ChunkMode)}
                              className="mr-2"
                            />
                            <span>Auto - Optimized hybrid chunking</span>
                          </label>
                          <label className="flex items-center">
                            <input
                              type="radio"
                              value="manual"
                              checked={chunkMode === 'manual'}
                              onChange={(e) => setChunkMode(e.target.value as ChunkMode)}
                              className="mr-2"
                            />
                            <span>Manual - Custom chunk size and overlap</span>
                          </label>
                        </div>
                      </div>

                      {chunkMode === 'manual' && (
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium mb-2">Chunk Size (tokens)</label>
                            <input
                              type="number"
                              min="100"
                              max="8000"
                              value={chunkSize}
                              onChange={(e) => setChunkSize(parseInt(e.target.value) || 1000)}
                              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 w-full"
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium mb-2">Chunk Overlap (tokens)</label>
                            <input
                              type="number"
                              min="0"
                              max="2000"
                              value={chunkOverlap}
                              onChange={(e) => setChunkOverlap(parseInt(e.target.value) || 200)}
                              className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 w-full"
                            />
                          </div>
                        </div>
                      )}

                      <Button 
                        onClick={processDocument}
                        disabled={!fileId || !documentName || !selectedIndex || documentNameExists}
                        className="w-full"
                      >
                        Process Document
                      </Button>

                      {processingJob && (
                        <div className="space-y-2">
                          <ProgressBar 
                            value={processingJob.progress || 0} 
                            label="Processing Progress" 
                            variant={processingJob.status === 'completed' ? 'success' : processingJob.status === 'failed' ? 'error' : 'default'}
                          />
                          <div className="flex items-center gap-2 text-sm">
                            <span>{processingJob.job_name || 'Processing'}</span>
                            <Badge color={processingJob.status === 'completed' ? 'green' : processingJob.status === 'failed' ? 'red' : 'blue'}>
                              {processingJob.status}
                            </Badge>
                            {processingJob.indexing_status && (
                              <>
                                <span>·</span>
                                <Badge color={processingJob.indexing_status === 'completed' ? 'green' : processingJob.indexing_status === 'failed' ? 'red' : 'yellow'}>
                                  {processingJob.indexing_status}
                                </Badge>
                              </>
                            )}
                            {typeof processingJob.num_chunks === 'number' && processingJob.status === 'completed' && (
                              <span className="text-gray-600 dark:text-gray-400">
                                · Chunks: <span className="font-medium">{processingJob.num_chunks}</span>
                              </span>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}

              {selectedIndex && indexDocuments.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Indexed Documents</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-4">
                      {indexDocuments.map((doc) => (
                        <div key={doc.id} className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg">
                          <div>
                            <h4 className="font-medium">{doc.name}</h4>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {doc.num_chunks} chunks
                            </p>
                          </div>
                          <Badge color="green">Indexed</Badge>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>Processing Logs</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 h-48 overflow-auto text-sm">
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
                      <select
                        className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 w-full"
                        value={queryIndex}
                        onChange={(e) => setQueryIndex(e.target.value)}
                      >
                        <option value="">Select an index...</option>
                        {indices.map(idx => (
                          <option key={idx.id} value={idx.id}>
                            {idx.name} ({idx.document_count} docs)
                          </option>
                        ))}
                      </select>
                    </div>
                    
                    <div className="flex gap-3">
                      <input
                        className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 flex-1"
                        placeholder="Your question"
                        value={question}
                        onChange={e => setQuestion(e.target.value)}
                        onKeyPress={e => e.key === 'Enter' && ask()}
                      />
                      <input
                        type="number"
                        min="1"
                        max="20"
                        value={topK}
                        onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                        className="border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 rounded px-3 py-2 w-20"
                        title="Number of top results to retrieve"
                      />
                      <Button onClick={ask} disabled={!question || !queryIndex}>Ask</Button>
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
                          <div className="font-semibold mb-2">Retrieved Contexts (Top {topK})</div>
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