import {NextRequest, NextResponse} from "next/server";

export async function GET() {
    try {
        const response = await fetch(`${process.env.DB_SERVER!}quotes/nomination`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": process.env.API_KEY!
            },
        });

        if (!response.ok) {
            return NextResponse.json([], { status: response.status });
        }

        const quotes: string[] = await response.json();
        return NextResponse.json(quotes);
    } catch {
        return NextResponse.json([], { status: 500 });
    }
}

export async function POST(req: NextRequest) {
    try {
        const response = await fetch(`${process.env.DB_SERVER!}approve`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": process.env.API_KEY!
            },
            body: JSON.stringify(await req.json())
        });

        if (!response.ok) {
            return NextResponse.json({ message: (await response.json())['message']}, {status: response.status});
        }

        return NextResponse.json({ message: (await response.json())['message']}, {status: 200});
    } catch {
        return NextResponse.json({message: 'internal error'}, { status: 500 });
    }
}

export async function DELETE(req: NextRequest) {
    try {
        const response = await fetch(`${process.env.DB_SERVER!}approve`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": process.env.API_KEY!
            },
            body: JSON.stringify(await req.json())
        });

        if (!response.ok) {
            return NextResponse.json({ message: (await response.json())['message']}, {status: response.status});
        }

        return NextResponse.json({ message: (await response.json())['message']}, {status: 200});
    } catch {
        return NextResponse.json({message: 'internal error'}, { status: 500 });
    }
}
