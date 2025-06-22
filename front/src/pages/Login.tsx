import {useEffect, useState} from "react";
import { useNavigate } from 'react-router-dom';
import RuneBackground from '../components/RuneBackground';
import {jwtDecode} from "jwt-decode";
import type {JwtPayload} from "../components/ProtectedRoute.tsx";

export const Login = () => {
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    useEffect(() => {
        document.title = "Password Verification";
    }, []);

    const handleLogin = async () => {
        try {
            setError('');

            const res = await fetch(`${import.meta.env.VITE_DB_SERVER!}login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password }),
                credentials: 'include'
            });

            if (res.ok) {
                const token: string = (await res.json())['token'];
                const role = jwtDecode<JwtPayload>(token).role;
                if (role === 'master')
                    navigate('/approve');
                if (role ==='user')
                    navigate('/');
            }

            setError('Login failed');
        } catch {
            setError('Network error. Please try again.');
        }
    };

    return (
        <div className="flex h-screen justify-center items-center">
            <RuneBackground />
            <div
                className="rounded-2xl shadow-xl p-8 bg-cover bg-center contentContainer"
                style={{ backgroundPosition: "center center", paddingTop: "30px" }}
            >
                <h2 className="text-black text-2xl mb-4 font-semibold">Login</h2>
                <input
                    type="password"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="border-black border-2 w-3/4 px-4 py-2 rounded mb-3 text-black"
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            handleLogin();
                        }
                    }}
                />
                {error && <p className="text-red-400 mb-2">{error}</p>}
                <button
                    onClick={handleLogin}
                    className="border-black border-2 blend text-black px-4 py-2 rounded w-1/3"
                >
                    Log In
                </button>
            </div>
        </div>
    );
};

export default Login;