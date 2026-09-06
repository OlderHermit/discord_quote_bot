import datetime
import os

import jwt
import pytest
from sqlalchemy.orm import Session

import context
from orm import Quote
from tests.conftest import test_bridge
from web import create_app


@pytest.fixture
async def client(test_bridge, aiohttp_client):
    context.db = test_bridge
    app = await create_app()
    return await aiohttp_client(app)

async def _login(client, role = 'user'):
    resp = await client.post('/login', json = {"password": os.getenv('USER_PASS') if role == 'user' else os.getenv('MASTER_PASS')})

    return resp.cookies.get('token').value

async def test_login(client):
    token = await _login(client)

    assert token is not None
    assert token != ''

    decoded = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms=['HS256'])

    assert decoded.get('role') == 'user'
    assert decoded.get('exp') > datetime.datetime.now(datetime.UTC).timestamp()

async def test_empty_token(client):
    resp = await client.get("/authors")
    assert resp.status == 401

async def test_invalid_login(client):
    resp = await client.post('/login', json = {"password": "not a password"})
    assert resp.status == 401

async def test_invalid_login_token(client):
    token = jwt.encode({
        "role": 'user',
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)
    }, 'NOT A VALID SECRET', algorithm="HS256")
    resp = await client.get("/authors", cookies={'token': token})
    assert resp.status == 401

async def test_expired_token(client):
    token = jwt.encode({
        "role": 'user',
        "exp": datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1)
    }, os.getenv('SECRET_KEY'), algorithm="HS256")
    resp = await client.get("/authors", cookies={'token': token})
    assert resp.status == 401

async def test_master_lock(client):
    token = await _login(client)
    resp = await client.post('/quotes/approve', cookies={'token': token}, json = {"id": 0})
    assert resp.status == 403

async def test_authors_endpoint(client):
    token = await _login(client)
    resp = await client.get("/authors", cookies={'token': token})

    assert resp.status == 200
    assert len(await resp.json()) > 0


async def test_quote_nominations(client):
    token = await _login(client, 'master')
    resp = await client.get("/quotes/nominations", cookies={'token': token})
    assert resp.status == 200

    nominations = await resp.json()
    nominations_len = len(nominations)
    assert nominations_len > 0

async def test_web_approve(client, test_bridge):
    candidates = test_bridge.get_candidate_quotes()
    q = candidates[0]

    token = await _login(client, 'master')
    resp = await client.post("/quotes/approve", cookies={'token': token}, json={'id': q.id})
    assert resp.status == 200

    with Session(test_bridge.engine) as session:
        quote = session.get(Quote, q.id)

        assert quote is not None
        assert quote.confirmed is True

async def test_web_delete(client, test_bridge):
    candidates = test_bridge.get_candidate_quotes()
    q = candidates[0]

    token = await _login(client, 'master')
    resp = await client.delete("/quotes/approve", cookies={'token': token}, json={'id': q.id})
    assert resp.status == 200

    with Session(test_bridge.engine) as session:
        quote = session.get(Quote, q.id)

        assert quote is not None
        assert quote.deleted is True
        assert quote.confirmed is False

async def test_post_quote_valid(client, test_bridge):
    token = await _login(client)
    payload = {
        "date": "2005-05-19",
        "explanation": "Context for why this is funny",
        "sentences": [
            {"sentence": "Hello there.", "author": "1"},
            {"sentence": "General Kenobi.", "author": "2"},
        ],
    }
    resp = await client.post("/quotes", json=payload, cookies={'token': token})

    assert resp.status == 200

    candidates = test_bridge.get_candidate_quotes()
    assert (await resp.json()).get('id') in (q.id for q in candidates)

async def test_post_quote_no_sentences(client, test_bridge):
    token = await _login(client)
    payload = {
        "date": "-----",
        "explanation": "Why would anyone put context here?",
        "sentences": [],
    }
    resp = await client.post("/quotes", json=payload, cookies={'token': token})

    assert resp.status == 400

async def test_post_quote_invalid_author(client, test_bridge):
    token = await _login(client)
    payload = {
        "date": "-----",
        "explanation": ":>",
        "sentences": [
            {"sentence": "I like trains", "author": "999"},
        ],
    }
    resp = await client.post("/quotes", json=payload, cookies={'token': token})

    assert resp.status == 400