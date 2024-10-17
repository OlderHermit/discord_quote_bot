from datetime import datetime
from typing import List

from sqlalchemy import ForeignKey, String, Table, Column, CheckConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


association_table = Table(
    'association_table',
    Base.metadata,
    Column('author_id', ForeignKey('author.id')),
    Column('quote_id', ForeignKey('quote.id')),
)


class Author(Base):
    __tablename__ = 'author'

    id: Mapped[str] = mapped_column(primary_key=True)
    signature: Mapped[str] = mapped_column(String(30))
    color: Mapped['color'] = relationship()

    def __repr__(self) -> str:
        return f'Author(id={self.id}, signature={self.signature}, color={self.color})'


class Quote(Base):
    __tablename__ = 'quote'

    id: Mapped[int] = mapped_column(primary_key=True)
    quote: Mapped[str]
    date: Mapped[str] = mapped_column(default='----')
    explanation: Mapped[str] = mapped_column(default='----')

    confirmed: Mapped[bool] = mapped_column(default=False)
    used: Mapped[bool] = mapped_column(default=False)

    author: Mapped[List[Author]] = relationship(secondary=association_table)

    def __repr__(self) -> str:
        return f'Quote(id={self.id}, quote={self.quote}, date={self.date}, explanation={self.explanation}'


class Color(Base):
    __tablename__ = 'color'

    id: Mapped[int] = mapped_column(primary_key=True)
    red: Mapped[int] = mapped_column(default=255)
    green: Mapped[int] = mapped_column(default=255)
    blue: Mapped[int] = mapped_column(default=255)

    author_id: Mapped[int] = mapped_column(ForeignKey('author.id'))

    CheckConstraint('red >= 0 AND red <= 255', name='check_red_value')
    CheckConstraint('green >= 0 AND green <= 255', name='check_green_value')
    CheckConstraint('blue >= 0 AND blue <= 255', name='check_blue_value')

    def __repr__(self) -> str:
        return f'Color(id={self.id}, red={self.red}, green={self.green}, blue={self.blue}, author={self.author_id}'


class Config(Base):
    __tabename__ = 'config'

    id: Mapped[int] = mapped_column(primary_key=True)
    bot_token: Mapped[str]
    address: Mapped[str]
    port: Mapped[str]
    last_used: Mapped[datetime]

    def __repr__(self) -> str:
        return f'Config(id={self.id}, token=secret last 5 characters{self.bot_token[-5:]}, adress={self.address}:{self.port}, last_used={self.last_used}'
