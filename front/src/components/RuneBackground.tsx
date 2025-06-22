import {useEffect, useRef, useState} from 'react';
import styles from './RuneBackground.module.css';

const runes = [
    'ᚠ', 'ᚡ', 'ᚢ', 'ᚣ', 'ᚤ', 'ᚥ', 'ᚦ', 'ᚧ', 'ᚨ', 'ᚩ', 'ᚪ', 'ᚫ', 'ᚬ', 'ᚭ', 'ᚮ', 'ᚯ',
    'ᚰ', 'ᚱ', 'ᚲ', 'ᚳ', 'ᚴ', 'ᚵ', 'ᚶ', 'ᚷ', 'ᚸ', 'ᚹ', 'ᚺ', 'ᚻ', 'ᚼ', 'ᚽ', 'ᚾ', 'ᚿ',
    'ᛀ', 'ᛁ', 'ᛂ', 'ᛃ', 'ᛄ', 'ᛅ', 'ᛆ', 'ᛇ', 'ᛈ', 'ᛉ', 'ᛊ', 'ᛋ', 'ᛌ', 'ᛍ', 'ᛎ', 'ᛏ',
    'ᛐ', 'ᛑ', 'ᛒ', 'ᛓ', 'ᛔ', 'ᛕ', 'ᛖ', 'ᛗ', 'ᛘ', 'ᛙ', 'ᛚ', 'ᛛ', 'ᛜ', 'ᛝ', 'ᛞ', 'ᛟ',
    'ᛠ', 'ᛡ', 'ᛢ', 'ᛣ', 'ᛤ', 'ᛥ', 'ᛦ', 'ᛧ', 'ᛨ', 'ᛩ', 'ᛪ', '᛫', '᛬', '᛭', 'ᛮ', 'ᛯ',
    'ᛰ'
];

const runesSizes: Record<string, number>  = {
    'ᚠ':10.5, 'ᚡ':10.5, 'ᚢ':9.5, 'ᚣ':8.3, 'ᚤ':9.5, 'ᚥ':9.8, 'ᚦ':7.6, 'ᚧ':7.6, 'ᚨ':5.9, 'ᚩ':8.4, 'ᚪ':8.4, 'ᚫ':7.5, 'ᚬ':7.6, 'ᚭ':5.9, 'ᚮ':5.9, 'ᚯ':7.6,
    'ᚰ':7.6, 'ᚱ':8.4, 'ᚲ':5.0, 'ᚳ':6.4, 'ᚴ':8.7, 'ᚵ':8.7, 'ᚶ':8.7, 'ᚷ':7.7, 'ᚸ':7.7, 'ᚹ':8.4, 'ᚺ':9.6, 'ᚻ':9.6, 'ᚼ':7.6, 'ᚽ':4.3, 'ᚾ':7.6, 'ᚿ':5.9,
    'ᛀ':7.6, 'ᛁ':4.2, 'ᛂ':4.2, 'ᛃ':8.1, 'ᛄ':5.8, 'ᛅ':7.6, 'ᛆ':5.9, 'ᛇ':7.6, 'ᛈ':8.4, 'ᛉ':8.6, 'ᛊ':6.1, 'ᛋ':9.1, 'ᛌ':4.2, 'ᛍ':4.2, 'ᛎ':7.6, 'ᛏ':7.6,
    'ᛐ':5.9, 'ᛑ':5.9, 'ᛒ':8.4, 'ᛓ':5.9, 'ᛔ':8.5, 'ᛕ':8.1, 'ᛖ':10.1, 'ᛗ':10.1, 'ᛘ':9.0, 'ᛙ':4.2, 'ᛚ':5.9, 'ᛛ':5.9, 'ᛜ':7.2, 'ᛝ':7.8, 'ᛞ':10.1, 'ᛟ':7.5,
    'ᛠ':8.9, 'ᛡ':7.6, 'ᛢ':8.9, 'ᛣ':8.6, 'ᛤ':7.7, 'ᛥ':10.1, 'ᛦ':9.0, 'ᛧ':4.2, 'ᛨ':7.6, 'ᛩ':8.4, 'ᛪ':9.7, '᛫':4.7, '᛬':3.5, '᛭':10.3, 'ᛮ':7.6, 'ᛯ':9.0,
    'ᛰ':9.1
};

type RuneResult = {
    delay: number;
    amount: number;
    x: number;
    y: number;
    runeWidth: number;
    selectedRunes: string[]; // Adjust this if selectedRunes is not an array of strings
    failed: boolean;
};


const RuneBackground = () => {
    const backgroundRef = useRef(null);
    const [runesData, setRunesData] = useState<RuneResult[]>([]);

    const generateBackground = () => {
        const vw: number = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
        const vh: number = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

        const localRunesData: RuneResult[] = [];

        for (let i = 0; i < 200; i++) {
            const runeData = generateRuneForBackground(localRunesData, vw, vh);
            localRunesData.push(runeData);
        }

        return localRunesData.filter((runeData) => !runeData.failed);
    };

    useEffect(() => {
        const handleResize = () => {
            const background = generateBackground();
            if (background) {
                setRunesData(background);
            }
        };

        requestAnimationFrame(() => {
            handleResize();
        });

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const generateRuneForBackground = (list: RuneResult[], vw: number, vh: number) => {
        const delay = Math.random() * 25;
        const amount = Math.floor(Math.random() * 9) + 3;
        let x = Math.random() * 100;
        let y = Math.random() * 95;
        let runeWidth = 0;
        const runeHeight = 24;

        // Calculate total size
        const selectedRunes: string[] = [];
        for (let i = 0; i < amount; i++) {
            const symbol = runes[Math.floor(Math.random() * runes.length)];
            selectedRunes.push(symbol);
            runeWidth += runesSizes[symbol];
        }

        let retryCounter = 50;

        // Check for overlaps
        while (retryCounter > 0) {
            const currentLeft = (x * vw) / 100;
            const currentTop = (y * vh) / 100;
            const currentRight = currentLeft + runeWidth;
            const currentBottom = currentTop + runeHeight;

            // Check if current position overlaps with any existing rune
            const hasOverlap = list.some(existingRune => {
                const existingLeft = (existingRune.x * vw) / 100;
                const existingTop = (existingRune.y * vh) / 100;
                const existingRight = existingLeft + existingRune.runeWidth;
                const existingBottom = existingTop + runeHeight;

                // Check for rectangle overlap
                return !(currentRight < existingLeft ||
                    currentLeft > existingRight ||
                    currentBottom < existingTop ||
                    currentTop > existingBottom);
            });

            // Also check bounds
            const withinBounds = (currentLeft >= 0 &&
                currentRight <= vw &&
                currentTop >= 0 &&
                currentBottom <= vh);

            if (!hasOverlap && withinBounds) {
                break;
            }

            x = Math.random() * 100;
            y = Math.random() * 95;
            retryCounter--;
        }

        return {
            delay,
            amount,
            x: retryCounter <= 0 ? 0 : x,
            y: retryCounter <= 0 ? 0 : y,
            runeWidth,
            selectedRunes,
            failed: retryCounter <= 0
        };
    };

    return (
        <div id="background" ref={backgroundRef} className={styles.backgroundContainer}>
            {(runesData ?? []).map((runeData, index) => (
                <div
                    key={index}
                    className={styles.runesContainer}
                    style={{
                        left: `${runeData.x}vw`,
                        top: `${runeData.y}vh`,
                        animation: `scrollAnimation ${runeData.runeWidth / 4}s infinite linear`,
                        animationDelay: `${runeData.delay}s`,
                    }}
                >
                    {runeData.selectedRunes.map((symbol, runeIndex) => (
                        <div
                            key={runeIndex}
                            className={styles.rune}
                            style={{
                                animationDelay: `${runeData.delay + runeIndex * 0.5}s`,
                                opacity: 0
                            }}
                        >
                            {symbol}
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
};

export default RuneBackground;