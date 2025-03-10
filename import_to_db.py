import json

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from orm import Base, Config, Author, Color, Quote

engine = create_engine("sqlite:///quotes.db")
Base.metadata.create_all(engine)
session = Session(engine)

session.add(
    Config(
        id=0,
        bot_token='',
        address='',
        port='',
        last_used=1,
        last_quote_id=None
    )
)
session.commit()

with open('jsons\\quotes.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

for e in data['authors']:

    author = Author(
        id=data['authors'][e]['author'],
        signature=data['authors'][e]['signature']
    )

    color_tuple = data['authors'][e]['color'].split(' ')
    color = Color(
        red=color_tuple[0],
        green=color_tuple[1],
        blue=color_tuple[2],
    )

    author.color = color
    session.add(author)
    session.commit()

for e in data['quotes']:

    quote = None
    if type(e['quote']) is not str:
        quote = Quote(
            quote='[NEW_SENTENCE]'.join(e['quote']),
            date=e['date'],
            explanation=e['explanation'],
            confirmed=True
        )
    else:
        quote = Quote(
            quote=e['quote'],
            date=e['date'],
            explanation=e['explanation'],
            confirmed=True
        )
    for a in session.query(Author).filter(Author.id.in_(e['author'].split(';'))).all():
        quote.authors.append(a)

    session.add(quote)
    session.commit()

session.commit()
session.close()
