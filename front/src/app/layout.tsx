import {Geist, Geist_Mono} from "next/font/google";
import "./globals.css";

export const metadata = {
    icons: {
        icon: [
            {
                url: '/favicon.png',
                type: 'image/png',
                sizes: '32x32',
            },
        ],
    },
};

const geistSans = Geist({
    variable: "--font-geist-sans",
    subsets: ["latin"],
});

const geistMono = Geist_Mono({
    variable: "--font-geist-mono",
    subsets: ["latin"],
});

export default function RootLayout({children}: Readonly<{ children: React.ReactNode; }>) {
    return (
        <html lang="en">
        <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        {children}
        </body>
        </html>
    );
}
