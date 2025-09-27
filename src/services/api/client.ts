import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';

// API client configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient: AxiosInstance = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response: AxiosResponse) => response,
    (error) => {
        console.error('API Error:', error);
        if (error.response?.status === 404) {
            throw new Error('Resource not found');
        } else if (error.response?.status >= 500) {
            throw new Error('Server error occurred');
        } else if (error.response?.data?.detail) {
            throw new Error(error.response.data.detail);
        } else {
            throw new Error(error.message || 'An error occurred');
        }
    }
);

// Generic API response wrapper
export interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
}

// API error wrapper
export class ApiError extends Error {
    constructor(
        message: string,
        public status?: number,
        public code?: string
    ) {
        super(message);
        this.name = 'ApiError';
    }
}