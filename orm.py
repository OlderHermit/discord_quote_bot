from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, String, Table, Column, CheckConstraint, TypeDecorator, Integer, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session


class Base(DeclarativeBase):
    pass


class Timestamp(TypeDecorator):
    impl = Integer

    def process_bind_param(self, value, dialect):
        if isinstance(value, datetime):
            return int(value.timestamp())
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return datetime.fromtimestamp(value)
        return value


class Sentence(Base):
    __tablename__ = 'sentence'

    number: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[str] = mapped_column(ForeignKey('author.id'), primary_key=True)
    quote_id: Mapped[int] = mapped_column(ForeignKey('quote.id'), primary_key=True)
    sentence: Mapped[str] = mapped_column(String(200))

    quote: Mapped['Quote'] = relationship(back_populates='sentences')
    author: Mapped['Author'] = relationship()



class Author(Base):
    __tablename__ = 'author'

    id: Mapped[str] = mapped_column(primary_key=True)
    signature: Mapped[str] = mapped_column(String(30))
    color: Mapped['Color'] = relationship()

    def __repr__(self) -> str:
        return f'Author(id={self.id}, signature={self.signature}, color={self.color})'

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Quote(Base):
    __tablename__ = 'quote'

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[str] = mapped_column(default='----')
    explanation: Mapped[str] = mapped_column(default='----')

    confirmed: Mapped[bool] = mapped_column(default=False)
    used: Mapped[bool] = mapped_column(default=False)
    deleted: Mapped[bool] = mapped_column(default=False)

    sentences: Mapped[List[Sentence]] = relationship(back_populates='quote')

    def __repr__(self) -> str:
        return f'Quote(id={self.id}, quote={self.sentences}, date={self.date}, explanation={self.explanation}, author={self.get_authors()}'

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def get_authors(self) -> List[Author]:
        return list({s.author.id: s.author for s in self.sentences if s.author is not None}.values())


class Color(Base):
    __tablename__ = 'color'

    id: Mapped[int] = mapped_column(primary_key=True)
    red: Mapped[int] = mapped_column(default=255)
    green: Mapped[int] = mapped_column(default=255)
    blue: Mapped[int] = mapped_column(default=255)

    author_id: Mapped[str] = mapped_column(ForeignKey('author.id'), nullable=True)

    CheckConstraint('red >= 0 AND red <= 255', name='check_red_value')
    CheckConstraint('green >= 0 AND green <= 255', name='check_green_value')
    CheckConstraint('blue >= 0 AND blue <= 255', name='check_blue_value')

    def __repr__(self) -> str:
        return f'Color(id={self.id}, red={self.red}, green={self.green}, blue={self.blue}, author={self.author_id}'


class Config(Base):
    __tablename__ = 'config'

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_token: Mapped[str]
    address: Mapped[str]
    port: Mapped[str]
    max_login_attempts: Mapped[int]
    login_failed_timeout: Mapped[int]  # in seconds
    login_session_time: Mapped[int]  # in seconds
    last_used: Mapped[datetime] = mapped_column(Timestamp)
    last_quote_id: Mapped[int] = mapped_column(ForeignKey('quote.id'), nullable=True)

    def __repr__(self) -> str:
        return f'Config(id={self.id}, token=secret last 5 characters{self.bot_token[-5:]}, adress={self.address}:{self.port}, last_used={self.last_used}'
