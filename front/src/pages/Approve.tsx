import {useEffect, useState} from 'react';
import styles from '../styles/Approve.module.css'
import RuneBackground from '../components/RuneBackground.tsx';

type SentenceObject = {
    number: number;
    sentence: string;
    author_id: string;
}

type QuoteObject = {
    id: number;
    explanation: string;
    sentences: SentenceObject[]
};

export default function QuotesPage() {
    const [quotes, setQuotes] = useState<QuoteObject[]>([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        document.title = 'Approve Quote';
    }, []);

    useEffect(() => {
        async function fetchQuotes() {
            try {
                const res = await fetch('/api/quotes/nominations', {
                    method: 'GET',
                    headers: {'Content-Type': 'application/json'},
                    credentials: 'include'
                });

                if (!res.ok) {
                    const body = await res.json().catch(() => null);
                    alert(`Couldn't load quotes: ${body?.message ?? 'no message provided'}`);
                    return;
                }

                setQuotes(await res.json());
            } catch {
                setError('Network error');
            } finally {
                setLoading(false);   // runs after the request resolves, not before
            }
        }

        fetchQuotes();
    }, []);

    const removeQuote = (idToRemove: number) => {
        setQuotes(prev => prev.filter(q => q.id !== idToRemove));
    };

    async function approveQuote(id: number) {
        const res = await fetch('/api/quotes/approve', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id }),
            credentials: 'include'
        });

        if (!res.ok) {
            const body = await res.json().catch(() => null);
            alert(`Couldn't approve quote: ${body?.message ?? 'no message provided'}`);
            return
        }

        removeQuote(id)
    }

    async function discardQuote(id: number) {
        const res = await fetch('/api/quotes/approve', {
            method: 'DELETE',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id: id }),
            credentials: 'include'
        });

        if (!res.ok) {
            alert('couldn\'t delete quote: ' + (await res.json())['message'] || 'No message provided')
            return
        }

        removeQuote(id)
    }

    return (
        <div className="page">
            <RuneBackground/>
            <div className={styles.shell}>
                <h1 className="cardTitle">Approve Nominations</h1>

                {!loading && !error && (
                    <p className="previewEmpty">
                        {quotes.length} nomination{quotes.length === 1 ? '' : 's'} pending
                    </p>
                )}

                {loading ? (
                    <p className="previewEmpty">Loading nominations…</p>
                ) : error ? (
                    <p className={styles.statusError}>Error: {error}</p>
                ) : quotes.length === 0 ? (
                    <p className="previewEmpty">No nominations waiting.</p>
                ) : (
                    <div className="layout">
                        {quotes.map((q) => (
                            <div key={q.id} className={styles.column_approve}>
                                <div className={styles.lines}>
                                    {q.sentences.map((sentence, i) => (
                                        <p key={i} className={styles.text_approve}>
                                            {sentence.author_id + ': ' + sentence.sentence}
                                        </p>
                                    ))}
                                    {q.explanation && (
                                        <p className={styles.explanation}>{q.explanation}</p>
                                    )}
                                </div>
                                <div className={styles.actions}>
                                    <input
                                        type='button'
                                        className={`${styles.button} ${styles.acceptButton}`}
                                        onClick={() => approveQuote(q.id)}
                                        value='Accept'
                                    />
                                    <input
                                        type='button'
                                        className={`${styles.button} ${styles.discardButton}`}
                                        onClick={() => discardQuote(q.id)}
                                        value='Discard'
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}