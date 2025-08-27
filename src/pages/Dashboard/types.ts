// src/pages/Dashboard/types.ts
export type IndexingStatus = "idle" | "indexing" | "completed";

export type DocStatus = "pending" | "parsing" | "completed";

export type Project = {
    id: string;
    name: string;
    secret: string;
    indexingStatus: IndexingStatus;
};

export type DocumentItem = {
    id: string;
    filename: string;
    status: DocStatus;
    uploadedAt: string;
};

export type IndexItem = {
    id: string;
    name: string;
    status: IndexingStatus; // index-level status
    documentIds: string[];
};
