import { apiClient } from './client';

// Types matching backend schemas
export interface ProjectCreate {
    name: string;
}

export interface Project {
    id: string;
    name: string;
    secret: string;
}

export interface Document {
    id: string;
    project_id: string;
    filename: string;
    status: string;
}

export interface Index {
    id: string;
    project_id: string;
    name: string;
    status: string;
    document_ids: string[];
}

export interface PaginatedDocs {
    items: Document[];
    total: number;
}

// Projects API
export const projectsApi = {
    // Create a new project
    create: async (data: ProjectCreate): Promise<Project> => {
        const response = await apiClient.post<Project>('/projects', data);
        return response.data;
    },

    // List all projects
    list: async (): Promise<Project[]> => {
        const response = await apiClient.get<Project[]>('/projects');
        return response.data;
    },

    // Get project by ID
    get: async (id: string): Promise<Project> => {
        const response = await apiClient.get<Project>(`/projects/${id}`);
        return response.data;
    },

    // Delete project
    delete: async (id: string): Promise<void> => {
        await apiClient.delete(`/projects/${id}`);
    },
};

// Documents API
export const documentsApi = {
    // Upload a document
    upload: async (projectId: string, file: File): Promise<Document> => {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await apiClient.post<Document>(
            `/projects/${projectId}/documents`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    },

    // List project documents
    list: async (projectId: string, skip: number = 0, limit: number = 100): Promise<PaginatedDocs> => {
        const response = await apiClient.get<PaginatedDocs>(
            `/projects/${projectId}/documents?skip=${skip}&limit=${limit}`
        );
        return response.data;
    },

    // Parse next document
    parseNext: async (projectId: string): Promise<Document | null> => {
        const response = await apiClient.post<Document | null>(
            `/projects/${projectId}/parse-next`
        );
        return response.data;
    },

    // Delete document
    delete: async (projectId: string, documentId: string): Promise<void> => {
        await apiClient.delete(`/projects/${projectId}/documents/${documentId}`);
    },
};

// Indexes API
export const indexesApi = {
    // Create an index
    create: async (projectId: string, data: { name: string; document_ids: string[] }): Promise<Index> => {
        const response = await apiClient.post<Index>(`/projects/${projectId}/indexes`, data);
        return response.data;
    },

    // List project indexes
    list: async (projectId: string): Promise<Index[]> => {
        const response = await apiClient.get<Index[]>(`/projects/${projectId}/indexes`);
        return response.data;
    },

    // Start indexing
    start: async (projectId: string, indexId: string): Promise<Index> => {
        const response = await apiClient.post<Index>(
            `/projects/${projectId}/indexes/${indexId}/start`
        );
        return response.data;
    },

    // Delete index
    delete: async (projectId: string, indexId: string): Promise<void> => {
        await apiClient.delete(`/projects/${projectId}/indexes/${indexId}`);
    },
};