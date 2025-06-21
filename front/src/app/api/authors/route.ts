import { NextResponse } from "next/server";

export async function GET() {
    try {
        const response = await fetch(`${process.env.DB_SERVER!}authors`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": process.env.API_KEY!
            },
        });

        if (!response.ok) {
            return NextResponse.json([], { status: response.status });
        }

        const authorsList: string[] = await response.json();
        return NextResponse.json(authorsList);
    } catch {
        return NextResponse.json([], { status: 500 });
    }
}
