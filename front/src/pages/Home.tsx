'use client'

import {useState, useEffect, useRef, useCallback} from 'react';
import RuneBackground from "../components/RuneBackground";

type SentenceObject = {
    number: number;
    author: string;
    sentence: string;
}

type QuoteObject = {
    date: string;
    explanation: string;
    sentences: SentenceObject[];
}

const EMPTY_AUTHOR = '-------';
const MAX_LINES = 8;

export default function Home() {
    const [dialogFields, setDialogFields] = useState([{author: EMPTY_AUTHOR, sentence: ''}]);
    const [authors, setAuthors] = useState<string[]>([EMPTY_AUTHOR]);
    const [explanation, setExplanation] = useState('');
    const [date, setDate] = useState('');
    const [focusIndex, setFocusIndex] = useState<number | null>(null);

    const textareaRefs = useRef<(HTMLTextAreaElement | null)[]>([]);

    useEffect(() => {
        document.title = "Add new Quote";
    }, []);

    useEffect(() => {
        async function fetchAuthors() {
            const res = await fetch('/api/authors', {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include'
            });
            if (res.ok) {
                const authorsList: string[] = await res.json();
                authorsList.push(EMPTY_AUTHOR);
                setAuthors(authorsList.sort());
            }
        }

        fetchAuthors();
    }, []);

    const autoResize = (el: HTMLTextAreaElement | null) => {
        if (!el) return;
        el.style.height = 'auto';
        el.style.height = `${el.scrollHeight}px`;
    };

    useEffect(() => {
        if (focusIndex === null) return;
        const el = textareaRefs.current[focusIndex];
        if (el) {
            el.focus();
            autoResize(el);
        }
        setFocusIndex(null);
    }, [focusIndex]);

    const handleAuthorChange = (index: number, value: string) => {
        setDialogFields(prev =>
            prev.map((row, i) => (i === index ? {...row, author: value} : row))
        );
    };

    const handleSentenceChange = (index: number, value: string) => {
        setDialogFields(prev =>
            prev.map((row, i) => (i === index ? {...row, sentence: value} : row))
        );
    };

    const addField = useCallback(() => {
        setDialogFields(prev => {
            if (prev.length >= MAX_LINES) return prev;
            setFocusIndex(prev.length);
            return [...prev, {author: EMPTY_AUTHOR, sentence: ''}];
        });
    }, []);

    const removeField = (index: number) => {
        setDialogFields(prev =>
            prev.length === 1
                ? [{author: EMPTY_AUTHOR, sentence: ''}] // keep at least one empty row
                : prev.filter((_, i) => i !== index)
        );
    };

    function generate_quote() {
        const list = dialogFields.filter(
            (e) => e.author !== EMPTY_AUTHOR && e.sentence.trim() !== ''
        );
        const pickedDate = new Date(date);
        const date_string = date === ''
            ? '----'
            : pickedDate.toLocaleString('default', {month: 'long'}) + " " + pickedDate.getFullYear();
        const explanation_string = (explanation.length <= 1) ? "----" : explanation;

        if (list.length <= 0) {
            alert('Can\'t submit a quote without at least one author and line.');
            return null;
        }

        const sentences: SentenceObject[] = list.map((item, i) => ({
            number: i,
            author: item.author,
            sentence: item.sentence,
        }));

        const quoteObject: QuoteObject = {
            date: date_string,
            explanation: explanation_string,
            sentences: sentences
        };
        return JSON.stringify(quoteObject);
    }

    async function send_quote(generateQuote: null | string) {
        if (generateQuote === null) return;

        const res = await fetch('/api/quotes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: generateQuote,
            credentials: 'include'
        });

        if (res.ok) {
            alert("Quote submitted");
            clear_input();
        } else {
            const data = await res.json().catch(() => ({}));
            alert(data.error || 'Quote submit failed');
        }
    }

    function clear_input() {
        setExplanation('');
        setDate('');
        setDialogFields([{author: EMPTY_AUTHOR, sentence: ''}]);
    }

    const handleSubmit = async () => {
        await send_quote(generate_quote());
    };

    const previewSentences = dialogFields.filter(
        (e) => e.author !== EMPTY_AUTHOR && e.sentence.trim() !== ''
    );
    const previewDate = date === ''
        ? ''
        : new Date(date).toLocaleString('default', {month: 'long'}) + " " + new Date(date).getFullYear();

    return (
        <div className="page">
            <RuneBackground/>

            <div className="layout">
                {/* ---------- EDITOR ---------- */}
                <div className="contentContainer">
                    <h1 className="cardTitle">Add a Quote</h1>

                    <div className="lines">
                        {dialogFields.map((row, index) => (
                            <div className="line" key={index}>
                                <select
                                    className="select"
                                    value={row.author}
                                    onChange={(e) => handleAuthorChange(index, e.target.value)}
                                    aria-label={`Author for line ${index + 1}`}
                                >
                                    {authors.map((a) => (
                                        <option key={a} value={a} className="option">
                                            {a}
                                        </option>
                                    ))}
                                </select>

                                <textarea
                                    ref={(el) => { textareaRefs.current[index] = el; }}
                                    className="quote"
                                    rows={1}
                                    placeholder="Type the line…"
                                    value={row.sentence}
                                    onChange={(e) => {
                                        handleSentenceChange(index, e.target.value);
                                        autoResize(e.target);
                                    }}
                                    onKeyDown={(e) => {
                                        // Power-user shortcut: Ctrl/Cmd+Enter adds a line.
                                        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                                            e.preventDefault();
                                            addField();
                                        }
                                    }}
                                    aria-label={`Line ${index + 1} text`}
                                />

                                <button
                                    type="button"
                                    className="iconButton"
                                    onClick={() => removeField(index)}
                                    aria-label={`Remove line ${index + 1}`}
                                    title="Remove line"
                                >
                                    ×
                                </button>
                            </div>
                        ))}
                    </div>

                    <button
                        type="button"
                        className="addButton"
                        onClick={addField}
                        disabled={dialogFields.length >= MAX_LINES}
                    >
                        + Add line
                    </button>

                    <div className="metaField">
                        <label htmlFor="explanation">Explanation</label>
                        <textarea
                            id="explanation"
                            className="quote"
                            rows={2}
                            placeholder="Optional context…"
                            value={explanation}
                            onChange={(e) => {
                                setExplanation(e.target.value);
                                autoResize(e.target);
                            }}
                        />
                    </div>

                    <div className="metaField">
                        <label htmlFor="date">Date</label>
                        <input
                            id="date"
                            type="date"
                            className="quote"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                        />
                    </div>

                    <div className="actions">
                        <button className="buttons" onClick={handleSubmit}>Submit</button>
                        <button className="buttons" onClick={clear_input}>Clear</button>
                    </div>
                </div>

                {/* ---------- PREVIEW ---------- */}
                <div className="previewContainer">
                    <h2 className="cardTitle">Preview</h2>

                    {previewSentences.length === 0 ? (
                        <p className="previewEmpty">Pick an author and type a line to see the preview.</p>
                    ) : (
                        <div className="previewBody">
                            {previewSentences.map((s, i) => (
                                <p className="previewLine" key={i}>
                                    <span className="previewAuthor">{s.author}:</span> {s.sentence}
                                </p>
                            ))}
                            <div className="previewMeta">
                                <span>{previewDate || '----'}</span>
                                {explanation.length > 1 && <span className="previewExpl">{explanation}</span>}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}