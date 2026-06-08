"""Backward-compatible entrypoint for the platform crawler.

The old implementation used an LLM-based "agent" cleaner. The production
pipeline is now deterministic: curated URLs from crawl_sources/urls.json,
requests/PDF extraction, rule-based Markdown cleaners, then quality gate.
"""

import argparse
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from run_crawler import GreenSMCrawler


def print_agent_step(step_name: str, message: str = "") -> None:
    print(f"\n[AGENT_STEP] {step_name}", flush=True)
    if message:
        print(f"[INFO] {message}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Green SM deterministic Platform/PDF crawler")
    parser.add_argument("--max-urls", type=int, default=0, help="Max URLs to crawl; 0 means all enabled URLs")
    parser.add_argument("--sources", type=str, default="platform,platform_pdf", help="Comma-separated source profiles")
    parser.add_argument("--categories", type=str, default="", help="Comma-separated categories")
    args = parser.parse_args()

    source_profiles = [item.strip() for item in args.sources.split(",") if item.strip()]
    categories = [item.strip() for item in args.categories.split(",") if item.strip()] or None

    print_agent_step("Registry", "Loading curated URLs from crawl_sources. URL auto-discovery is disabled.")
    print_agent_step("Crawl", "Running deterministic requests/PDF crawler. No LLM or Agent API calls are used.")
    GreenSMCrawler(
        max_urls=args.max_urls,
        source_profiles=source_profiles,
        categories=categories,
    ).run()
    print_agent_step("Complete", "Deterministic Platform/PDF crawl completed.")


if __name__ == "__main__":
    main()
