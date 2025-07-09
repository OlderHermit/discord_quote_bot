import os

import aiohttp_cors
import jwt
from aiohttp import web
from sqlalchemy import select, and_

import globals
from orm import Quote, Author, Sentence


async def start_server():
    app = web.Application()

    app.add_routes([
        web.post('/quotes', submit_through_web),
        web.post('/quotes/approve', approve_through_web),
        web.delete('/quotes/approve', delete_through_web),
        web.get('/quotes/nominations', return_nominations_data),
        web.get('/authors', return_authors_data),
        web.post('/login', login),
        web.get('/login/check', check_token),
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

        new_quote = Quote(
            date=data['date'],
            explanation=data['explanation'],
            confirmed=False
        )
        globals.session.add(new_quote)
        globals.session.flush()

        for i, sentence in enumerate(data['sentences']):
            new_sentence = Sentence(
                number=i,
                sentence=sentence['sentence'],
                author_id=sentence['author'],
                quote_id=new_quote.id,
            )
            globals.session.add(new_sentence)

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
        .where(and_(Quote.confirmed.is_(False), Quote.deleted.is_(False)))
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
    quotes_to_accept = list(map(lambda q: (q[0].as_dict()),
                                globals.session.execute(
                                    select(Quote)
                                    .join(Sentence)
                                    .where(Quote.confirmed.is_(False))
                                    .where(Quote.deleted.is_(False))
                                    .group_by(Quote.id)
                                ).all()))
    return web.json_response(
        quotes_to_accept
    )


async def login(request):
    try:
        data = await request.json()
        password = data.get("password")

        if password == os.getenv('MASTER_PASS'):
            role = "master"
        elif password == os.getenv('USER_PASS'):
            role = "user"
        else:
            return web.json_response({"error": "Invalid password"}, status=401)

        token = jwt.encode({"role": role}, os.getenv('SECRET_KEY'), algorithm="HS256")

        resp = web.json_response({'message': 'Login successful', 'token': token}, status=200)
        resp.set_cookie(
            'token',
            token,
            httponly=True,
            secure=False,
            samesite='Strict',
            max_age=3600
        )
        return resp
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)


async def check_token(request):
    return web.json_response({'message': 'Token valid', 'token': request.cookies.get('token')}, status=200)


@web.middleware
async def auth_middleware(request, handler):
    if request.path == "/login" or request.method == "OPTIONS":
        return await handler(request)

    token = request.cookies.get('token')
    if not token:
        print(f"No or invalid Authorization header from ip {request.remote}")
        return web.json_response({'message': 'Missing or invalid Authorization header'}, status=401)

    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        print(f"Expired token from ip {request.remote}")
        return web.json_response({'message': 'Token expired'}, status=401)
    except jwt.InvalidTokenError:
        print(f"Invalid token from ip {request.remote}")
        return web.json_response({'message': 'Invalid token'}, status=401)
    except Exception as e:
        return web.json_response({'message': f'Internal server error {e}'}, status=500)

    if request.path == "quote/approve" and payload.get("role") != "master":
        return web.json_response({'message': 'You do not have permission to access this resource'}, status=403)

    return await handler(request)
