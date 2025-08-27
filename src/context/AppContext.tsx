import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
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
    | { type: 'SET_DOCUMENTS'; payload: { projectId: string; documents: Document[] } }
    | { type: 'ADD_DOCUMENT'; payload: { projectId: string; document: Document } }
    | { type: 'UPDATE_DOCUMENT'; payload: { projectId: string; documentId: string; updates: Partial<Document> } }
    | { type: 'SET_INDEXES'; payload: { projectId: string; indexes: Index[] } }
    | { type: 'ADD_INDEX'; payload: { projectId: string; index: Index } }
    | { type: 'UPDATE_INDEX'; payload: { projectId: string; indexId: string; updates: Partial<Index> } }
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
    
    // Document actions
    uploadDocument: (projectId: string, file: File) => Promise<void>;
    loadDocuments: (projectId: string) => Promise<void>;
    parseNextDocument: (projectId: string) => Promise<void>;
    
    // Index actions
    createIndex: (projectId: string, name: string, documentIds: string[]) => Promise<void>;
    loadIndexes: (projectId: string) => Promise<void>;
    startIndexing: (projectId: string, indexId: string) => Promise<void>;
    
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

    const setLoading = (loading: boolean) => dispatch({ type: 'SET_LOADING', payload: loading });
    const setError = (error: string | null) => dispatch({ type: 'SET_ERROR', payload: error });

    const createProject = async (name: string) => {
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
    };

    const loadProjects = async () => {
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
    };

    const setActiveProject = (projectId: string | null) => {
        dispatch({ type: 'SET_ACTIVE_PROJECT', payload: projectId });
    };

    const uploadDocument = async (projectId: string, file: File) => {
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
    };

    const loadDocuments = async (projectId: string) => {
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
    };

    const parseNextDocument = async (projectId: string) => {
        try {
            setError(null);
            const document = await documentsApi.parseNext(projectId);
            if (document) {
                dispatch({ type: 'UPDATE_DOCUMENT', payload: { projectId, documentId: document.id, updates: document } });
            }
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to parse document');
        }
    };

    const createIndex = async (projectId: string, name: string, documentIds: string[]) => {
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
    };

    const loadIndexes = async (projectId: string) => {
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
    };

    const startIndexing = async (projectId: string, indexId: string) => {
        try {
            setError(null);
            const index = await indexesApi.start(projectId, indexId);
            dispatch({ type: 'UPDATE_INDEX', payload: { projectId, indexId, updates: index } });
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to start indexing');
        }
    };

    const queryIndex = async (projectId: string, queryData: QueryRequest): Promise<QueryResponse> => {
        try {
            setError(null);
            const response = await queryApi.query(projectId, queryData);
            return response;
        } catch (error) {
            setError(error instanceof Error ? error.message : 'Failed to query index');
            throw error;
        }
    };

    const clearError = () => setError(null);

    const value: AppContextType = {
        ...state,
        createProject,
        loadProjects,
        setActiveProject,
        uploadDocument,
        loadDocuments,
        parseNextDocument,
        createIndex,
        loadIndexes,
        startIndexing,
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