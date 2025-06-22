import {type JSX, useEffect, useState} from 'react'
import {Navigate} from 'react-router-dom'
import {jwtDecode} from 'jwt-decode';

export interface JwtPayload {
    role?: string;
}

export const ProtectedRoute = ({children, requiredRole}: { children: JSX.Element, requiredRole?: string }) => {
    const [loading, setLoading] = useState<boolean>(true)
    const [authorized, setAuthorized] = useState<boolean>(false)
    const [role, setRole] = useState<string | null>(null)

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const res = await fetch(`${import.meta.env.VITE_DB_SERVER!}login/check`, {
                    method: 'GET',
                    headers: { "Content-Type": "application/json" },
                    credentials: 'include',
                });

                setAuthorized(res.ok);

                if (res.ok) {
                    const token: string = (await res.json())['token'];
                    if (token) {
                        const decoded = jwtDecode<JwtPayload>(token);
                        setRole(decoded.role || null);
                    } else {
                        setRole(null);
                    }
                }
            } catch {
                setAuthorized(false);
            } finally {
                setLoading(false);
            }
        };

        checkAuth();
    }, [])

    if (loading) return <div>Loading...</div>
    console.log(requiredRole)
    console.log(role)

    if (!authorized || (requiredRole !== undefined && requiredRole !== role))
        return <Navigate to="/login"/>

    return children
}