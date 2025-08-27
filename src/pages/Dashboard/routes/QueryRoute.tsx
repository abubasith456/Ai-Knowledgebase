import React, { useMemo, useState } from "react";
import type { DocumentItem, IndexItem, Project } from "../types";
import SectionHeader from "../components/SectionHeader";
import StatusBadge from "../components/StatusBadge";

const QueryRoute: React.FC = () => {
    // Demo sources (replace with context/API)
    const [projects] = useState<Project[]>([
        { id: "prj_demo1", name: "Knowledge Base", secret: "sec_xxxxx", indexingStatus: "idle" },
        { id: "prj_demo2", name: "Marketing Docs", secret: "sec_yyyyy", indexingStatus: "idle" },
    ]);
    const [docsByProject] = useState<Record<string, DocumentItem[]>>({
        prj_demo1: [
            { id: "d1", filename: "kb-intro.pdf", status: "completed", uploadedAt: "2025-08-26 10:30" },
            { id: "d2", filename: "release-notes.md", status: "completed", uploadedAt: "2025-08-26 10:40" },
            { id: "d3", filename: "draft.md", status: "parsing", uploadedAt: "2025-08-26 10:42" },
        ],
        prj_demo2: [{ id: "d4", filename: "q3-roadmap.docx", status: "completed", uploadedAt: "2025-08-26 10:41" }],
    });
    const [indexesByProject] = useState<Record<string, IndexItem[]>>({
        prj_demo1: [
            { id: "idx1", name: "Main Index", status: "completed", documentIds: ["d1", "d2"] },
            { id: "idx2", name: "Draft Index", status: "completed", documentIds: ["d3"] },
        ],
        prj_demo2: [{ id: "idx3", name: "Marketing Index", status: "completed", documentIds: ["d4"] }],
    });

    const [projectId, setProjectId] = useState<string>("prj_demo1");
    const [selectedIndexId, setSelectedIndexId] = useState<string>("");
    const [queryText, setQueryText] = useState<string>("");
    const [queryResults, setQueryResults] = useState<any[]>([]);
    const [isQuerying, setIsQuerying] = useState<boolean>(false);

    const docs = useMemo(() => docsByProject[projectId] ?? [], [docsByProject, projectId]);
    const indexes = useMemo(() => indexesByProject[projectId] ?? [], [indexesByProject, projectId]);
    const completedIndexes = useMemo(() => indexes.filter(idx => idx.status === "completed"), [indexes]);

    const handleQuery = async () => {
        if (!queryText.trim() || !selectedIndexId) return;

        setIsQuerying(true);
        try {
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Mock results
            const mockResults = [
                {
                    document: `This is a sample result for query: "${queryText}". It shows how the search would work with the selected index.`,
                    metadata: { project_id: projectId, doc_id: "d1", chunk_index: 0 },
                    distance: 0.1
                },
                {
                    document: `Another relevant result containing information about "${queryText}". This demonstrates the search functionality.`,
                    metadata: { project_id: projectId, doc_id: "d2", chunk_index: 1 },
                    distance: 0.3
                }
            ];
            
            setQueryResults(mockResults);
        } catch (error) {
            console.error("Query failed:", error);
            setQueryResults([]);
        } finally {
            setIsQuerying(false);
        }
    };

    const clearQuery = () => {
        setQueryText("");
        setQueryResults([]);
    };

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
                        setQueryResults([]);
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
                            {idx.name} ({idx.documentIds.length} docs)
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
            {queryResults.length > 0 && (
                <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                    <SectionHeader
                        title="Search Results"
                        subtitle={`Found ${queryResults.length} relevant results`}
                    />
                    
                    <div className="mt-4 space-y-4">
                        {queryResults.map((result, index) => (
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
            {queryResults.length === 0 && queryText && selectedIndexId && !isQuerying && (
                <div className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
                    <div className="text-center py-8">
                        <p className="text-sm text-slate-500">No results found for your query.</p>
                        <p className="text-xs text-slate-400 mt-1">Try rephrasing your question or selecting a different index.</p>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QueryRoute;