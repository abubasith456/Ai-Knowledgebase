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
        uploadDocument,
        loadDocuments,
        parseNextDocument,
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

    // Auto-parse next document when none is parsing
    useEffect(() => {
        if (!activeProject) return;
        
        const list = documents[activeProject.id] ?? [];
        const hasParsing = list.some((d) => d.status === "parsing");
        const hasPending = list.some((d) => d.status === "pending");
        
        if (!hasParsing && hasPending) {
            const next = list.find((d) => d.status === "pending");
            if (next) {
                parseNextDocument(activeProject.id);
            }
        }
    }, [activeProject, activeProject?.id, parseNextDocument, documents]);

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
                    actions={
                        <button
                            onClick={() => parseNextDocument(activeProject.id)}
                            disabled={!docs.some(d => d.status === "pending")}
                            className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-500 disabled:bg-slate-300 disabled:cursor-not-allowed"
                        >
                            Start Parsing
                        </button>
                    }
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
                                <div className="h-3 w-3 rounded-full bg-blue-500"></div>
                                <span className="text-sm font-medium text-blue-900">Parsing Queue</span>
                            </div>
                            <div className="text-xs text-blue-700">
                                {docs.filter(d => d.status === "parsing").length} parsing • {docs.filter(d => d.status === "pending").length} pending • {docs.filter(d => d.status === "completed").length} completed
                            </div>
                        </div>
                    </div>
                )}
                
                <div className="mt-4 space-y-3">
                    {docs.length === 0 ? (
                        <p className="text-sm text-slate-500 text-center py-8">
                            No documents uploaded yet. Upload some files to get started.
                        </p>
                    ) : (
                        docs.map((doc) => (
                            <div key={doc.id} className="flex items-center justify-between p-3 rounded-lg border border-slate-200 bg-slate-50">
                                <div className="flex items-center gap-3">
                                    <div className="h-8 w-8 rounded-md bg-slate-200 flex items-center justify-center">
                                        <span className="text-xs text-slate-600">
                                            {doc.filename.split('.').pop()?.toUpperCase()}
                                        </span>
                                    </div>
                                    <div>
                                        <p className="text-sm font-medium text-slate-900">{doc.filename}</p>
                                        <p className="text-xs text-slate-500">ID: {doc.id}</p>
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <StatusBadge status={doc.status} />
                                    {doc.status === "pending" && (
                                        <button
                                            onClick={() => parseNextDocument(activeProject.id)}
                                            className="px-2 py-1 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200"
                                        >
                                            Parse Now
                                        </button>
                                    )}
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
