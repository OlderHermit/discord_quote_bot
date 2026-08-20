import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Sequence

from sqlalchemy import Engine, create_engine, select, update, func, event
from sqlalchemy.orm import Session, sessionmaker, selectinload

from orm import Config, Base, Quote, Author, Sentence


class DatabaseCorrupt(RuntimeError):
    pass

class ValidQuotesMissing(RuntimeError):
    pass



class DBBridge():

    def __init__(self, db_path: Path | str = "quotes.db"):
        self.db_path = Path(db_path).resolve()
        self._check_integrity()

        self.engine: Engine = create_engine(f"sqlite:///{self.db_path}")

        @event.listens_for(self.engine, "connect")
        def _pragmas(dbapi_conn, _record):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=5000")
            cur.close()

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(self.engine, expire_on_commit=False)

    def _check_integrity(self) -> None:
        if not self.db_path.exists():
            return
        with closing(sqlite3.connect(self.db_path)) as conn:
            result = conn.execute("PRAGMA integrity_check").fetchone()
        if result[0] != "ok":
            raise DatabaseCorrupt(result[0])

    # config ===============================================

    def get_config(self) -> Config:
        with self.Session() as session:
            return session.get_one(Config, 0)

    def is_new_quote_time(self) -> bool:
        last_used = self.get_config().last_used.date()
        now = datetime.now(timezone.utc).date()
        return now > last_used

    def update_config_last_used_quote(self, q_id: int) -> None:
        with self.Session() as session, session.begin():
            session.execute(
                update(Config)
                .where(Config.id == 0)
                .values(last_used=datetime.now(timezone.utc), last_quote_id=q_id)
            )

    # quotes ===============================================

    def get_explanation(self) -> str | None:
        with self.Session() as session:
            quote_id = session.get_one(Config, 0).last_quote_id # keeping all in single session
            if quote_id is None:
                return None
            quote = session.get(Quote, quote_id)
            return quote.explanation if quote else None

    def get_random_valid_quote(self) -> Quote:
        selection = (
            select(Quote)
            .options(selectinload(Quote.sentences)
                     .joinedload(Sentence.author)
                     .joinedload(Author.color))
            .where(Quote.used.is_(False), Quote.deleted.is_(False), Quote.confirmed.is_(True))
            .order_by(func.random())
            .limit(1)
        )

        with self.Session() as session, session.begin():
            quote = session.scalars(selection).first()
            if quote is not None:
                return quote

            self._reset_used_quotes(session)
            result = session.scalars(selection).first()
            if not result:
                raise ValidQuotesMissing
            return result

    def get_specific_quote_with_joins(self, q_id) -> Quote:
        with self.Session()  as session:
            return session.scalar(
                select(Quote)
                .options(selectinload(Quote.sentences)
                         .joinedload(Sentence.author)
                         .joinedload(Author.color))
                .where(Quote.id == q_id, Quote.deleted.is_(False), Quote.confirmed.is_(True))
            )

    @staticmethod
    def _reset_used_quotes(session: Session) -> None:
        session.execute(
            update(Quote).where(Quote.used.is_(True)).values(used=False)
        )

    def mark_quote_as_used(self, q_id):
        with self.Session() as session, session.begin():
            session.execute(
                update(Quote).where(Quote.id == q_id).values(used=True)
            )

    def get_authors(self) -> Sequence[Author]:
        with self.Session() as session:
            return session.scalars(select(Author)).all()

    def get_candidate_quotes(self) -> Sequence[Quote]:
        with self.Session() as session:
            return session.scalars(
                select(Quote)
                .options(selectinload(Quote.sentences).joinedload(Sentence.author).joinedload(Author.color))
                .where(Quote.deleted.is_(False), Quote.confirmed.is_(False))
            ).all()

    def approve_quote(self, q_id: int) -> None:
        with self.Session() as session, session.begin():
            session.execute(
                update(Quote)
                .where(Quote.id == q_id, Quote.deleted.is_(False), Quote.confirmed.is_(False))
                .values(confirmed=True)
            )

    def delete_quote(self, q_id: int) -> None:
        with self.Session() as session, session.begin():
            session.execute(
                update(Quote)
                .where(Quote.id == q_id, Quote.deleted.is_(False), Quote.confirmed.is_(False))
                .values(deleted=True)
            )

    def add_submission(
        self,
        quote_date: str,
        explanation: str,
        sentences: list[tuple[str, str]],
    ) -> int:
        with self.Session() as session, session.begin():
            quote = Quote(
                date=quote_date,
                explanation=explanation,
                confirmed=False,
                used=False,
                deleted=False,
            )
            session.add(quote)
            session.flush()          # assigns quote.id

            session.add_all(
                Sentence(
                    number=i,
                    sentence=text,
                    author_id=author_id,
                    quote_id=quote.id,
                )
                for i, (text, author_id) in enumerate(sentences)
            )
        return quote.id