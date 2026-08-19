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

const GAP = 6;
const MAX_RUNES = 200;
/** One rune per this many px² of viewport, so phones stay sparse. */
const AREA_PER_RUNE = 12_000;
const MIN_GLYPHS = 3;
const MAX_GLYPHS = 11;
/** Positions tried per rune before giving up on it. */
const PLACEMENT_ATTEMPTS = 50;
/** Runes skipped in a row before we call the canvas full. */
const MAX_CONSECUTIVE_FAILURES = 25;
const RESIZE_DEBOUNCE_MS = 200;
/** Ignore resizes smaller than this (mobile toolbars, soft keyboard). */
const RESIZE_DEAD_ZONE_PX = 120;

type RuneResult = {
    delay: number;
    x: number;
    y: number;
    runeWidth: number;
    selectedRunes: string[]; // Adjust this if selectedRunes is not an array of strings
};

type Rect = { left: number; top: number; right: number; bottom: number };

function fontSpecOf(el: HTMLElement): string {
    const cs = getComputedStyle(el);
    return `${cs.fontStyle} ${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
}

function measureRunes(fontSpec: string): Record<string, number> {
    const ctx = document.createElement('canvas').getContext('2d');
    if (!ctx) return Object.fromEntries(runes.map((r) => [r, 8]));
    ctx.font = fontSpec;
    return Object.fromEntries(runes.map((r) => [r, ctx.measureText(r).width]));
}

class BandIndex {
    private readonly cells = new Map<number, Rect[]>();

    constructor(private readonly bandHeight: number) {}

    private firstBand(top: number): number {
        return Math.floor(top / this.bandHeight);
    }

    private lastBand(bottom: number): number {
        return Math.floor(bottom / this.bandHeight);
    }

    collides(r: Rect): boolean {
        const last = this.lastBand(r.bottom);
        for (let band = this.firstBand(r.top); band <= last; band++) {
            const bucket = this.cells.get(band);
            if (!bucket) continue;
            for (const other of bucket) {
                if (
                    r.left < other.right &&
                    r.right > other.left &&
                    r.top < other.bottom &&
                    r.bottom > other.top
                ) {
                    return true;
                }
            }
        }
        return false;
    }

    insert(r: Rect): void {
        const last = this.lastBand(r.bottom);
        for (let band = this.firstBand(r.top); band <= last; band++) {
            const bucket = this.cells.get(band);
            if (bucket)
                bucket.push(r);
            else
                this.cells.set(band, [r]);
        }
    }
}

function generateBackground(
    vw: number,
    vh: number,
    widths: Record<string, number>,
    runeHeight: number,
): RuneResult[] {
    const index = new BandIndex(Math.max(runeHeight, 1));
    const target = Math.min(MAX_RUNES, Math.round((vw * vh) / AREA_PER_RUNE));
    const placed: RuneResult[] = [];
    let consecutiveFailures = 0;

    while (placed.length < target && consecutiveFailures < MAX_CONSECUTIVE_FAILURES) {
        const glyphCount = MIN_GLYPHS + Math.floor(Math.random() * (MAX_GLYPHS - MIN_GLYPHS + 1));

        const selectedRunes: string[] = [];
        let runeWidth = 0;
        for (let i = 0; i < glyphCount; i++) {
            const glyph = runes[Math.floor(Math.random() * runes.length)];
            selectedRunes.push(glyph);
            runeWidth += widths[glyph] ?? 0;
        }

        // Draw straight from the valid range, so no attempt is wasted on a
        // position that could never fit inside the viewport.
        const maxLeft = vw - runeWidth - GAP;
        const maxTop = vh - runeHeight - GAP;
        if (maxLeft <= GAP || maxTop <= GAP) break;

        let success = false;
        for (let attempt = 0; attempt < PLACEMENT_ATTEMPTS; attempt++) {
            const left = GAP + Math.random() * (maxLeft - GAP);
            const top = GAP + Math.random() * (maxTop - GAP);

            const rect: Rect = {
                left: left - GAP,
                top: top - GAP,
                right: left + runeWidth + GAP,
                bottom: top + runeHeight + GAP,
            };

            if (index.collides(rect)) continue;

            index.insert(rect);
            placed.push({
                delay: Math.random() * 25,
                x: (left / vw) * 100,
                y: (top / vh) * 100,
                runeWidth,
                selectedRunes,
            });
            success = true;
            break;
        }

        consecutiveFailures = success ? 0 : consecutiveFailures + 1;
    }

    return placed;
}
const RuneBackground = () => {
    const probeRef = useRef<HTMLDivElement>(null);
    const [runesData, setRunesData] = useState<RuneResult[]>([]);

    useEffect(() => {
        let cancelled = false;
        let timer: number | undefined;
        let lastViewport = { w: 0, h: 0 };
        let widths: Record<string, number> | null = null;
        let runeHeight = 0;

        const regenerate = () => {
            if (cancelled || !widths) return;

            const vw = window.innerWidth;
            const vh = window.innerHeight;

            // Ignore the small height changes mobile browsers fire constantly.
            if (
                Math.abs(vw - lastViewport.w) < RESIZE_DEAD_ZONE_PX &&
                Math.abs(vh - lastViewport.h) < RESIZE_DEAD_ZONE_PX
            ) {
                return;
            }

            lastViewport = { w: vw, h: vh };
            setRunesData(generateBackground(vw, vh, widths, runeHeight));
        };

        const init = async () => {
            // Measuring before webfonts land would capture fallback metrics.
            if (document.fonts?.ready) await document.fonts.ready;

            const probe = probeRef.current;
            if (cancelled || !probe) return;

            widths = measureRunes(fontSpecOf(probe));
            runeHeight =
                probe.getBoundingClientRect().height ||
                parseFloat(getComputedStyle(probe).fontSize) * 1.4;

            regenerate();
        };

        void init();

        const onResize = () => {
            window.clearTimeout(timer);
            timer = window.setTimeout(regenerate, RESIZE_DEBOUNCE_MS);
        };

        window.addEventListener('resize', onResize);
        return () => {
            cancelled = true;
            window.clearTimeout(timer);
            window.removeEventListener('resize', onResize);
        };
    }, []);

    return (
        <div id="background" className={styles.backgroundContainer}>
            {/* Off-screen probe: carries the real .rune styling so the canvas
                measures the same font the runes are drawn with. */}
            <div
                ref={probeRef}
                className={styles.rune}
                aria-hidden="true"
                style={{
                    position: 'absolute',
                    top: -9999,
                    left: -9999,
                    visibility: 'hidden',
                    animation: 'none',
                    opacity: 0,
                }}
            >
                ᚠ
            </div>

            {runesData.map((runeData, index) => (
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
                                opacity: 0,
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