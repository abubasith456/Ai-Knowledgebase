import React, { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";

const Login: React.FC = () => {
    const nav = useNavigate();
    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [submitting, setSubmitting] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const onSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
        e.preventDefault();
        setSubmitting(true);
        setError(null);
        try {
            // For testing: simulate a brief async call
            await new Promise((r) => setTimeout(r, 500));

            // No real auth here. After "success", go to dashboard
            nav("/dashboard", { replace: true });
        } catch (err) {
            const msg = err instanceof Error ? err.message : "Login failed";
            setError(msg);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
            <div className="w-full max-w-sm space-y-6">
                <div className="text-center">
                    <h1 className="text-2xl font-semibold text-gray-900">Sign in</h1>
                    <p className="text-sm text-gray-500">Use email and password</p>
                </div>

                <form onSubmit={onSubmit} className="space-y-4 bg-white p-6 rounded-lg shadow">
                    <div>
                        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                            Email
                        </label>
                        <input
                            id="email"
                            type="email"
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="name@company.com"
                            required
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                            Password
                        </label>
                        <input
                            id="password"
                            type="password"
                            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    {error && <div className="text-sm text-red-600">{error}</div>}

                    <button
                        type="submit"
                        disabled={submitting}
                        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-white text-sm font-medium hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
                    >
                        {submitting ? "Signing in..." : "Sign in"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Login;
