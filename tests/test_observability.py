from unittest.mock import patch

import pytest
from fastapi import HTTPException

from agent.db import User
from server.app import create_session, SessionCreate


# Session creation rejects a user whose claimed role differs from the database role.
# A token issued for one session cannot authorize a different session.

def test_bad_role_passed() -> None:
    u = User(id=1, name="Ozzy Osbourne", role="support", store_id=None)

    with patch("server.app.db.get_user") as get_user:
        get_user.return_value = u
        session_body = SessionCreate(user_id=u.id, role="merchant")
        with pytest.raises(HTTPException):
            create_session(session_body)
