import {NextRequest, NextResponse} from "next/server";
import { signRole } from '@/utils/jwt';

export async function POST(req: NextRequest) {
    const { password } = await req.json();

    let role = null

    if (password === process.env.MASTER_PASSWORD!) {
        role = 'master'
    } else if (password === process.env.USER_PASSWORD!) {
        role = 'user'
    }

    if (!role) {
        return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
    }

    const token = await signRole(role);
    const response = NextResponse.json({ message: 'Logged in', role });

    response.cookies.set('session_token', token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24,
    });

    return response;
}