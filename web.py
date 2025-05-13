import json
import os
import aiohttp_cors
import aiohttp_jinja2
import bcrypt
import jinja2

from aiohttp import web
from sqlalchemy import func, select, and_

import globals
from orm import Quote, Author, PagePassword
from security import validate_session_token, is_login_blocked, generate_session_token, record_failed_login_attempt


async def start_server():
    app = web.Application()
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("quote_web_ui"))

    app.add_routes([
        web.post('/', submit_through_web),
        web.get('/', redirectToIndex),
        web.get('/index', return_web_page_main),
        web.get('/approve', return_web_page_approve),
        web.post('/approve', approve_through_web),
        web.delete('/approve', delete_through_web),
        web.get('/authors', return_authors_data),
        web.get('/quotes/nomination', return_nominations_data),
        web.get('/login', authenticate_handler),
        web.post('/login', authenticate_handler),
    ])
    app.router.add_static('/static/', path='quote_web_ui/static', name='static', follow_symlinks=True)

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


async def redirectToIndex(_):
    raise web.HTTPFound('/index')


async def return_web_page_main(_):
    return web.FileResponse(path=os.path.abspath('quote_web_ui/index.html'))


async def return_web_page_approve(_):
    return web.FileResponse(path=os.path.abspath('quote_web_ui/approve.html'))


async def return_authors_data(_):
    authors = list(map(lambda a: a.id, globals.session.scalars(select(Author)).all()))
    return web.json_response(
        json.dumps(authors, indent=4, ensure_ascii=False)
    )


async def submit_through_web(request):
    try:
        data = json.loads((await request.json()))

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
    quote_id = json.loads(await (request.json()))['id']
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
    public_paths = ['/login', '/author', '/static', '/quotes/nomination']
    page = request.path.split('/')[-1]

    if not page or any(request.path.startswith(path) for path in public_paths):
        return await handler(request)

    token = request.cookies.get('session_token')
    if not token:
        print(f'No session cookie found for ip {request.remote}')
        return web.HTTPFound(f"/login?next={request.path}")

    user_id = validate_session_token(token, page)
    if not user_id:
        print('Invalid session token for ip {request.remote}')
        resp = web.HTTPFound(f"/login?next={request.path}")
        resp.del_cookie('session_token')
        return resp

    request['user_id'] = user_id

    return await handler(request)


async def authenticate_handler(request):
    page = request.query.get('next', '/index')[1:]

    if request.method == 'POST':
        data = await request.post()
        password = data.get('password', '').encode()
        stored_hash = globals.session.scalars(select(PagePassword).where(PagePassword.page.is_(page))).one_or_none().hash

        ip = request.remote

        if is_login_blocked(ip):
            return web.Response(text="Too many attempts. Try again later.", status=403)

        if stored_hash and bcrypt.checkpw(password, stored_hash.encode()):
            token = generate_session_token(ip, page)

            resp = web.HTTPFound(f"/{page}")
            resp.set_cookie(
                "session_token",
                token,
                httponly=True,
                secure=False,
                samesite="strict",
                max_age=globals.config.login_session_time
            )

            if ip in globals.failed_login_attempts:
                del globals.failed_login_attempts[ip]

            return resp
        else:
            record_failed_login_attempt(ip)
            return aiohttp_jinja2.render_template(
                "login.html",
                request,
                {"message": "Invalid password."}
            )

    return aiohttp_jinja2.render_template("login.html", request, {})
