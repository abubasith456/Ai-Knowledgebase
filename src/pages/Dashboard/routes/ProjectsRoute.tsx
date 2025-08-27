import React, { useMemo, useState, useEffect, useRef } from "react";
import { useApp } from "../../../context/AppContext";
import ProjectCards from "../components/ProjectCards";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";

const SPLIT_UPLOAD_TYPES = "PDF, DOCX, MD, TXT — max 25MB each.";

const ProjectsRoute: React.FC = () => {
    const {
        projects,
        documents,
        activeProjectId,
        loading,
        createProject,
        setActiveProject,
        deleteProject,
        uploadDocument,
        loadDocuments,
        deleteDocument,
    } = useApp();

    const [newProjectName, setNewProjectName] = useState<string>("");
    const [isCreatingProject, setIsCreatingProject] = useState<boolean>(false);
    const loadedProjectsRef = useRef<Set<string>>(new Set());

    const activeProject = useMemo(
        () => projects.find((p) => p.id === activeProjectId) ?? null,
        [projects, activeProjectId]
    );
    
    const docs = activeProject ? (documents[activeProject.id] ?? []) : [];

    // Load documents when active project changes
    useEffect(() => {
        if (activeProject && !loadedProjectsRef.current.has(activeProject.id)) {
            loadedProjectsRef.current.add(activeProject.id);
            loadDocuments(activeProject.id);
        }
    }, [activeProject, activeProject?.id, loadDocuments]);

    // Auto-poll for document status updates every 5 seconds
    useEffect(() => {
        if (!activeProject) return;

        const interval = setInterval(() => {
            // Only poll if there are documents with pending or parsing status
            const docs = documents[activeProject.id] ?? [];
            const hasActiveDocuments = docs.some(d => d.status === "pending" || d.status === "parsing");
            
            if (hasActiveDocuments) {
                console.log(`🔄 Auto-polling documents for project ${activeProject.id}`);
                loadDocuments(activeProject.id);
            }
        }, 5000); // Poll every 5 seconds

        // Cleanup interval on unmount or when activeProject changes
        return () => {
            clearInterval(interval);
        };
    }, [activeProject, documents, loadDocuments]);



    // Create project
    const onCreate = async (name: string) => {
        if (!name.trim()) return;
        
        setIsCreatingProject(true);
        try {
            await createProject(name.trim());
            setNewProjectName("");
        } catch (error) {
            // Error is handled by context
        } finally {
            setIsCreatingProject(false);
        }
    };

    const onOpen = (id: string) => setActiveProject(id);

    // Upload documents
    const onUpload = async (files: FileList | null) => {
        if (!files || !activeProject) return;
        
        try {
            for (const file of Array.from(files)) {
                await uploadDocument(activeProject.id, file);
            }
        } catch (error) {
            // Error is handled by context
        }
    };

    // If no active project, show the card list + Create Project
    if (!activeProject) {
        return (
            <ProjectCards 
                projects={projects} 
                onCreate={onCreate} 
                onOpen={onOpen}
                onDelete={deleteProject}
                isCreating={isCreatingProject}
                newProjectName={newProjectName}
                setNewProjectName={setNewProjectName}
            />
        );
    }

    // Parsing screen for the active project
    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-base font-semibold text-slate-900">{activeProject.name}</h2>
                    <p className="text-xs text-slate-500">{activeProject.id}</p>
                </div>
                <button
                    onClick={() => setActiveProject(null)}
                    className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 shadow-sm"
                >
                    Back to projects
                </button>
            </div>

            {/* Upload Panel */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                                    <SectionHeader
                        title="Upload Documents"
                        subtitle={SPLIT_UPLOAD_TYPES}
                    />
                <div className="mt-4">
                    <input
                        type="file"
                        multiple
                        accept=".pdf,.docx,.md,.txt"
                        onChange={(e) => onUpload(e.target.files)}
                        className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"
                    />
                </div>
            </div>

            {/* Documents List */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <SectionHeader
                    title="Documents"
                    subtitle={`${docs.length} document${docs.length !== 1 ? 's' : ''} in this project`}
                />
                
                {/* Parsing Queue Status */}
                {docs.length > 0 && (
                    <div className="mt-4 p-3 rounded-lg bg-blue-50 border border-blue-200">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <div className="h-3 w-3 rounded-full bg-blue-500 animate-pulse"></div>
                                <span className="text-sm font-medium text-blue-900">Document Processing Status</span>
                            </div>
                            <div className="text-xs text-blue-700">
                                {docs.filter(d => d.status === "parsing").length} processing • {docs.filter(d => d.status === "pending").length} queued • {docs.filter(d => d.status === "completed").length} completed
                            </div>
                        </div>
                        {/* Real-time status updates */}
                        {docs.filter(d => d.status === "parsing" || d.status === "pending").length > 0 && (
                            <div className="mt-2 text-xs text-blue-600">
                                🔄 Auto-updating every 5 seconds • Documents process automatically on upload
                            </div>
                        )}
                    </div>
                )}
                
                <div className="mt-4 space-y-3">
                    {docs.length === 0 ? (
                        <p className="text-sm text-slate-500 text-center py-8">
                            No documents uploaded yet. Upload some files to get started.
                        </p>
                    ) : (
                        docs.map((doc) => (
                            <div key={doc.id} className={`flex items-center justify-between p-3 rounded-lg border ${
                                doc.status === "parsing" ? "border-blue-200 bg-blue-50" : 
                                doc.status === "pending" ? "border-yellow-200 bg-yellow-50" :
                                doc.status === "completed" ? "border-green-200 bg-green-50" :
                                "border-slate-200 bg-slate-50"
                            }`}>
                                <div className="flex items-center gap-3">
                                    <div className={`h-8 w-8 rounded-md flex items-center justify-center ${
                                        doc.status === "parsing" ? "bg-blue-200" :
                                        doc.status === "pending" ? "bg-yellow-200" :
                                        doc.status === "completed" ? "bg-green-200" :
                                        "bg-slate-200"
                                    }`}>
                                        <span className="text-xs text-slate-600">
                                            {doc.filename.split('.').pop()?.toUpperCase()}
                                        </span>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-slate-900">{doc.filename}</p>
                                        <p className="text-xs text-slate-500">ID: {doc.id}</p>
                                        {doc.status === "parsing" && (
                                            <div className="flex items-center gap-1 mt-1">
                                                <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse"></div>
                                                <span className="text-xs text-blue-600">Processing...</span>
                                            </div>
                                        )}
                                        {doc.status === "pending" && (
                                            <div className="flex items-center gap-1 mt-1">
                                                <div className="h-2 w-2 rounded-full bg-yellow-500"></div>
                                                <span className="text-xs text-yellow-600">Queued for processing</span>
                                            </div>
                                        )}
                                        {doc.status === "completed" && doc.chunk_count && (
                                            <div className="text-xs text-green-600 mt-1">
                                                ✅ {doc.chunk_count} chunks created
                                            </div>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <StatusBadge status={doc.status} />
                                    <button
                                        onClick={() => deleteDocument(activeProject.id, doc.id)}
                                        className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200"
                                        title="Delete document"
                                    >
                                        🗑️
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Loading indicator */}
            {loading && (
                <div className="text-center py-4">
                    <div className="inline-flex items-center gap-2 text-sm text-slate-500">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"></div>
                        Processing...
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProjectsRoute;
