import json
import os

import aiohttp_cors
from aiohttp import web
from sqlalchemy import func, select, and_

import globals
from orm import Quote, Author


async def start_server():
    app = web.Application()

    app.add_routes([
        web.post('/', submit_through_web),
        web.post('/approve', approve_through_web),
        web.delete('/approve', delete_through_web),
        web.get('/authors', return_authors_data),
        web.get('/quotes/nomination', return_nominations_data),
    ])

    app.middlewares.append(auth_middleware)

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, globals.config.address, int(globals.config.port))
    await site.start()
    print("website is on")


async def return_authors_data(_):
    authors = list(map(lambda a: a.id, globals.session.scalars(select(Author)).all()))
    return web.json_response(authors)


async def submit_through_web(request):
    try:
        data = (await request.json())

        if type(data['quote']) is not str:
            new_quote = Quote(
                quote='[NEW_SENTENCE]'.join(data['quote']),
                date=data['date'],
                explanation=data['explanation'],
                confirmed=False
            )
            for a in globals.session.scalars(select(Author).where(Author.id.in_(data['author'].split(';')))).all():
                new_quote.authors.append(a)
        else:
            new_quote = Quote(
                quote=data['quote'],
                date=data['date'],
                explanation=data['explanation'],
                confirmed=False
            )
            new_quote.authors.append(
                globals.session.scalars(select(Author).where(Author.id.in_(data['author'].split(';')))).one()
            )

        globals.session.add(new_quote)
        globals.session.commit()

        return web.json_response({'status': 'success', 'message': 'Quote added to DB'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)


async def check_if_quote_exists_for_web(request):
    quote_id = (await request.json())['id']
    if quote_id is None:
        raise ValueError("quote_id couldn't be read from request")

    candidate = (globals.session.execute(
        select(Quote)
        .where(Quote.id.is_(quote_id))
        .where(and_(Quote.confirmed.is_(False), Quote.confirmed.is_(False)))
    ).scalar_one_or_none())

    if candidate is None:
        raise IndexError('There was no quote for given id')

    return candidate


async def approve_through_web(request):
    try:
        candidate = await check_if_quote_exists_for_web(request)
        candidate.confirmed = True
        globals.session.commit()
        return web.json_response({'status': 'success', 'message': 'Quote approved'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)


async def delete_through_web(request):
    try:
        candidate = await check_if_quote_exists_for_web(request)
        candidate.deleted = True
        globals.session.commit()
        return web.json_response({'status': 'success', 'message': 'Quote discarded'})
    except Exception as e:
        return web.json_response({'status': 'error', 'message': str(e)}, status=500)


async def return_nominations_data(_):
    quotes_to_accept = list(map(lambda q: (q[0].as_dict(), q[1]),
                                globals.session.execute(
                                    select(Quote, func.group_concat(Author.id, ', ').label("authors"))
                                    .join(Quote.authors)
                                    .where(Quote.confirmed.is_(False))
                                    .where(Quote.deleted.is_(False))
                                    .group_by(Quote.id)
                                ).all()))
    return web.json_response(
        quotes_to_accept
    )


@web.middleware
async def auth_middleware(request, handler):
    token = request.headers.get('x-api-key')

    if not token:
        print(f'No api key found for ip {request.remote}')
        return web.HTTPUnauthorized()
    if token != os.getenv('API_KEY'):
        print(f'Invalid api key for ip {request.remote}')
        return web.HTTPUnauthorized()

    return await handler(request)
