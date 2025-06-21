import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import {verifyJWT} from "@/utils/jwt";

export async function middleware(request: NextRequest) {
    const token = request.cookies.get('session_token')?.value;

    const pathname = request.nextUrl.pathname

    if (pathname === '/login' || pathname === '/api/login') {
        return NextResponse.next()
    }

    const payload = token ? await verifyJWT(token) : null;
    const role = payload?.role;

    if (!role && pathname !== '/login') {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    if (pathname.startsWith('/approve') && role !== 'master') {
        return NextResponse.redirect(new URL('/login', request.url))
    }

    if (pathname === '/login' && role === 'master') {
        return NextResponse.redirect(new URL('/approve', request.url))
    }

    if (pathname === '/login' && role === 'user') {
        return NextResponse.redirect(new URL('/', request.url))
    }

    return NextResponse.next()
}

export const config = {
    matcher: [
        '/((?!_next/|.*\\.svg|.*\\.png|.*\\.jpg|.*\\.jpeg|.*\\.gif|.*\\.webp).*)',
    ],
}
