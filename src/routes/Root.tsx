import React, { useEffect, useState } from "react";
import Login from "../pages/Login";

// For testing: only wait a bit, then show Login
const SPLASH_MS = 1200; // adjust the delay as needed

const Root: React.FC = () => {
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const t = setTimeout(() => setLoading(false), SPLASH_MS);
        return () => clearTimeout(t);
    }, []);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-gray-600 text-sm">Loading…</div>
            </div>
        );
    }

    // After the short delay, always render Login (no token check)
    return <Login />;
};

export default Root;
