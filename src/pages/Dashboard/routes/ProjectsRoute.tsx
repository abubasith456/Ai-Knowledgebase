import React, { useMemo, useState, useEffect } from "react";
import { useApp } from "../../context/AppContext";
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

    const activeProject = useMemo(
        () => projects.find((p) => p.id === activeProjectId) ?? null,
        [projects, activeProjectId]
    );
    
    const docs = activeProject ? (documents[activeProject.id] ?? []) : [];

    // Load documents when active project changes
    useEffect(() => {
        if (activeProject) {
            loadDocuments(activeProject.id);
        }
    }, [activeProject, loadDocuments]);

    // Auto-parse next document when none is parsing
    useEffect(() => {
        if (!activeProject) return;
        
        const list = documents[activeProject.id] ?? [];
        const hasParsing = list.some((d) => d.status === "parsing");
        
        if (!hasParsing) {
            const next = list.find((d) => d.status === "pending");
            if (next) {
                parseNextDocument(activeProject.id);
            }
        }
    }, [activeProject, documents, parseNextDocument]);

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
                                <StatusBadge status={doc.status} />
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
