"""Route-level transaction handling.

The commit must happen **before** the response is handed to the server. A plain
HTTP middleware commits after ``call_next`` returns, but by then the response has
already started streaming to the client, so an immediate follow-up read can see
the old committed state. Wrapping the route handler keeps the commit inside the
request cycle and before any bytes leave the process.
"""
from __future__ import annotations

from fastapi import Request, Response
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session


class TransactionRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request: Request) -> Response:
            db: Session | None = getattr(request.state, "db", None)
            if db is None:
                return await original(request)
            try:
                response = await original(request)
            except Exception:
                db.rollback()
                raise
            if response.status_code < 400:
                db.commit()
            else:
                db.rollback()
            return response

        return handler
