#!/usr/bin/env python3
"""Prepare the encrypted payload and helper secrets in a single step."""

from __future__ import annotations

import argparse
import base64
import getpass
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        cmd,
        check=True,
        capture_output=capture,
    )


def key_exists(recipient: str) -> bool:
    try:
        subprocess.run(
            ["gpg", "--batch", "--list-secret-keys", recipient],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def generate_key(recipient: str, passphrase: str, expire: str) -> None:
    print(f"[setup] Generating GPG key for '{recipient}'", flush=True)
    run(
        [
            "gpg",
            "--batch",
            "--passphrase",
            passphrase,
            "--pinentry-mode",
            "loopback",
            "--quick-gen-key",
            recipient,
            "rsa4096",
            "sign,encrypt",
            expire,
        ]
    )


def export_secret_key(recipient: str) -> None:
    print("[setup] Exporting private key artefacts", flush=True)
    secret = run(
        ["gpg", "--armor", "--export-secret-keys", recipient],
        capture=True,
    ).stdout

    asc_path = Path("private-key.asc")
    asc_b64_path = Path("private-key.asc.b64")

    asc_path.write_bytes(secret)
    asc_b64_path.write_text(base64.b64encode(secret).decode("ascii"))

    print(f"[setup] Wrote {asc_path} and {asc_b64_path}", flush=True)


def encrypt_strategy(recipient: str, source: Path, output: Path) -> None:
    if not source.exists():
        raise SystemExit(f"{source} not found. Create or decrypt your strategy first.")

    print(f"[setup] Encrypting {source} → {output}", flush=True)
    run(
        [
            "gpg",
            "--batch",
            "--yes",
            "--output",
            str(output),
            "--encrypt",
            "--recipient",
            recipient,
            str(source),
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate/refresh the encrypted strategy payload."
    )
    # Try to get PLAYER_NAME from environment or positional argument
    player_name = os.getenv("PLAYER_NAME", "").strip()
    parser.add_argument(
        "player_name",
        nargs="?",
        default=player_name,
        help="Player name to use as GPG key identity (defaults to PLAYER_NAME from environment).",
    )
    parser.add_argument(
        "--recipient",
        help="GPG identity to use (overrides player_name if provided).",
    )
    parser.add_argument(
        "--expire",
        default="1y",
        help="GPG key expiry (default: 1y). Ignored if the key already exists.",
    )
    parser.add_argument(
        "--source",
        default="strategy.py",
        type=Path,
        help="Plaintext strategy file.",
    )
    parser.add_argument(
        "--output",
        default="strategy.py.gpg",
        type=Path,
        help="Encrypted output file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # Use --recipient if provided, otherwise use player_name positional arg
    recipient = args.recipient or args.player_name
    
    if not recipient:
        raise SystemExit(
            "GPG recipient name required. Either:\n"
            "  • Set PLAYER_NAME environment variable, or\n"
            "  • Pass player name as argument: python scripts/setup_encryption.py 'Your Player Name'"
        )

    passphrase = getpass.getpass("GPG passphrase (for new key or future reference): ")
    if not passphrase:
        raise SystemExit("Passphrase cannot be empty.")

    if not key_exists(recipient):
        generate_key(recipient, passphrase, args.expire)
    else:
        print(f"[setup] Reusing existing GPG key '{recipient}'", flush=True)

    encrypt_strategy(recipient, args.source, args.output)
    export_secret_key(recipient)

    print(
        "\nNext steps:\n"
        "  • Add private-key.asc.b64 to repo secret GPG_PRIVATE_KEY_B64\n"
        "  • Store the passphrase you just entered in GPG_PASSPHRASE\n"
        "  • Delete private-key.asc and private-key.asc.b64 after copying\n",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(exc.stderr.decode() if exc.stderr else str(exc))
        sys.exit(exc.returncode)

