import asyncio
import datetime
import json
import os
import secrets

import aiohttp_cors
import jwt
from aiohttp import web
from sqlalchemy.exc import IntegrityError

import context

async def start_server() -> web.AppRunner:
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
    site = web.TCPSite(runner, os.getenv("LOCAL_ADDRESS"), int(os.getenv("LOCAL_PORT")))
    await site.start()
    print("website is on")
    return runner


async def return_authors_data(_):
    authors = [a.id for a in context.db.get_authors()]
    return web.json_response(authors)

async def submit_through_web(request):
    try:
        data = (await request.json())
        quote_date = data["date"]
        explanation = data["explanation"]
        sentences = [
            (s["sentence"], s["author"]) for s in data["sentences"]
        ]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return web.json_response(
            {"status": "error", "message": "Invalid payload"}, status=400
        )

    if not sentences:
        return web.json_response(
            {"status": "error", "message": "At least one sentence required"},
            status=400,
        )

    try:
        quote_id = await asyncio.to_thread(
            context.db.add_submission, quote_date, explanation, sentences
        )
    except IntegrityError:
        return web.json_response(
            {"status": "error", "message": "Unknown author"}, status=400
        )
    except Exception:
        # log.exception("submit failed")
        return web.json_response(
            {"status": "error", "message": "Internal error"}, status=500
        )

    return web.json_response({"status": "success", "id": quote_id})


async def approve_through_web(request):
    try:
        quote_id = (await request.json())['id']
        await asyncio.to_thread(context.db.approve_quote, quote_id)
        return web.json_response({'status': 'success', 'message': 'Quote approved'})
    except Exception as e:
        print(f"Submit error: {e}")  # albo logger
        return web.json_response({'status': 'error', 'message': 'Internal error'}, status=500)


async def delete_through_web(request):
    try:
        quote_id = (await request.json())['id']
        await asyncio.to_thread(context.db.delete_quote, quote_id)
        return web.json_response({'status': 'success', 'message': 'Quote discarded'})
    except Exception as e:
        print(f"Submit error: {e}")  # albo logger
        return web.json_response({'status': 'error', 'message': 'Internal error'}, status=500)


async def return_nominations_data(_):
    return web.json_response(
        [q.as_dict() for q in await asyncio.to_thread(context.db.get_candidate_quotes)]
    )


async def login(request):
    try:
        data = (await request.json())
        password = data.get("password")

        if not isinstance(password, str) or len(password) <= 0:
            return web.json_response({"error": "password invalid format" }, status=400)

        if secrets.compare_digest(password, os.getenv('MASTER_PASS')):
            role = "master"
        elif secrets.compare_digest(password, os.getenv('USER_PASS')):
            role = "user"
        else:
            return web.json_response({"error": "Invalid password"}, status=401)

        token = jwt.encode({
            "role": role,
            "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
        }, os.getenv('SECRET_KEY'), algorithm="HS256")

        resp = web.json_response({'message': 'Login successful', 'role': role})
        resp.set_cookie(
            'token',
            token,
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=3600
        )
        return resp
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)


async def check_token(request):
    return web.json_response({'role': request['jwt'].get('role')})


@web.middleware
async def auth_middleware(request, handler):
    if request.path == "/login" or request.method == "OPTIONS":
        return handler(request)

    token = request.cookies.get('token')
    if not token:
        print(f"No or invalid Authorization header from ip {request.remote}")
        return web.json_response({'message': 'Missing or invalid Authorization header'}, status=401)

    try:
        payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=["HS256"])
        request['jwt'] = payload
    except jwt.ExpiredSignatureError:
        print(f"Expired token from ip {request.remote}")
        return web.json_response({'message': 'Token expired'}, status=401)
    except jwt.InvalidTokenError:
        print(f"Invalid token from ip {request.remote}")
        return web.json_response({'message': 'Invalid token'}, status=401)
    except Exception as e:
        return web.json_response({'message': f'Internal server error {e}'}, status=500)

    if request.path == "/quotes/approve" and payload.get("role") != "master":
        return web.json_response({'message': 'You do not have permission to access this resource'}, status=403)

    return handler(request)
