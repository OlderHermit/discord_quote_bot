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

            const res = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password }),
                credentials: 'include'
            });

            if (res.ok) {
                const { role } = await res.json();
                navigate(role === 'master' ? '/approve' : '/');
                return;
            }

            setError('Login failed');
        } catch {
            setError('Network error. Please try again.');
        }
    };

    return (
        <div>
            <RuneBackground />
            <div
                style={{ backgroundPosition: "center center", paddingTop: "30px" }}
            >
                <h2>Login</h2>
                <input
                    type="password"
                    placeholder="Enter password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            handleLogin();
                        }
                    }}
                />
                {error && <p>{error}</p>}
                <button
                    onClick={handleLogin}
                >
                    Log In
                </button>
            </div>
        </div>
    );
};

export default Login;