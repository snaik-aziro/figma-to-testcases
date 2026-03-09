"""CLI to run the evaluator against PRD and tests JSON files."""

import argparse
import json
import sys

from app.services import Evaluator


def load_json(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prd', required=True, help='Path to PRD JSON')
    parser.add_argument('--tests', required=True, help='Path to generated tests JSON')
    parser.add_argument('--prefer-premium', action='store_true', help='Try premium model first')
    parser.add_argument('--screen', required=False, help='Path to selected screen JSON (optional)')
    args = parser.parse_args()

    try:
        prd = load_json(args.prd)
    except Exception as e:
        print(f"Failed to load PRD: {e}")
        sys.exit(1)

    try:
        tests = load_json(args.tests)
    except Exception as e:
        print(f"Failed to load tests: {e}")
        sys.exit(1)

    evaluator = Evaluator.with_fallback()
    screen = None
    if args.screen:
        try:
            screen = load_json(args.screen)
        except Exception as e:
            print(f"Failed to load screen JSON: {e}")
            sys.exit(1)

    result = evaluator.evaluate(prd, tests, screen=screen, prefer_premium=args.prefer_premium)

    metrics = result.get('metrics') if isinstance(result, dict) else None
    print(json.dumps(metrics if metrics else result, indent=2))


if __name__ == '__main__':
    main()
