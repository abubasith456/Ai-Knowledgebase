import React, { useMemo, useState, useEffect } from "react";
import { useApp } from "../../../context/AppContext";
import SectionHeader from "../components/SectionHeader";
import type { QueryResponse } from "../../../services/api/query";

const QueryRoute: React.FC = () => {
    const {
        projects,
        indexes,
        loading,
        queryIndex,
    } = useApp();

    const [projectId, setProjectId] = useState<string>("");
    const [selectedIndexId, setSelectedIndexId] = useState<string>("");
    const [queryText, setQueryText] = useState<string>("");
    const [queryResults, setQueryResults] = useState<QueryResponse | null>(null);
    const [isQuerying, setIsQuerying] = useState<boolean>(false);

    // Set first project as default if available
    useEffect(() => {
        if (projects.length > 0 && !projectId) {
            setProjectId(projects[0].id);
        }
    }, [projects, projectId]);

    // const docs = useMemo(() => documents[projectId] ?? [], [documents, projectId]);
    const projectIndexes = useMemo(() => indexes[projectId] ?? [], [indexes, projectId]);
    const completedIndexes = useMemo(() => projectIndexes.filter(idx => idx.status === "completed"), [projectIndexes]);

    const handleQuery = async () => {
        if (!queryText.trim() || !selectedIndexId) return;

        setIsQuerying(true);
        try {
            const response = await queryIndex(projectId, {
                index_id: selectedIndexId,
                query: queryText.trim(),
                n_results: 5
            });
            setQueryResults(response);
        } catch (error) {
            // Error is handled by context
            setQueryResults(null);
        } finally {
            setIsQuerying(false);
        }
    };

    const clearQuery = () => {
        setQueryText("");
        setQueryResults(null);
    };

    if (projects.length === 0) {
        return (
            <div className="text-center py-12">
                <p className="text-sm text-slate-500">No projects available. Create a project first.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Project selector */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <label className="block text-xs font-medium text-slate-700">Select project</label>
                <select
                    value={projectId}
                    onChange={(e) => {
                        setProjectId(e.target.value);
                        setSelectedIndexId("");
                        setQueryResults(null);
                    }}
                    className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                >
                    {projects.map((p) => (
                        <option key={p.id} value={p.id}>
                            {p.name}
                        </option>
                    ))}
                </select>
            </div>

            {/* Index selector */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <label className="block text-xs font-medium text-slate-700">Select index</label>
                <select
                    value={selectedIndexId}
                    onChange={(e) => setSelectedIndexId(e.target.value)}
                    className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                >
                    <option value="">Choose an index...</option>
                    {completedIndexes.map((idx) => (
                        <option key={idx.id} value={idx.id}>
                            {idx.name} ({idx.document_ids.length} docs)
                        </option>
                    ))}
                </select>
                {completedIndexes.length === 0 && (
                    <p className="mt-2 text-xs text-slate-500">No completed indexes available for this project.</p>
                )}
            </div>

            {/* Query interface */}
            <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                <SectionHeader
                    title="Query your knowledge base"
                    subtitle="Ask questions and get relevant answers from your indexed documents."
                />
                
                <div className="mt-4 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-700">Your question</label>
                        <textarea
                            value={queryText}
                            onChange={(e) => setQueryText(e.target.value)}
                            placeholder="Enter your question here..."
                            rows={3}
                            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30"
                        />
                    </div>
                    
                    <div className="flex gap-3">
                        <button
                            onClick={handleQuery}
                            disabled={!queryText.trim() || !selectedIndexId || isQuerying}
                            className="rounded-md bg-indigo-600 px-4 py-2 text-sm text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isQuerying ? "Searching..." : "Search"}
                        </button>
                        <button
                            onClick={clearQuery}
                            className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 shadow-sm hover:bg-slate-50"
                        >
                            Clear
                        </button>
                    </div>
                </div>
            </div>

            {/* Results */}
            {queryResults && queryResults.results.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                    <SectionHeader
                        title="Search Results"
                        subtitle={`Found ${queryResults.total_results} relevant results`}
                    />
                    
                    <div className="mt-4 space-y-4">
                        {queryResults.results.map((result, index) => (
                            <div key={index} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <p className="text-sm text-slate-900">{result.document}</p>
                                        <div className="mt-2 flex items-center gap-2 text-xs text-slate-500">
                                            <span>Doc: {result.metadata.doc_id}</span>
                                            <span>Chunk: {result.metadata.chunk_index}</span>
                                            <span>Score: {(1 - result.distance).toFixed(3)}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* No results message */}
            {queryResults && queryResults.results.length === 0 && queryText && selectedIndexId && !isQuerying && (
                <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                    <div className="text-center py-8">
                        <p className="text-sm text-slate-500">No results found for your query.</p>
                        <p className="text-xs text-slate-400 mt-1">Try rephrasing your question or selecting a different index.</p>
                    </div>
                </div>
            )}

            {/* Loading indicator */}
            {loading && (
                <div className="text-center py-4">
                    <div className="inline-flex items-center gap-2 text-sm text-slate-500">
                        <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"></div>
                        Loading...
                    </div>
                </div>
            )}
        </div>
    );
};

export default QueryRoute;