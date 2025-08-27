import React, { createContext, useContext, useReducer, useEffect, ReactNode, useCallback } from 'react';
import { projectsApi, documentsApi, indexesApi } from '../services/api/projects';
import { queryApi } from '../services/api/query';
import type { Project, Document, Index } from '../services/api/projects';
import type { QueryRequest, QueryResponse } from '../services/api/query';

// State types
interface AppState {
    projects: Project[];
    documents: Record<string, Document[]>;
    indexes: Record<string, Index[]>;
    loading: boolean;
    error: string | null;
    activeProjectId: string | null;
}

// Action types
type AppAction =
    | { type: 'SET_LOADING'; payload: boolean }
    | { type: 'SET_ERROR'; payload: string | null }
    | { type: 'SET_PROJECTS'; payload: Project[] }
    | { type: 'ADD_PROJECT'; payload: Project }
    | { type: 'DELETE_PROJECT'; payload: string }
    | { type: 'SET_DOCUMENTS'; payload: { projectId: string; documents: Document[] } }
    | { type: 'ADD_DOCUMENT'; payload: { projectId: string; document: Document } }
    | { type: 'UPDATE_DOCUMENT'; payload: { projectId: string; documentId: string; updates: Partial<Document> } }
    | { type: 'DELETE_DOCUMENT'; payload: { projectId: string; documentId: string } }
    | { type: 'SET_INDEXES'; payload: { projectId: string; indexes: Index[] } }
    | { type: 'ADD_INDEX'; payload: { projectId: string; index: Index } }
    | { type: 'UPDATE_INDEX'; payload: { projectId: string; indexId: string; updates: Partial<Index> } }
    | { type: 'DELETE_INDEX'; payload: { projectId: string; indexId: string } }
    | { type: 'SET_ACTIVE_PROJECT'; payload: string | null };

// Initial state
const initialState: AppState = {
    projects: [],
    documents: {},
    indexes: {},
    loading: false,
    error: null,
    activeProjectId: null,
};

// Reducer
function appReducer(state: AppState, action: AppAction): AppState {
    switch (action.type) {
        case 'SET_LOADING':
            return { ...state, loading: action.payload };
        case 'SET_ERROR':
            return { ...state, error: action.payload };
        case 'SET_PROJECTS':
            return { ...state, projects: action.payload };
        case 'ADD_PROJECT':
            return { ...state, projects: [action.payload, ...state.projects] };
        case 'DELETE_PROJECT':
            return { 
                ...state, 
                projects: state.projects.filter(p => p.id !== action.payload),
                documents: Object.fromEntries(
                    Object.entries(state.documents).filter(([key]) => key !== action.payload)
                ),
                indexes: Object.fromEntries(
                    Object.entries(state.indexes).filter(([key]) => key !== action.payload)
                )
            };
        case 'SET_DOCUMENTS':
            return {
                ...state,
                documents: { ...state.documents, [action.payload.projectId]: action.payload.documents }
            };
        case 'ADD_DOCUMENT':
            return {
                ...state,
                documents: {
                    ...state.documents,
                    [action.payload.projectId]: [
                        action.payload.document,
                        ...(state.documents[action.payload.projectId] || [])
                    ]
                }
            };
        case 'UPDATE_DOCUMENT':
            return {
                ...state,
                documents: {
                    ...state.documents,
                    [action.payload.projectId]: (state.documents[action.payload.projectId] || []).map(doc =>
                        doc.id === action.payload.documentId ? { ...doc, ...action.payload.updates } : doc
                    )
                }
            };
        case 'DELETE_DOCUMENT':
            return {
                ...state,
                documents: {
                    ...state.documents,
                    [action.payload.projectId]: (state.documents[action.payload.projectId] || []).filter(doc =>
                        doc.id !== action.payload.documentId
                    )
                }
            };
        case 'SET_INDEXES':
            return {
                ...state,
                indexes: { ...state.indexes, [action.payload.projectId]: action.payload.indexes }
            };
        case 'ADD_INDEX':
            return {
                ...state,
                indexes: {
                    ...state.indexes,
                    [action.payload.projectId]: [
                        action.payload.index,
                        ...(state.indexes[action.payload.projectId] || [])
                    ]
                }
            };
        case 'UPDATE_INDEX':
            return {
                ...state,
                indexes: {
                    ...state.indexes,
                    [action.payload.projectId]: (state.indexes[action.payload.projectId] || []).map(idx =>
                        idx.id === action.payload.indexId ? { ...idx, ...action.payload.updates } : idx
                    )
                }
            };
        case 'DELETE_INDEX':
            return {
                ...state,
                indexes: {
                    ...state.indexes,
                    [action.payload.projectId]: (state.indexes[action.payload.projectId] || []).filter(idx =>
                        idx.id !== action.payload.indexId
                    )
                }
            };
        case 'SET_ACTIVE_PROJECT':
            return { ...state, activeProjectId: action.payload };
        default:
            return state;
    }
}

// Context
interface AppContextType extends AppState {
    // Project actions
    createProject: (name: string) => Promise<void>;
    loadProjects: () => Promise<void>;
    setActiveProject: (projectId: string | null) => void;
    deleteProject: (projectId: string) => Promise<void>;
    
    // Document actions
    uploadDocument: (projectId: string, file: File) => Promise<void>;
    loadDocuments: (projectId: string) => Promise<void>;
    deleteDocument: (projectId: string, documentId: string) => Promise<void>;
    
    // Index actions
    createIndex: (projectId: string, name: string, documentIds: string[]) => Promise<void>;
    loadIndexes: (projectId: string) => Promise<void>;
    startIndexing: (projectId: string, indexId: string) => Promise<void>;
    deleteIndex: (projectId: string, indexId: string) => Promise<void>;
    
    // Query actions
    queryIndex: (projectId: string, queryData: QueryRequest) => Promise<QueryResponse>;
    
    // Utility actions
    clearError: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Provider component
interface AppProviderProps {
    children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
    const [state, dispatch] = useReducer(appReducer, initialState);

    // Load projects on mount
    useEffect(() => {
        loadProjects();
    }, []);

    const setLoading = useCallback((loading: boolean) => dispatch({ type: 'SET_LOADING', payload: loading }), []);
    const setError = useCallback((error: string | null) => dispatch({ type: 'SET_ERROR', payload: error }), []);

    const createProject = useCallback(async (name: string) => {
        try {
            setLoading(true);
            setError(null);
            const project = await projectsApi.create({ name });
            dispatch({ type: 'ADD_PROJECT', payload: project });
            dispatch({ type: 'SET_ACTIVE_PROJECT', payload: project.id });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to create project');
            throw error;
        } finally {
            setLoading(false);
        }
    }, [setLoading, setError]);

    const loadProjects = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            const projects = await projectsApi.list();
            dispatch({ type: 'SET_PROJECTS', payload: projects });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to load projects');
        } finally {
            setLoading(false);
        }
    }, []);

    const setActiveProject = useCallback((projectId: string | null) => {
        dispatch({ type: 'SET_ACTIVE_PROJECT', payload: projectId });
    }, []);

    const deleteProject = useCallback(async (projectId: string) => {
        try {
            setError(null);
            setLoading(true);
            
            // Call the actual delete API
            await projectsApi.delete(projectId);
            
            // Update local state after successful API call
            dispatch({ type: 'DELETE_PROJECT', payload: projectId });
            // If this was the active project, clear it
            if (state.activeProjectId === projectId) {
                dispatch({ type: 'SET_ACTIVE_PROJECT', payload: null });
            }
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to delete project');
            throw error;
        } finally {
            setLoading(false);
        }
    }, [setError, setLoading, state.activeProjectId]);

    const uploadDocument = useCallback(async (projectId: string, file: File) => {
        try {
            setLoading(true);
            setError(null);
            const document = await documentsApi.upload(projectId, file);
            dispatch({ type: 'ADD_DOCUMENT', payload: { projectId, document } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to upload document');
            throw error;
        } finally {
            setLoading(false);
        }
    }, [setLoading, setError]);

    const loadDocuments = useCallback(async (projectId: string) => {
        try {
            setLoading(true);
            setError(null);
            const result = await documentsApi.list(projectId);
            dispatch({ type: 'SET_DOCUMENTS', payload: { projectId, documents: result.items } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to load documents');
        } finally {
            setLoading(false);
        }
    }, [setLoading, setError]);

    const deleteDocument = useCallback(async (projectId: string, documentId: string) => {
        try {
            setError(null);
            setLoading(true);
            
            // Call the actual delete API
            await documentsApi.delete(projectId, documentId);
            
            // Update local state after successful API call
            dispatch({ type: 'DELETE_DOCUMENT', payload: { projectId, documentId } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to delete document');
            throw error;
        } finally {
            setLoading(false);
        }
    }, [setError, setLoading]);

    const createIndex = useCallback(async (projectId: string, name: string, documentIds: string[]) => {
        try {
            setLoading(true);
            setError(null);
            const index = await indexesApi.create(projectId, { name, document_ids: documentIds });
            dispatch({ type: 'ADD_INDEX', payload: { projectId, index } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to create index');
            throw error;
        } finally {
            setLoading(false);
        }
    }, [setLoading, setError]);

    const loadIndexes = useCallback(async (projectId: string) => {
        try {
            setLoading(true);
            setError(null);
            const indexes = await indexesApi.list(projectId);
            dispatch({ type: 'SET_INDEXES', payload: { projectId, indexes } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to load indexes');
        } finally {
            setLoading(false);
        }
    }, [setLoading, setError]);

    const startIndexing = useCallback(async (projectId: string, indexId: string) => {
        try {
            setError(null);
            const index = await indexesApi.start(projectId, indexId);
            dispatch({ type: 'UPDATE_INDEX', payload: { projectId, indexId, updates: index } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to start indexing');
        }
    }, [setError]);

    const deleteIndex = useCallback(async (projectId: string, indexId: string) => {
        try {
            setError(null);
            setLoading(true);
            
            // Call the actual delete API
            await indexesApi.delete(projectId, indexId);
            
            // Update local state after successful API call
            dispatch({ type: 'DELETE_INDEX', payload: { projectId, indexId } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to delete index');
            throw error;
        } finally {
            setLoading(false);
        }
    }, [setError, setLoading]);

    const queryIndex = useCallback(async (projectId: string, queryData: QueryRequest): Promise<QueryResponse> => {
        try {
            setError(null);
            const response = await queryApi.query(projectId, queryData);
            return response;
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to query index');
            throw error;
        }
    }, [setError]);

    const clearError = useCallback(() => setError(null), []);

    const value: AppContextType = {
        ...state,
        createProject,
        loadProjects,
        setActiveProject,
        deleteProject,
        uploadDocument,
        loadDocuments,
        deleteDocument,
        createIndex,
        loadIndexes,
        startIndexing,
        deleteIndex,
        queryIndex,
        clearError,
    };

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Hook to use the context
export const useApp = (): AppContextType => {
    const context = useContext(AppContext);
    if (context === undefined) {
        throw new Error('useApp must be used within an AppProvider');
    }
    return context;
};