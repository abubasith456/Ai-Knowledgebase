import React, { useEffect, useState } from 'react'
import { http } from '../lib/http'
import { Card, CardContent, CardHeader, CardTitle } from './Card'
import { Button } from './Button'
import { Badge } from './Badge'

type Project = { projectId: string, name: string, description?: string }
type ProjectSummary = { projectId: string, name: string }
type FileSummary = { fileId: string, filename: string }
type IndexSummary = { indexId: string, name: string }
type QueryAnswer = { text: string, source?: string }

export default function V1Manager() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')
  const [newProjectName, setNewProjectName] = useState<string>('')
  const [newProjectDesc, setNewProjectDesc] = useState<string>('')

  const [files, setFiles] = useState<FileSummary[]>([])
  const [selectedFile, setSelectedFile] = useState<string>('')

  const [indexes, setIndexes] = useState<IndexSummary[]>([])
  const [selectedIndex, setSelectedIndex] = useState<string>('')
  const [newIndexName, setNewIndexName] = useState<string>('')

  const [query, setQuery] = useState<string>('')
  const [answers, setAnswers] = useState<QueryAnswer[]>([])

  const [quickTestFile, setQuickTestFile] = useState<File | null>(null)
  const [quickTestQuery, setQuickTestQuery] = useState<string>('What is the policy?')
  const [quickTestAnswers, setQuickTestAnswers] = useState<QueryAnswer[]>([])

  async function loadProjects() {
    const res = await http.get('/v1/projects')
    setProjects(res.data || [])
  }

  async function createProject() {
    if (!newProjectName.trim()) return
    const res = await http.post('/v1/projects', { name: newProjectName, description: newProjectDesc })
    setNewProjectName('')
    setNewProjectDesc('')
    await loadProjects()
    setSelectedProject(res.data.projectId)
  }

  async function deleteProject(projectId: string) {
    await http.delete(`/v1/projects/${projectId}`)
    if (selectedProject === projectId) {
      setSelectedProject('')
      setFiles([])
      setIndexes([])
      setSelectedFile('')
      setSelectedIndex('')
    }
    await loadProjects()
  }

  async function loadFiles(projectId: string) {
    if (!projectId) return
    const res = await http.get(`/v1/projects/${projectId}/files`)
    setFiles(res.data || [])
  }

  async function uploadFile(file: File) {
    if (!selectedProject) return
    const form = new FormData()
    form.append('file', file)
    await http.post(`/v1/projects/${selectedProject}/files`, form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    await loadFiles(selectedProject)
  }

  async function loadIndexes(projectId: string) {
    if (!projectId) return
    const res = await http.get(`/v1/projects/${projectId}/indexes`)
    setIndexes(res.data || [])
  }

  async function createIndex() {
    if (!selectedProject || !newIndexName.trim()) return
    await http.post(`/v1/projects/${selectedProject}/indexes`, { name: newIndexName })
    setNewIndexName('')
    await loadIndexes(selectedProject)
  }

  async function deleteIndex(idx: string) {
    if (!selectedProject) return
    await http.delete(`/v1/projects/${selectedProject}/indexes/${idx}`)
    await loadIndexes(selectedProject)
    if (selectedIndex === idx) setSelectedIndex('')
  }

  async function ingest() {
    if (!selectedProject || !selectedIndex || !selectedFile) return
    await http.post(`/v1/projects/${selectedProject}/indexes/${selectedIndex}/ingest`, { fileId: selectedFile })
    // no-op; could show a toast
  }

  async function doQuery() {
    if (!selectedProject || !selectedIndex || !query.trim()) return
    const res = await http.post(`/v1/projects/${selectedProject}/indexes/${selectedIndex}/query`, { query, top_k: 3 })
    setAnswers(res.data?.answers || [])
  }

  async function doQuickTest() {
    if (!quickTestFile) return
    const form = new FormData()
    form.append('file', quickTestFile)
    form.append('query', quickTestQuery)
    const res = await http.post('/v1/query/test', form)
    setQuickTestAnswers(res.data?.answers || [])
  }

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (selectedProject) {
      loadFiles(selectedProject)
      loadIndexes(selectedProject)
    }
  }, [selectedProject])

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Projects</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex gap-2">
                <input className="border rounded px-3 py-2 flex-1" placeholder="Project name" value={newProjectName} onChange={e => setNewProjectName(e.target.value)} />
                <input className="border rounded px-3 py-2 flex-1" placeholder="Description (optional)" value={newProjectDesc} onChange={e => setNewProjectDesc(e.target.value)} />
                <Button onClick={createProject} disabled={!newProjectName}>Create</Button>
              </div>
              <div className="text-sm text-gray-600">Select a project to manage files, indexes and queries.</div>
            </div>
            <div>
              <select className="border rounded px-3 py-2 w-full" value={selectedProject} onChange={e => setSelectedProject(e.target.value)}>
                <option value="">Select a project...</option>
                {projects.map(p => (
                  <option key={p.projectId} value={p.projectId}>{p.name}</option>
                ))}
              </select>
              <div className="mt-3 space-y-2">
                {projects.map(p => (
                  <div key={p.projectId} className="flex items-center justify-between border rounded px-3 py-2">
                    <div>{p.name}</div>
                    <div className="flex items-center gap-2">
                      <Badge color={selectedProject === p.projectId ? 'green' : 'blue'}>{selectedProject === p.projectId ? 'Selected' : 'Project'}</Badge>
                      <Button onClick={() => deleteProject(p.projectId)}>Delete</Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Files</CardTitle>
        </CardHeader>
        <CardContent>
          {!selectedProject ? (
            <div className="text-gray-500">Select a project first</div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                <input type="file" onChange={e => e.target.files && uploadFile(e.target.files[0])} />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Select File</label>
                <select className="border rounded px-3 py-2 w-full" value={selectedFile} onChange={e => setSelectedFile(e.target.value)}>
                  <option value="">Select a file...</option>
                  {files.map(f => (
                    <option key={f.fileId} value={f.fileId}>{f.filename}</option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Indexes</CardTitle>
        </CardHeader>
        <CardContent>
          {!selectedProject ? (
            <div className="text-gray-500">Select a project first</div>
          ) : (
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex gap-2">
                  <input className="border rounded px-3 py-2 flex-1" placeholder="New index name" value={newIndexName} onChange={e => setNewIndexName(e.target.value)} />
                  <Button onClick={createIndex} disabled={!newIndexName}>Create Index</Button>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Select Index</label>
                  <select className="border rounded px-3 py-2 w-full" value={selectedIndex} onChange={e => setSelectedIndex(e.target.value)}>
                    <option value="">Select an index...</option>
                    {indexes.map(ix => (
                      <option key={ix.indexId} value={ix.indexId}>{ix.name}</option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <Button onClick={() => selectedIndex && deleteIndex(selectedIndex)} disabled={!selectedIndex}>Delete Index</Button>
                </div>
              </div>
              <div className="space-y-3">
                <div className="flex gap-2">
                  <Button onClick={ingest} disabled={!selectedFile || !selectedIndex}>Ingest Selected File</Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Query</CardTitle>
        </CardHeader>
        <CardContent>
          {!selectedProject || !selectedIndex ? (
            <div className="text-gray-500">Select a project and index</div>
          ) : (
            <div className="space-y-4">
              <div className="flex gap-2">
                <input className="border rounded px-3 py-2 flex-1" placeholder="Your question" value={query} onChange={e => setQuery(e.target.value)} />
                <Button onClick={doQuery} disabled={!query}>Ask</Button>
              </div>
              <div className="space-y-2">
                {answers.length === 0 ? (
                  <div className="text-gray-500">No answers yet</div>
                ) : (
                  answers.map((a, i) => (
                    <div key={i} className="border rounded p-3">
                      <div className="text-xs text-gray-500 mb-1">Source: {a.source || 'N/A'}</div>
                      <div className="whitespace-pre-wrap text-sm">{a.text}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Quick Test</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <input type="file" onChange={e => setQuickTestFile(e.target.files ? e.target.files[0] : null)} />
              <input className="border rounded px-3 py-2 flex-1" placeholder="Query" value={quickTestQuery} onChange={e => setQuickTestQuery(e.target.value)} />
              <Button onClick={doQuickTest} disabled={!quickTestFile}>Run</Button>
            </div>
            <div className="space-y-2">
              {quickTestAnswers.map((a, i) => (
                <div key={i} className="border rounded p-3">
                  <div className="whitespace-pre-wrap text-sm">{a.text}</div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

