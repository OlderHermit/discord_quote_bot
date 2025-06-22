'use client'

import {useEffect, useState} from 'react';
import styles from '../styles/Approve.module.css'
import RuneBackground from '../components/RuneBackground.tsx';

type Quote = {
    id: number;
    quote: string;
    explanation: string;
    author: string;
};

type QuoteObject = {
    id: number;
    quote: string;
    explanation: string;
};

export default function QuotesPage() {
    const [quotes, setQuotes] = useState<Quote[]>([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        document.title = 'Approve Quote';
    }, []);

    useEffect(() => {
        async function fetchQuotes() {
            const res = await fetch(`${import.meta.env.VITE_DB_SERVER!}quotes/nominations`, {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include'
            });

            if (!res.ok) {
                setError(res.statusText);
                return
            }
            const data: [QuoteObject, string][] = await res.json();
            setQuotes(
                data.map(([quoteObj, author]) => ({
                    id: quoteObj.id,
                    quote: quoteObj.quote,
                    explanation: quoteObj.explanation,
                    author: author,
                }))
            );
        }



        fetchQuotes();
        setLoading(false);
    }, []);

    const removeQuote = (idToRemove: number) => {
        setQuotes(prev => prev.filter(q => q.id !== idToRemove));
    };

    async function approveQuote(id: number) {
        const res = await fetch(`${import.meta.env.VITE_DB_SERVER!}quotes/approve`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id }),
            credentials: 'include'
        });

        if (!res.ok) {
            alert('couldn\'t approve quote: ' + (await res.json())['message'])
            return
        }

        removeQuote(id)
    }

    async function discardQuote(id: number) {
        const res = await fetch(`${import.meta.env.VITE_DB_SERVER!}quotes/approve`, {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id }),
            credentials: 'include'
        });

        if (!res.ok) {
            alert('couldn\'t delete quote: ' + (await res.json())['message'])
            return
        }

        removeQuote(id)
    }

    if (loading) return <p>Loading quotes...</p>;
    if (error) return <p>Error: {error}</p>;
    if (!quotes || quotes.length === 0) return <p>No quotes found.</p>;

    return (
        <div className='flex h-screen justify-center items-center'>
            <RuneBackground/>
            <div>
                {quotes.map((q) => (
                    <div key={q.id} className={`rounded-2xl shadow-xl p-8 bg-cover bg-center w-96 ${styles.column_approve}`}>
                        <div className='items-start'>
                            {q.quote.split('[NEW_SENTENCE]').map((sentence, i) => {
                                return (
                                    <p key={i} className={styles.text_approve}>
                                        {sentence.replace(']', ': ').replace('[', '')}
                                    </p>
                                );
                            })}
                            <p className='text_approve'>{q.explanation}</p>
                            <p className='text_approve'>{q.author}</p>
                        </div>
                        <div className='flex justify-center items-center gap-2 mt-4'>
                            <input
                                type='button'
                                onClick={() => approveQuote(q.id)}
                                value='Accept'
                            />
                            <input
                                type='button'
                                onClick={() => discardQuote(q.id)}
                                value='Discard'
                            />
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}