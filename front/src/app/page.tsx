'use client'

import React, {useState, useEffect, useRef} from 'react';
import RuneBackground from "@/app/components/RuneBackground";

export default function Home() {
    const EMPTY_AUTHOR = '-------'
    const [dialogFields, setDialogFields] = useState([{author: '', quote: ''}]);
    const [authors, setAuthors] = useState<string[]>([EMPTY_AUTHOR]);
    const [explanation, setExplanation] = useState('');
    const [date, setDate] = useState('');
    const [focusIndex, setFocusIndex] = useState<number | null>(null);
    const selectRefs = useRef<(HTMLSelectElement | null)[]>([]);

    useEffect(() => {
        document.title = "Add new Quote";
    }, []);

    useEffect(() => {
        async function fetchAuthors() {
            const res = await fetch('/api/authors', {
                method: 'GET',
                headers: {'Content-Type': 'application/json'},
            });
            if (res.ok) {
                const authorsList: string[] = await res.json();
                authorsList.push(EMPTY_AUTHOR);
                setAuthors(authorsList.sort());
            }
        }

        fetchAuthors();
    }, []);


    useEffect(() => {
        if (focusIndex === null) return;
        const select = selectRefs.current[focusIndex];
        if (select) {
            select.focus();
            setFocusIndex(null);
        }
    }, [focusIndex]);

    const handleInputChange = (index: number, field: string, value: string) => {
        const updatedFields = [...dialogFields];
        if (field === 'quote')
            updatedFields[index].quote = value;
        else if (field === 'author')
            updatedFields[index].author = value;
        setDialogFields(updatedFields);
    };

    const addField = () => {
        if (dialogFields.length >= 8) return;
        setDialogFields([...dialogFields, {author: '', quote: ''}]);
        setFocusIndex(dialogFields.length);
    };

    function generate_quote() {
        const list = dialogFields.filter((e) =>  e.author !== EMPTY_AUTHOR);
        const pickedDate = new Date(date)
        const date_string = date === '' ? '----' : pickedDate.toLocaleString('default', { month: 'long' }) + " " + pickedDate.getFullYear();
        const explanation_string = (explanation.length <= 1) ? "----" : explanation;

        if (list.length <= 0){
            alert("Can't submit quote without author or data");
            clear_input();
            return null
        }
        else if (list.length === 1) {
            const quoteObject = {
                quote: list[0].quote,
                author: list[0].author,
                date: date_string,
                explanation: explanation_string,
            };
            return JSON.stringify(quoteObject);
        } else {
            const base_quote = list.map((e) => `"[${e.author}]${e.quote}"`);
            const base_authors = Array.from(new Set(list.map(e => e.author))).join(';');
            const quoteObject = {
                quote: base_quote,
                author: base_authors,
                date: date_string,
                explanation: explanation,
            };
            return JSON.stringify(quoteObject);
        }
    }

    async function send_quote(generateQuote: null | string) {
        if (generateQuote === null)
            return

        const res = await fetch('/api/quotes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: generateQuote,
            credentials: 'include'
        })

        console.log(res)

        if (res.ok) {
            alert("Quote submitted")
            clear_input()
        } else {
            const data = await res.json()
            alert(data.error || 'Quote submit failed')
        }
    }

    function clear_input() {
        setExplanation('')
        setDate('')
        setDialogFields([{author: '', quote: ''}])
    }

    const handleSubmit = async () => {
        await send_quote(generate_quote());
    };

    return (
        <div className="flex h-screen justify-center items-center">
            <RuneBackground/>

            <div className="rounded-2xl shadow-xl p-8 bg-cover bg-center w-96 contentContainer">
                <table className="table">
                    <tbody>
                    {dialogFields.map((row, index) => (
                        <tr key={index}>
                            <td>
                                <select
                                    ref={(el) => (selectRefs.current[index] = el)}
                                    className="select"
                                    value={row.author}
                                    onChange={(e) =>
                                        handleInputChange(index, 'author', e.target.value)
                                    }
                                >
                                    {authors.map((a) => (
                                        <option key={a} value={a} className="option">
                                            {a}
                                        </option>
                                    ))}
                                </select>
                            </td>
                            <td>
                                <input
                                    type="text"
                                    className="quote"
                                    value={row.quote}
                                    onChange={(e) =>
                                        handleInputChange(index, 'quote', e.target.value)
                                    }
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault(); // Prevent form submission or default enter behavior
                                            addField();
                                        }
                                    }}
                                />
                            </td>
                        </tr>
                    ))}
                    </tbody>
                </table>
                <table className="table">
                    <tbody>
                    <tr>
                        <td>Explanation</td>
                        <td>
                            <input
                                type="text"
                                className="quote"
                                value={explanation}
                                onChange={(e) => setExplanation(e.target.value)}
                            />
                        </td>
                    </tr>
                    <tr>
                        <td>Date</td>
                        <td>
                            <input
                                type="date"
                                className="quote"
                                value={date}
                                onChange={(e) => setDate(e.target.value)}
                            />
                        </td>
                    </tr>
                    </tbody>
                </table>

                <div>
                    <button className="buttons" onClick={handleSubmit}>
                        Submit
                    </button>
                    <button className="buttons" onClick={clear_input}>
                        Clear
                    </button>
                </div>
            </div>

        </div>
    );
}
