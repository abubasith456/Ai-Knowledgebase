// src/pages/Dashboard/components/ProjectCards.tsx
import React, { useState } from "react";
import type { Project } from "../types";
import Modal from "./Modal";

type Props = {
    projects: Project[];
    onCreate: (name: string) => void;
    onOpen: (projectId: string) => void;
};

const ProjectCards: React.FC<Props> = ({ projects, onCreate, onOpen }) => {
    const [open, setOpen] = useState<boolean>(false);
    const [name, setName] = useState<string>("");

    return (
        <section>
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-base font-semibold text-slate-900">Projects</h2>
                <button
                    onClick={() => setOpen(true)}
                    className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500"
                >
                    Create Project
                </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-6">
                {projects.map((p) => (
                    <button
                        key={p.id}
                        onClick={() => onOpen(p.id)}
                        className="rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm hover:shadow transition-shadow"
                    >
                        <div className="text-sm font-medium text-slate-900">{p.name}</div>
                        <div className="mt-1 text-xs text-slate-500">{p.id}</div>
                        <div className="mt-3 inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600 ring-1 ring-inset ring-slate-200">
                            Secret: {p.secret.slice(0, 6)}•••
                        </div>
                    </button>
                ))}
                {projects.length === 0 && (
                    <div className="rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                        <p className="text-sm text-slate-600">No projects yet. Create one to get started.</p>
                    </div>
                )}
            </div>

            <Modal
                open={open}
                onClose={() => setOpen(false)}
                title="Create project"
                footer={
                    <div className="flex justify-end gap-2">
                        <button
                            onClick={() => setOpen(false)}
                            className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 shadow-sm"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={() => {
                                if (!name.trim()) return;
                                onCreate(name.trim());
                                setName("");
                                setOpen(false);
                            }}
                            className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500"
                        >
                            Create
                        </button>
                    </div>
                }
            >
                <label className="block text-xs font-medium text-slate-700">Project name</label>
                <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Acme Knowledge Base"
                    className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                />
            </Modal>
        </section>
    );
};

export default ProjectCards;
