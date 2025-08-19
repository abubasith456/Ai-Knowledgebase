import React, { useEffect, useState } from 'react'
import { http } from '../lib/http'
import { Card, CardContent, CardHeader, CardTitle } from './Card'
import { Button } from './Button'
import { Badge } from './Badge'

type ProjectSummary = { projectId: string, name: string }
type JobSummary = { jobId: string, filename: string, status: string }
type IndexSummary = { indexId: string, name: string }
type QueryAnswer = { text: string, source?: string }

type TabKey = 'projects' | 'parser' | 'index' | 'query'

function IconProjects({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 7h18"/>
      <path d="M10 3h4v4h-4z"/>
      <rect x="3" y="7" width="18" height="14" rx="2"/>
    </svg>
  )
}

function IconParser({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <path d="M14 2v6h6"/>
      <path d="M16 13H8"/>
      <path d="M16 17H8"/>
    </svg>
  )
}

function IconIndex({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <ellipse cx="12" cy="5" rx="9" ry="3"/>
      <path d="M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5"/>
      <path d="M3 12c0 1.7 4 3 9 3s9-1.3 9-3"/>
    </svg>
  )
}

function IconQuery({ className = 'w-5 h-5' }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <path d="M21 21l-4.3-4.3"/>
      <path d="M9 8a3 3 0 0 1 6 0c0 2-3 2-3 4"/>
      <path d="M12 17h.01"/>
    </svg>
  )
}

export default function V1Manager() {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<string>('')

  const [jobs, setJobs] = useState<JobSummary[]>([])
  const [selectedJob, setSelectedJob] = useState<string>('')

  const [indexes, setIndexes] = useState<IndexSummary[]>([])
  const [selectedIndex, setSelectedIndex] = useState<string>('')
  const [newIndexName, setNewIndexName] = useState<string>('')

  const [query, setQuery] = useState<string>('')
  const [answers, setAnswers] = useState<QueryAnswer[]>([])

  const [quickTestFile, setQuickTestFile] = useState<File | null>(null)
  const [quickTestQuery, setQuickTestQuery] = useState<string>('What is the policy?')
  const [quickTestAnswers, setQuickTestAnswers] = useState<QueryAnswer[]>([])

  const [activeTab, setActiveTab] = useState<TabKey>('projects')
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false)

  async function loadProjects() {
    const res = await http.get('/v1/projects')
    setProjects(res.data || [])
  }

  async function createProject(name: string, description: string) {
    if (!name.trim()) return
    const res = await http.post('/v1/projects', { name, description })
    await loadProjects()
    setSelectedProject(res.data.projectId)
  }

  async function deleteProject(projectId: string) {
    await http.delete(`/v1/projects/${projectId}`)
    if (selectedProject === projectId) {
      setSelectedProject('')
      setJobs([])
      setIndexes([])
      setSelectedJob('')
      setSelectedIndex('')
      setAnswers([])
    }
    await loadProjects()
  }

  async function loadJobs(projectId: string) {
    if (!projectId) return
    const res = await http.get(`/v1/projects/${projectId}/jobs`)
    setJobs(res.data || [])
  }

  async function uploadFile(file: File) {
    if (!selectedProject) return
    const form = new FormData()
    form.append('file', file)
    await http.post(`/v1/projects/${selectedProject}/jobs`, form, { headers: { 'Content-Type': 'multipart/form-data' } })
    await loadJobs(selectedProject)
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

  async function parseJob() {
    if (!selectedProject || !selectedJob) return
    await http.post(`/v1/projects/${selectedProject}/jobs/${selectedJob}/parse`)
    await loadJobs(selectedProject)
  }

  async function ingest() {
    if (!selectedProject || !selectedIndex || !selectedJob) return
    await http.post(`/v1/projects/${selectedProject}/indexes/${selectedIndex}/ingest`, { jobId: selectedJob })
    await loadJobs(selectedProject)
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

  useEffect(() => { loadProjects() }, [])

  useEffect(() => {
    if (selectedProject) {
      loadJobs(selectedProject)
      loadIndexes(selectedProject)
    }
  }, [selectedProject])

  function SidebarItem({ tab, label, icon }: { tab: TabKey, label: string, icon: React.ReactNode }) {
    const isActive = activeTab === tab
    return (
      <button
        className={`flex items-center gap-3 w-full px-3 py-2 rounded-md transition-colors ${isActive ? 'bg-indigo-600 text-white' : 'text-gray-700 dark:text-gray-200 hover:bg-indigo-100 dark:hover:bg-gray-800'}`}
        onClick={() => setActiveTab(tab)}
      >
        {icon}
        {!sidebarCollapsed && <span className="text-sm font-medium">{label}</span>}
      </button>
    )
  }

  return (
    <div className="flex gap-4">
      {/* Sidebar */}
      <aside className={`${sidebarCollapsed ? 'w-16' : 'w-64'} transition-all duration-200 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-lg p-3 h-[calc(100vh-8rem)] sticky top-6`}> 
        <div className="flex items-center justify-between mb-4">
          {!sidebarCollapsed && <div className="text-sm font-semibold text-gray-700 dark:text-gray-200">Navigation</div>}
          <button
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-600 dark:text-gray-300"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            title={sidebarCollapsed ? 'Expand' : 'Collapse'}
          >
            {/* hybrid toggle icon */}
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {sidebarCollapsed ? (
                <path d="M9 18l6-6-6-6"/>
              ) : (
                <path d="M15 18l-6-6 6-6"/>
              )}
            </svg>
          </button>
        </div>

        <div className="space-y-2">
          <SidebarItem tab="projects" label="Projects" icon={<IconProjects />} />
          <SidebarItem tab="parser" label="Parser" icon={<IconParser />} />
          <SidebarItem tab="index" label="Index" icon={<IconIndex />} />
          <SidebarItem tab="query" label="Query" icon={<IconQuery />} />
        </div>
      </aside>

      {/* Content */}
      <div className="flex-1 space-y-6">
        {activeTab === 'projects' && (
          <Card>
            <CardHeader>
              <CardTitle>Projects</CardTitle>
            </CardHeader>
            <CardContent>
              <ProjectsPanel
                projects={projects}
                selectedProject={selectedProject}
                onSelect={setSelectedProject}
                onCreate={createProject}
                onDelete={deleteProject}
              />
            </CardContent>
          </Card>
        )}

        {activeTab === 'parser' && (
          <ParserPanel
            selectedProject={selectedProject}
            jobs={jobs}
            selectedJob={selectedJob}
            onUpload={uploadFile}
            onSelectJob={setSelectedJob}
            onParse={parseJob}
          />
        )}

        {activeTab === 'index' && (
          <IndexPanel
            selectedProject={selectedProject}
            indexes={indexes}
            selectedIndex={selectedIndex}
            newIndexName={newIndexName}
            setNewIndexName={setNewIndexName}
            onCreateIndex={createIndex}
            onDeleteIndex={deleteIndex}
            onSelectIndex={setSelectedIndex}
            onIngest={ingest}
            selectedJob={selectedJob}
          />
        )}

        {activeTab === 'query' && (
          <QueryPanel
            selectedProject={selectedProject}
            selectedIndex={selectedIndex}
            query={query}
            setQuery={setQuery}
            answers={answers}
            onAsk={doQuery}
            quickTestFile={quickTestFile}
            setQuickTestFile={setQuickTestFile}
            quickTestQuery={quickTestQuery}
            setQuickTestQuery={setQuickTestQuery}
            quickTestAnswers={quickTestAnswers}
            onQuickTest={doQuickTest}
          />
        )}
      </div>
    </div>
  )
}

function ProjectsPanel({ projects, selectedProject, onSelect, onCreate, onDelete } : {
  projects: ProjectSummary[]
  selectedProject: string
  onSelect: (id: string) => void
  onCreate: (name: string, description: string) => Promise<void>
  onDelete: (id: string) => Promise<void>
}) {
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')

  return (
    <div className="grid md:grid-cols-2 gap-4">
      <div className="space-y-3">
        <div className="flex gap-2">
          <input className="border rounded px-3 py-2 flex-1" placeholder="Project name" value={name} onChange={e => setName(e.target.value)} />
          <input className="border rounded px-3 py-2 flex-1" placeholder="Description (optional)" value={desc} onChange={e => setDesc(e.target.value)} />
          <Button onClick={() => onCreate(name, desc)} disabled={!name}>Create</Button>
        </div>
        <div className="text-sm text-gray-600 dark:text-gray-400">Select a project to drive the Parser, Index, and Query tabs.</div>
      </div>
      <div>
        <select className="border rounded px-3 py-2 w-full" value={selectedProject} onChange={e => onSelect(e.target.value)}>
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
                <Button onClick={() => onDelete(p.projectId)}>Delete</Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function ParserPanel({ selectedProject, jobs, selectedJob, onUpload, onSelectJob, onParse } : {
  selectedProject: string
  jobs: JobSummary[]
  selectedJob: string
  onUpload: (file: File) => Promise<void>
  onSelectJob: (id: string) => void
  onParse: () => Promise<void>
}) {
  if (!selectedProject) return <div className="text-gray-500">Select a project first</div>
  return (
    <Card>
      <CardHeader>
        <CardTitle>Parser</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <input type="file" onChange={e => e.target.files && onUpload(e.target.files[0])} />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Select Job</label>
            <select className="border rounded px-3 py-2 w-full" value={selectedJob} onChange={e => onSelectJob(e.target.value)}>
              <option value="">Select a job...</option>
              {jobs.map(j => (
                <option key={j.jobId} value={j.jobId}>{j.filename} ({j.status})</option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            <Button onClick={onParse} disabled={!selectedJob}>Parse Job</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function IndexPanel({ selectedProject, indexes, selectedIndex, newIndexName, setNewIndexName, onCreateIndex, onDeleteIndex, onSelectIndex, onIngest, selectedJob } : {
  selectedProject: string
  indexes: IndexSummary[]
  selectedIndex: string
  newIndexName: string
  setNewIndexName: (v: string) => void
  onCreateIndex: () => Promise<void>
  onDeleteIndex: (id: string) => Promise<void>
  onSelectIndex: (id: string) => void
  onIngest: () => Promise<void>
  selectedJob: string
}) {
  if (!selectedProject) return <div className="text-gray-500">Select a project first</div>
  return (
    <Card>
      <CardHeader>
        <CardTitle>Index</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="space-y-3">
            <div className="flex gap-2">
              <input className="border rounded px-3 py-2 flex-1" placeholder="New index name" value={newIndexName} onChange={e => setNewIndexName(e.target.value)} />
              <Button onClick={onCreateIndex} disabled={!newIndexName}>Create Index</Button>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Select Index</label>
              <select className="border rounded px-3 py-2 w-full" value={selectedIndex} onChange={e => onSelectIndex(e.target.value)}>
                <option value="">Select an index...</option>
                {indexes.map(ix => (
                  <option key={ix.indexId} value={ix.indexId}>{ix.name}</option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <Button onClick={() => selectedIndex && onDeleteIndex(selectedIndex)} disabled={!selectedIndex}>Delete Index</Button>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex gap-2">
              <Button onClick={onIngest} disabled={!selectedJob || !selectedIndex}>Ingest Selected Job</Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function QueryPanel({ selectedProject, selectedIndex, query, setQuery, answers, onAsk, quickTestFile, setQuickTestFile, quickTestQuery, setQuickTestQuery, quickTestAnswers, onQuickTest } : {
  selectedProject: string
  selectedIndex: string
  query: string
  setQuery: (v: string) => void
  answers: QueryAnswer[]
  onAsk: () => Promise<void>
  quickTestFile: File | null
  setQuickTestFile: (f: File | null) => void
  quickTestQuery: string
  setQuickTestQuery: (v: string) => void
  quickTestAnswers: QueryAnswer[]
  onQuickTest: () => Promise<void>
}) {
  return (
    <div className="space-y-6">
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
                <Button onClick={onAsk} disabled={!query}>Ask</Button>
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
              <Button onClick={onQuickTest} disabled={!quickTestFile}>Run</Button>
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

