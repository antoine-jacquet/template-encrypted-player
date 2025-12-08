#!/usr/bin/env python3
"""Register this encrypted template player with the penalty shootout server."""

import os
from typing import Dict, Any

import requests


PLAYER_NAME = os.getenv("PLAYER_NAME", "encrypted-template").strip()


def main() -> None:
    server_url = os.getenv("SERVER_URL", "").strip()
    github_token = os.getenv("GAME_TOKEN", "").strip()
    github_repo = os.getenv("GITHUB_REPOSITORY", os.getenv("GITHUB_REPO", "")).strip()

    print(
        f"[register] Config state: SERVER_URL={'set' if server_url else 'missing'}, "
        f"GAME_TOKEN={'set' if github_token else 'missing'}, "
        f"PLAYER_NAME={'set' if PLAYER_NAME else 'missing'}, "
        f"GITHUB_REPO={'set' if github_repo else 'missing'}",
        flush=True,
    )

    if not server_url:
        raise SystemExit("SERVER_URL environment variable not set")
    if not github_token:
        raise SystemExit("GAME_TOKEN environment variable not set")
    if not PLAYER_NAME:
        raise SystemExit("PLAYER_NAME environment variable not set")
    if not github_repo:
        raise SystemExit("GITHUB_REPO or GITHUB_REPOSITORY environment variable not set")

    if not server_url.startswith(("http://", "https://")):
        raise SystemExit(f"SERVER_URL must include scheme (http/https); got '{server_url}'")

    server_url = server_url.rstrip("/")
    print(f"[register] Using endpoint {server_url}/register", flush=True)
    print(f"[register] Configuring auto-trigger for repo: {github_repo}", flush=True)
    print("[register] Using GAME_TOKEN for both authentication and workflow triggering", flush=True)

    try:
        response = requests.post(
            f"{server_url}/register",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {github_token}",
            },
            json={"player_name": PLAYER_NAME, "github_repo": github_repo},
            timeout=10,
        )
    except Exception as exc:  # pragma: no cover
        raise SystemExit(f"Registration error: {exc}") from exc

    if not response.ok:
        raise SystemExit(f"Registration failed: {response.status_code} {response.text}")

    try:
        payload: Dict[str, Any] = response.json()
    except ValueError:
        print("Registration succeeded but response was not JSON.")
        return

    status = (payload.get("status") or "").lower()
    if status == "registered":
        print(f"Player '{payload.get('player_name')}' registered with id {payload.get('player_id')}.")
        print(f"✅ Auto-trigger configured for repo: {github_repo}")
    elif status == "already_registered":
        print(
            f"Player '{payload.get('player_name')}' already registered. "
            f"Using id {payload.get('player_id')}."
        )
    else:
        print(f"Registration response: {payload}")


if __name__ == "__main__":
    main()

