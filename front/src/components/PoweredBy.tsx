// Author attribution required by the additional terms in ADDITIONAL_TERMS.md
// (GNU AGPL v3.0, section 7(b)). Do not remove it from the user interface.
const SOURCE_URL = 'https://github.com/OlderHermit/discord_quote_bot';

export const PoweredBy = () => (
    <footer className="poweredBy">
        Powered by{' '}
        <a href={SOURCE_URL} target="_blank" rel="noopener noreferrer">discord_quote_bot</a>{' '}
        by OlderHermit · AGPL-3.0
    </footer>
);

export default PoweredBy;
