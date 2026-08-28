import argparse
from pathlib import Path

from src.pipeline import team_tasks


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape the full team roster and update the seeded teams CSV.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Reconcile the existing data/raw/teams/teams_latest.csv without re-scraping or touching backend/seed_data/teams.csv.",
    )
    args = parser.parse_args()

    if args.dry_run:
        raw_path = team_tasks.RAW_TEAMS_LATEST_PATH
        if not raw_path.exists():
            raise FileNotFoundError(f"No raw team file found at {raw_path} - run without --dry-run first.")
        print(f"Dry run: reconciling existing {raw_path}")
        output_path = team_tasks.reconcile_teams_csv(raw_path, output_path=Path("data/processed/teams_reconciled.csv"))
        print(f"Dry run output written to {output_path} ({team_tasks.SEED_TEAMS_PATH} untouched)")
        return

    raw_path = team_tasks.scrape_teams()
    print(f"Scraped teams written to {raw_path}")

    output_path = team_tasks.reconcile_teams_csv(raw_path)
    print(f"Updated {output_path}")


if __name__ == "__main__":
    main()
