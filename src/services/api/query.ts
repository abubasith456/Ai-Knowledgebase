import { apiClient } from './client';

export interface QueryRequest {
    index_id: string;
    query: string;
    n_results?: number;
}

export interface QueryResult {
    document: string;
    metadata: Record<string, any>;
    distance: number;
}

export interface QueryResponse {
    query: string;
    results: QueryResult[];
    total_results: number;
}

export const queryApi = {
    // Query an index
    query: async (projectId: string, data: QueryRequest): Promise<QueryResponse> => {
        const response = await apiClient.post<QueryResponse>(`/query?project_id=${projectId}`, data);
        return response.data;
    },
};