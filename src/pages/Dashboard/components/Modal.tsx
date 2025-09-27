// src/pages/Dashboard/components/Modal.tsx
import React from "react";

type Props = {
    open: boolean;
    onClose: () => void;
    title: string;
    children: React.ReactNode;
    footer?: React.ReactNode;
};

const Modal: React.FC<Props> = ({ open, onClose, title, children, footer }) => {
    if (!open) return null;
    return (
        <div className="fixed inset-0 z-50">
            <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" onClick={onClose} />
            <div className="absolute inset-0 flex items-center justify-center p-4">
                <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white shadow-xl">
                    <div className="px-4 py-3 border-b border-slate-200">
                        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
                    </div>
                    <div className="p-4">{children}</div>
                    {footer && <div className="px-4 py-3 border-t border-slate-200">{footer}</div>}
                </div>
            </div>
        </div>
    );
};

export default Modal;
