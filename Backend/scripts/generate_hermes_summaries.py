"""
Generate Hermes daily summaries for all children (cron-friendly).

The app has no in-process cron; run this script from system cron / n8n.

Usage:
    venv/bin/python scripts/generate_hermes_summaries.py                     # today (server time)
    venv/bin/python scripts/generate_hermes_summaries.py --date 2026-10-21
    venv/bin/python scripts/generate_hermes_summaries.py --child-id child_xxx --date 2026-10-21

Cron example (nightly at 21:00):
    0 21 * * * cd /path/to/MENTOR-AI-onlyapi && venv/bin/python scripts/generate_hermes_summaries.py >> logs/hermes_summaries.log 2>&1

Notes:
- Idempotent: children with an existing summary for the date are skipped.
- Set HERMES_MOCK=true for a dry run with zero Gemini calls.
- Requires GOOGLE_API_KEY and Firebase credentials in .env.

Author: Mentor AI Team
Version: 1.0.0
"""

import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime

# Add project root to Python path (convention used across scripts/)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Generate Hermes daily summaries")
    parser.add_argument(
        "--date",
        default=None,
        help="YYYY-MM-DD (default: today, server time)",
    )
    parser.add_argument(
        "--child-id",
        default=None,
        help="Generate for one child only (default: all children)",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    if os.getenv("HERMES_MOCK", "false").lower() == "true":
        logger.info("HERMES_MOCK=true — running with canned responses, no Gemini calls")

    from services.hermes_summary_service import HermesSummaryService

    service = HermesSummaryService()

    if args.child_id:
        result = await service.generate(args.child_id, date_str)
        logger.info(
            f"Summary for {args.child_id} on {date_str}: "
            f"quiet_day={result.quiet_day}, mock={result.mock}"
        )
        print({"generated": 1, "child_id": args.child_id, "quiet_day": result.quiet_day})
        return 0

    stats = await service.generate_for_all_children(date_str)
    logger.info(f"Batch complete for {date_str}: {stats}")
    print(stats)
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        logger.exception("Summary generation failed")
        sys.exit(1)
