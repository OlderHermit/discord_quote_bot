import {NextRequest, NextResponse} from "next/server";

export async function POST(req: NextRequest) {
    try {
        const response = await fetch(`${process.env.DB_SERVER!}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "x-api-key": process.env.API_KEY!
            },
            body: await req.json(),
        });

        if (!response.ok) {
            return NextResponse.json({ message: (await response.json())['message']}, {status: response.status});
        }

        return NextResponse.json({ message: (await response.json())['message']}, {status: 200});
    } catch (error) {
        return NextResponse.json({ message: error}, {status: 500 });
    }
}
