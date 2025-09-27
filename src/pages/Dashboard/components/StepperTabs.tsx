// src/pages/Dashboard/components/StepperTabs.tsx
import React from "react";

type Props = {
    current: "parsing" | "indexing";
    onChange: (v: "parsing" | "indexing") => void;
};

const StepperTabs: React.FC<Props> = ({ current, onChange }) => {
    const isParsing = current === "parsing";
    return (
        <div className="flex items-center gap-3">
            <button
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition-colors ${isParsing ? "bg-indigo-600 text-white ring-indigo-600" : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50"
                    }`}
                onClick={() => onChange("parsing")}
            >
                <span className="w-5 h-5 rounded-full bg-white/20 ring-1 ring-white/30 flex items-center justify-center">1</span>
                Parsing
            </button>
            <button
                className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition-colors ${!isParsing ? "bg-indigo-600 text-white ring-indigo-600" : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50"
                    }`}
                onClick={() => onChange("indexing")}
            >
                <span className="w-5 h-5 rounded-full bg-white/20 ring-1 ring-white/30 flex items-center justify-center">2</span>
                Indexing
            </button>
        </div>
    );
};

export default StepperTabs;
