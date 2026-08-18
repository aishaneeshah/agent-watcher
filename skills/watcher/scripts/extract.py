#!/usr/bin/env python3
"""
CLI: extract recent transcript turns for the current session.

Usage:
    python3 extract.py [--session-id ID] [--harness NAME] [--last N]

Output: one line per turn, format:
    USER: <text truncated to 500 chars>
    ASSISTANT: <text truncated to 500 chars>

Exit codes:
    0  success
    1  transcript not found or harness error
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import extractors


TRUNCATE = 500


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--harness", default=os.environ.get("WATCHER_HARNESS"))
    parser.add_argument("--last", type=int, default=20)
    args = parser.parse_args()

    try:
        extractor = extractors.get(args.harness) if args.harness else extractors.auto_detect()
    except (ValueError, RuntimeError) as e:
        print(f"WATCHER_EXTRACT_ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    session_id = args.session_id or extractor.detect_session_id()

    try:
        turns = extractor.get_recent_turns(session_id=session_id, n=args.last)
    except FileNotFoundError as e:
        print(f"WATCHER_EXTRACT_ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    for turn in turns:
        text = turn.text
        if len(text) > TRUNCATE:
            text = text[:TRUNCATE] + "...[truncated]"
        print(f"{turn.role.upper()}: {text}")


if __name__ == "__main__":
    main()
