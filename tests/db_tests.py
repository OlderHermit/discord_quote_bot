from sqlalchemy.orm import Session

from orm import Quote

def test_add_submission(test_bridge):
    qid = test_bridge.add_submission(
        "2024-01-01", "expl", [("hello", "1"), ("world", "2")]
    )
    with Session(test_bridge.engine) as session:
        quote = session.get(Quote, qid)

        assert quote is not None
        assert len(quote.get_authors()) == 2
        assert len(quote.sentences) == 2
        assert quote.confirmed is False
        assert quote.deleted is False

def test_delete_submission(test_bridge):
    candidates = test_bridge.get_candidate_quotes()
    assert candidates, "expected a pending quote to delete"
    q = candidates[0]

    test_bridge.delete_quote(q.id)
    with Session(test_bridge.engine) as session:
        res = session.get(Quote, q.id)
        assert res is not None
        assert res.deleted is True

