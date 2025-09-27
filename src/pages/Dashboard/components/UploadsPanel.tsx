import React, { useState } from "react";
import SectionHeader from "./SectionHeader";

type Props = { onStartIndexing: () => void; onUpload: (files: FileList | null) => void };

const UploadsPanel: React.FC<Props> = ({ onStartIndexing, onUpload }) => {
    const [dragOver, setDragOver] = useState(false);

    return (
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm p-4">
            <SectionHeader
                title="Upload documents"
                subtitle="PDF, DOCX, MD, TXT up to 25MB"
                actions={
                    <button className="rounded-md bg-indigo-600 px-3 py-1.5 text-sm text-white shadow-sm hover:bg-indigo-500" onClick={onStartIndexing}>
                        Start indexing
                    </button>
                }
            />
            <div className="mt-4">
                <label
                    htmlFor="file"
                    onDragOver={(e) => {
                        e.preventDefault();
                        setDragOver(true);
                    }}
                    onDragLeave={() => setDragOver(false)}
                    onDrop={(e) => {
                        e.preventDefault();
                        setDragOver(false);
                        onUpload(e.dataTransfer.files);
                    }}
                    className={`flex items-center justify-center rounded-lg border-2 border-dashed p-8 text-sm transition-colors ${dragOver ? "border-indigo-400 bg-indigo-50/40 text-indigo-700" : "border-slate-300 text-slate-600 hover:bg-slate-50"
                        } cursor-pointer`}
                >
                    <span>Drag & drop files here or click to browse</span>
                    <input id="file" name="file" type="file" multiple className="sr-only" onChange={(e) => onUpload(e.target.files)} />
                </label>
            </div>
        </section>
    );
};

export default UploadsPanel;
