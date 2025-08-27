import React, { createContext, useContext, useState, useEffect } from "react";
import type { SampleDataType } from "../types/sample";
import { fetchData } from "../services/api/sample";

interface SampleContextType {
  data: SampleDataType;
  error: string | null;
  isLoading: boolean;
  getData: () => Promise<void>;
}

const SampleContext = createContext<SampleContextType | undefined>(undefined);

export const SampleProvider: React.FC<{ children: React.ReactNode }> = ({children}) => {

    const [data, setData] = useState<SampleDataType>({
        name: '',
        description: ''
    });
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setLoading] = useState<boolean>(true);


    const getData = async (): Promise<void> => {
        setLoading(true);
        setError(null);
        try {
            const dataFetched = await fetchData();
            setData(dataFetched);
        } catch (err) {
            setError(
                err instanceof Error ? err.message : "An unknown error occurred"
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    const value = {
        data,
        error,
        isLoading,
        getData
    };

    return (
        <SampleContext.Provider value={value}>
        {children}
        </SampleContext.Provider>
    );
};

export const useSample = (): SampleContextType => {
    const context = useContext(SampleContext);

    if (context === undefined) {
        throw new Error("useAllProjects must be used within a AllProjectsProvider");
    }

    return context;
};
