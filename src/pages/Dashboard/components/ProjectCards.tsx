// src/pages/Dashboard/components/ProjectCards.tsx
import React, { useState } from "react";
import type { Project } from "../types";

interface ProjectCardsProps {
    projects: Project[];
    onCreate: (name: string) => void;
    onOpen: (id: string) => void;
    isCreating: boolean;
    newProjectName: string;
    setNewProjectName: (name: string) => void;
}

const ProjectCards: React.FC<ProjectCardsProps> = ({
    projects,
    onCreate,
    onOpen,
    isCreating,
    newProjectName,
    setNewProjectName,
}) => {
    const [showCreateForm, setShowCreateForm] = useState(false);

    const handleCreate = () => {
        if (newProjectName.trim()) {
            onCreate(newProjectName.trim());
            setShowCreateForm(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleCreate();
        } else if (e.key === 'Escape') {
            setShowCreateForm(false);
            setNewProjectName("");
        }
    };

    return (
        <div className="space-y-6">
            {/* Create Project Section */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6">
                <div className="text-center">
                    <h2 className="text-lg font-semibold text-slate-900">Create New Project</h2>
                    <p className="mt-1 text-sm text-slate-500">
                        Start building your knowledge base by creating a new project.
                    </p>
                    
                    {!showCreateForm ? (
                        <button
                            onClick={() => setShowCreateForm(true)}
                            className="mt-4 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                        >
                            Create Project
                        </button>
                    ) : (
                        <div className="mt-4 space-y-3">
                            <input
                                type="text"
                                value={newProjectName}
                                onChange={(e) => setNewProjectName(e.target.value)}
                                onKeyDown={handleKeyPress}
                                placeholder="Enter project name..."
                                className="w-full max-w-md rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                                autoFocus
                            />
                            <div className="flex gap-2 justify-center">
                                <button
                                    onClick={handleCreate}
                                    disabled={!newProjectName.trim() || isCreating}
                                    className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isCreating ? "Creating..." : "Create"}
                                </button>
                                <button
                                    onClick={() => {
                                        setShowCreateForm(false);
                                        setNewProjectName("");
                                    }}
                                    className="rounded-md border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 shadow-sm hover:bg-slate-50"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Existing Projects */}
            {projects.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-6">
                    <h2 className="text-lg font-semibold text-slate-900 mb-4">Your Projects</h2>
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                        {projects.map((project) => (
                            <div
                                key={project.id}
                                className="rounded-lg border border-slate-200 bg-slate-50 p-4 hover:bg-slate-100 transition-colors cursor-pointer"
                                onClick={() => onOpen(project.id)}
                            >
                                <div className="flex items-center gap-3">
                                    <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-indigo-500 to-violet-500 flex items-center justify-center text-white font-semibold text-sm">
                                        {project.name.charAt(0).toUpperCase()}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <h3 className="text-sm font-medium text-slate-900 truncate">
                                            {project.name}
                                        </h3>
                                        <p className="text-xs text-slate-500 truncate">
                                            ID: {project.id}
                                        </p>
                                    </div>
                                </div>
                                <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
                                    <span>Secret: {project.secret}</span>
                                    <span className="text-indigo-600 hover:text-indigo-700">
                                        Open →
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Empty State */}
            {projects.length === 0 && !showCreateForm && (
                <div className="text-center py-12">
                    <div className="mx-auto h-12 w-12 text-slate-400">
                        <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                    </div>
                    <h3 className="mt-2 text-sm font-medium text-slate-900">No projects</h3>
                    <p className="mt-1 text-sm text-slate-500">
                        Get started by creating your first knowledge base project.
                    </p>
                </div>
            )}
        </div>
    );
};

export default ProjectCards;
