import React, { useMemo, useState, useEffect } from "react";
import type { DocumentItem, Project } from "../types";
import ProjectCards from "../components/ProjectCards";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";

const SPLIT_UPLOAD_TYPES = "PDF, DOCX, MD, TXT — max 25MB each.";

const ProjectsRoute: React.FC = () => {
    // Local demo state (replace with API/context when wiring backend)
    const [projects, setProjects] = useState<Project[]>([]);
    const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
    const [docsByProject, setDocsByProject] = useState<Record<string, DocumentItem[]>>({});

    const activeProject = useMemo(
        () => projects.find((p) => p.id === activeProjectId) ?? null,
        [projects, activeProjectId]
    );
    const docs = activeProject ? docsByProject[activeProject.id] ?? [] : [];

    // Create/open project
    const onCreate = (name: string) => {
        const id = `prj_${Date.now()}`;
        const secret = `sec_${Math.random().toString(36).slice(2, 8)}`;
        const p: Project = { id, name, secret, indexingStatus: "idle" };
        setProjects((prev) => [p, ...prev]);
        setDocsByProject((prev) => ({ ...prev, [id]: [] }));
        setActiveProjectId(id);
    };
    const onOpen = (id: string) => setActiveProjectId(id);

    // Upload: add as pending; parsing loop promotes one at a time
    const onUpload = (files: FileList | null) => {
        if (!files || !activeProject) return;
        const additions: DocumentItem[] = Array.from(files).map((f, i) => ({
            id: `doc_${Date.now()}_${i}`,
            filename: f.name,
            status: "pending",
            uploadedAt: new Date().toLocaleString(),
        }));
        setDocsByProject((prev) => ({
            ...prev,
            [activeProject.id]: [...(prev[activeProject.id] ?? []), ...additions],
        }));
    };

    // Promote first pending to parsing if none parsing
    useEffect(() => {
        if (!activeProject) return;
        const list = docsByProject[activeProject.id] ?? [];
        const hasParsing = list.some((d) => d.status === "parsing");
        if (!hasParsing) {
            const next = list.find((d) => d.status === "pending");
            if (next) {
                setDocsByProject((prev) => ({
                    ...prev,
                    [activeProject.id]: (prev[activeProject.id] ?? []).map((d) =>
                        d.id === next.id ? { ...d, status: "parsing" } : d
                    ),
                }));
            }
        }
    }, [activeProject, docsByProject]);

    // Complete current parsing after delay and trigger next
    useEffect(() => {
        if (!activeProject) return;
        const list = docsByProject[activeProject.id] ?? [];
        const current = list.find((d) => d.status === "parsing");
        if (!current) return;
        const t = setTimeout(() => {
            setDocsByProject((prev) => ({
                ...prev,
                [activeProject.id]: (prev[activeProject.id] ?? []).map((d) =>
                    d.id === current.id ? { ...d, status: "completed" } : d
                ),
            }));
        }, 1200);
        return () => clearTimeout(t);
    }, [activeProject, docsByProject]);

    // If no active project, show the card list + Create Project
    if (!activeProject) {
        return <ProjectCards projects={projects} onCreate={onCreate} onOpen={onOpen} />;
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
                    onClick={() => setActiveProjectId(null)}
                    className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 shadow-sm"
                >
                    Back to projects
                </button>
            </div>

            <section className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <SectionHeader
                    title="Parsing"
                    subtitle="Upload files. They parse one-by-one: first is parsing, others pending."
                />
                <div className="mt-4">
                    <label
                        htmlFor="file"
                        className="flex items-center justify-center rounded-lg border-2 border-dashed border-slate-300 p-8 text-sm text-slate-600 hover:bg-slate-50 cursor-pointer"
                    >
                        <span>Drag & drop files here or click to browse</span>
                        <input id="file" name="file" type="file" multiple className="sr-only" onChange={(e) => onUpload(e.target.files)} />
                    </label>
                    <p className="mt-2 text-xs text-slate-500">{SPLIT_UPLOAD_TYPES}</p>
                </div>

                <ul className="mt-6 divide-y divide-slate-200">
                    {docs.map((d) => (
                        <li key={d.id} className="px-2 py-3 flex items-center justify-between">
                            <div className="min-w-0">
                                <div className="text-sm text-slate-900 truncate">{d.filename}</div>
                                <div className="text-xs text-slate-500">{d.uploadedAt}</div>
                            </div>
                            <StatusBadge kind={d.status === "pending" ? "idle" : d.status} />
                        </li>
                    ))}
                    {docs.length === 0 && (
                        <li className="px-2 py-10 text-center text-sm text-slate-500">No files yet. Upload to start parsing.</li>
                    )}
                </ul>
            </section>
        </div>
    );
};

export default ProjectsRoute;
