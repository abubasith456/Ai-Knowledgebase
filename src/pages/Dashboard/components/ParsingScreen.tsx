// src/pages/Dashboard/components/ParsingScreen.tsx
import React, { useEffect } from "react";
import type { DocumentItem } from "../types";
import SectionHeader from "./SectionHeader";
import StatusBadge from "./StatusBadge";

type Props = {
    docs: DocumentItem[];
    setDocs: (updater: (d: DocumentItem[]) => DocumentItem[]) => void;
    onUpload: (files: FileList | null) => void;
    onProceedToIndexing: () => void;
};

const ParsingScreen: React.FC<Props> = ({ docs, setDocs, onUpload, onProceedToIndexing }) => {
    // Sequential parser simulator: always keep one "parsing", rest "pending"
    useEffect(() => {
        const hasParsing = docs.some((d) => d.status === "parsing");
        if (!hasParsing) {
            const nextPending = docs.find((d) => d.status === "pending");
            if (nextPending) {
                setDocs((prev) =>
                    prev.map((d) => (d.id === nextPending.id ? { ...d, status: "parsing" } : d))
                );
            }
        }
    }, [docs, setDocs]);

    // Auto-complete "parsing" after a delay, then next pending becomes parsing
    useEffect(() => {
        const current = docs.find((d) => d.status === "parsing");
        if (!current) return;
        const t = setTimeout(() => {
            setDocs((prev) =>
                prev.map((d) => (d.id === current.id ? { ...d, status: "completed" } : d))
            );
        }, 1200);
        return () => clearTimeout(t);
    }, [docs, setDocs]);

    return (
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
            <div className="flex items-center justify-between">
                <SectionHeader title="Parsing" subtitle="Upload files. They parse one-by-one: first is parsing, others pending." />
                <button
                    onClick={onProceedToIndexing}
                    className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500"
                >
                    Go to Indexing
                </button>
            </div>

            <div className="mt-4">
                <label
                    htmlFor="file"
                    className="flex items-center justify-center rounded-lg border-2 border-dashed border-slate-300 p-8 text-sm text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                    <span>Drag & drop files here or click to browse</span>
                    <input id="file" name="file" type="file" multiple className="sr-only" onChange={(e) => onUpload(e.target.files)} />
                </label>
                <p className="mt-2 text-xs text-slate-500">PDF, DOCX, MD, TXT — max 25MB each.</p>
            </div>

            <ul className="mt-6 divide-y divide-slate-200">
                {docs.map((d) => (
                    <li key={d.id} className="px-2 py-3 flex items-center justify-between">
                        <div className="min-w-0">
                            <div className="text-sm text-slate-900 truncate">{d.filename}</div>
                            <div className="text-xs text-slate-500">{d.uploadedAt}</div>
                        </div>
                        <StatusBadge kind={d.status === "completed" ? "completed" : d.status === "parsing" ? "parsing" : "idle"} />
                    </li>
                ))}
                {docs.length === 0 && (
                    <li className="px-2 py-10 text-center text-sm text-slate-500">No files yet. Upload to start parsing.</li>
                )}
            </ul>
        </section>
    );
};

export default ParsingScreen;
