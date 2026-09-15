import sqlite3
from contextlib import closing

import pytest
from fastapi import HTTPException

from server.app import create_session, SessionCreate, _authorize


def test_create_session_rejects_role_mismatch(world) -> None:
    """Session creation rejects a user whose claimed role differs from the database role."""
    with closing(sqlite3.connect(world["db"])) as conn:
        (user_id,) = conn.execute("SELECT id FROM users WHERE role = 'shopper' ORDER BY id LIMIT 1").fetchone()
    session_body_ok = SessionCreate(user_id=user_id, role="shopper")
    session_body_notok = SessionCreate(user_id=user_id, role="merchant")

    ok = create_session(session_body_ok)  # success
    assert "session_id" in ok and "token" in ok

    with pytest.raises(HTTPException) as exc:
        create_session(session_body_notok)
    assert exc.value.status_code == 403


def test_cross_session_token(world) -> None:
    """A token issued for one session cannot authorize a different session."""
    with closing(sqlite3.connect(world["db"])) as conn:
        (user_id, role) = conn.execute("SELECT id, role FROM users ORDER BY id LIMIT 1").fetchone()
    session1 = create_session(SessionCreate(user_id=user_id, role=role))
    session2 = create_session(SessionCreate(user_id=user_id, role=role))

    ctx = _authorize(session1["session_id"], f"Bearer {session1['token']}")  # success
    assert ctx.user_id == user_id

    with pytest.raises(HTTPException) as exc:
        _authorize(session1["session_id"], f"Bearer {session2['token']}")
    assert exc.value.status_code == 403
