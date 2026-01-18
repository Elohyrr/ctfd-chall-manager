"""
This module defines decorators used by API endpoints.
"""

import functools

from CTFd.models import Challenges
from CTFd.utils.user import is_admin
from flask import request
from flask_restx import abort
from sqlalchemy.sql import and_


def challenge_visible(func):
    """
    This decorator abort the request if the challenge is not visible.
    The request is NOT abort if the user is admin.
    GitOps mode: accepts both CTFd ID and scenario as challengeId.
    """

    @functools.wraps(func)
    def _challenge_visible(*args, **kwargs):
        from CTFd.plugins.ctfd_chall_manager.models import DynamicIaCChallenge
        
        # Get challengeId from query string
        challenge_id = request.args.get("challengeId")

        if not challenge_id:
            data = request.get_json()
            if data:
                challenge_id = data.get("challengeId")

        if not challenge_id:
            abort(400, "missing args", success=False)

        # GitOps mode: try to find challenge by scenario first, then by ID
        challenge = None
        
        # Try by scenario (for GitOps workflow)
        challenge = DynamicIaCChallenge.query.filter(
            DynamicIaCChallenge.scenario == challenge_id
        ).first()
        
        # Fallback: try by ID (original behavior)
        if not challenge:
            challenge = Challenges.query.filter(Challenges.id == challenge_id).first()

        if is_admin():
            if not challenge:
                abort(404, "no such challenge", success=False)
        else:
            if not challenge or challenge.state == "hidden" or challenge.state == "locked":
                abort(403, "challenge not visible", success=False)
        return func(*args, **kwargs)

    return _challenge_visible
