import React from "react";

type Props = { title: string; subtitle?: string; actions?: React.ReactNode; className?: string };

const SectionHeader: React.FC<Props> = ({ title, subtitle, actions, className }) => (
    <div className={`flex items-start justify-between ${className ?? ""}`}>
        <div>
            <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
            {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
        </div>
        {actions}
    </div>
);

export default SectionHeader;
