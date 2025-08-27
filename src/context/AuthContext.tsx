import React, { createContext, useContext, useMemo, useState } from "react";

export type User = { id: string; email: string };

export type AuthContextType = {
    user: User | null;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    loading: boolean;
    error: string | null;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<React.PropsWithChildren> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const login = async (email: string, password: string): Promise<void> => {
        setLoading(true);
        setError(null);
        try {
            // Replace with real API call: POST /auth/login -> { token, user }
            await new Promise((r) => setTimeout(r, 300));
            if (!email || !password) throw new Error("Email and password required");

            // Persist a demo token; replace with real token
            localStorage.setItem("kb_token", "demo_token");
            setUser({ id: "u_1", email });
        } catch (e) {
            const msg = e instanceof Error ? e.message : "Login failed";
            setError(msg);
            setUser(null);
            localStorage.removeItem("kb_token");
        } finally {
            setLoading(false);
        }
    };

    const logout = (): void => {
        setUser(null);
        localStorage.removeItem("kb_token");
        setError(null);
    };

    const value = useMemo<AuthContextType>(
        () => ({
            user,
            isAuthenticated: user !== null,
            login,
            logout,
            loading,
            error,
        }),
        [user, loading, error]
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within AuthProvider");
    return ctx;
};
