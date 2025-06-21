'use client'

import {useEffect, useState} from 'react'
import { useRouter } from 'next/navigation'
import RuneBackground from "@/app/components/RuneBackground";

export default function LoginPage() {
    const [password, setPassword] = useState('')
    const [error, setError] = useState('')
    const router = useRouter()

    useEffect(() => {
        document.title = "Password Veryfication";
    }, []);

    const handleLogin = async () => {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ password }),
            credentials: 'include'
        })

        if (res.ok) {
            router.push('/')
        } else {
            const data = await res.json()
            setError(data.error || 'Login failed')
        }
    }

    return (
        <div className="flex h-screen justify-center items-center">
            <RuneBackground/>
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
    )
}


