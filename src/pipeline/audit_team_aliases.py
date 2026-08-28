"""Finds teams the raw scrape calls by more than one name, for human review before
adding entries to src/utils/team_aliases.py's TEAM_NAME_ALIASES.

Background: the belt algorithm (src/cinturao_algorithm/cinturao.py) is a linear walk
that matches a champion's *name* to their next game by name equality. If one real team
shows up under two different raw labels across the scraped history (a rename, a
short-label-vs-full-name split, a typo the source site never fixed), the algorithm
sees two different teams and the reconstructed title-succession chain silently
fragments. Two such splits (Locomotiva FA/América Locomotiva, T-Rex/Timbó Rex) were
found incidentally - one test failure and one manual diff review - before this script
existed. This automates finding the rest.

Method: every raw game row scraped since 2026-08-25 carries the team-page URL each
side linked to (Mandante URL/Visitante URL columns - see GamesScrapper.__get_team_url
in src/scrapping/scrape_games/scrapper.py). That URL's slug is a stable ID for a team
that survives a display-name change, unlike the display name itself. Grouping every
appearance by slug and checking for more than one distinct label is a direct,
non-fuzzy way to detect a name split - no string-similarity heuristics involved.

What this script does NOT do, and why that matters: it only detects splits within one
slug (one site page). It cannot tell you that two DIFFERENT team pages are actually
the same real-world team across time (e.g. a club that got a new site page after a
merger or rebrand) - that requires human knowledge the URL can't provide. When a human
supplies that kind of cross-slug merge, verify it against check_self_play_clashes()
below before trusting it: if the two labels ever played each other in the raw data,
they were provably separate opponents at some point, not one team under two names, and
merging them would turn a real historical game into a team playing itself. This is
exactly what happened during the 2026-08-26 review - see docs/DATA_PIPELINE.md's "Team
name slug audit" section for the six cross-slug merges that were proposed, checked,
and deliberately rejected for this reason (and the note at the bottom of
team_aliases.py for the same list with dates/game counts).

Usage:
    python -m src.pipeline.audit_team_aliases
    python -m src.pipeline.audit_team_aliases --raw-dir data/raw/games --json out.json

The output is a report for a human to read, categorized into "already covered by
TEAM_NAME_ALIASES" and "not yet covered" - it never writes to team_aliases.py itself.
Applying a finding is a deliberate, reviewed edit to that file, not something this
script should do automatically (see docs/DATA_PIPELINE.md for why: several
auto-detected candidates needed the self-play check above to catch that they were
wrong before being applied).
"""

import argparse
import json
from pathlib import Path
from typing import Optional

import pandas as pd

from src.utils.team_aliases import TEAM_NAME_ALIASES, extract_team_slug

RAW_GAMES_DIR = Path("data/raw/games")


def _read_raw_games(raw_dir: Path) -> pd.DataFrame:
    files = sorted(p for p in raw_dir.glob("*.csv") if "games" in p.name)
    if not files:
        raise ValueError(f"No raw games files found under {raw_dir}")
    return pd.concat((pd.read_csv(f) for f in files), ignore_index=True)


def find_split_teams(raw_dir: Path = RAW_GAMES_DIR) -> dict:
    """Groups every team appearance by team-page slug and returns every slug used
    under more than one raw label, split into already-aliased vs. new findings."""
    df = _read_raw_games(raw_dir)

    home = df[["Data", "Mandante", "Mandante URL"]].rename(
        columns={"Mandante": "Label", "Mandante URL": "URL"}
    )
    away = df[["Data", "Visitante", "Visitante URL"]].rename(
        columns={"Visitante": "Label", "Visitante URL": "URL"}
    )
    long_df = pd.concat([home, away], ignore_index=True)
    long_df["Slug"] = long_df["URL"].apply(extract_team_slug)
    long_df["Data_parsed"] = pd.to_datetime(long_df["Data"], errors="coerce")

    with_slug = long_df.dropna(subset=["Slug"])
    no_slug_count = int(long_df["Slug"].isna().sum())

    label_counts = with_slug.groupby("Slug")["Label"].nunique()
    split_slugs = label_counts[label_counts > 1].index.tolist()

    new_findings = []
    already_handled = []

    for slug in split_slugs:
        rows = with_slug[with_slug["Slug"] == slug]
        url_example = rows["URL"].dropna().iloc[0] if rows["URL"].notna().any() else None

        label_groups = []
        for label, group in rows.groupby("Label"):
            label_groups.append(
                {
                    "label": label,
                    "count": int(len(group)),
                    "min_date": _fmt(group["Data_parsed"].min()),
                    "max_date": _fmt(group["Data_parsed"].max()),
                }
            )
        label_groups.sort(key=lambda x: x["max_date"] or "")

        recommended = rows.sort_values("Data_parsed", ascending=False).iloc[0]["Label"]
        labels = {g["label"] for g in label_groups}
        aliased_targets = {TEAM_NAME_ALIASES.get(label, label) for label in labels}

        entry = {
            "slug": slug,
            "url_example": url_example,
            "total_games": int(len(rows)),
            "labels": label_groups,
            "recommended": recommended,
        }

        if len(aliased_targets) == 1:
            already_handled.append(entry)
        else:
            new_findings.append(entry)

    new_findings.sort(key=lambda x: -x["total_games"])
    already_handled.sort(key=lambda x: -x["total_games"])

    return {
        "total_games_rows": int(len(df)),
        "total_team_appearances": int(len(long_df)),
        "no_slug_count": no_slug_count,
        "total_slugs_checked": int(len(label_counts)),
        "split_slugs_count": len(split_slugs),
        "new_findings": new_findings,
        "already_handled": already_handled,
    }


def check_self_play_clashes(raw_dir: Path, groups: dict[str, list[str]]) -> dict[str, pd.DataFrame]:
    """Given proposed {canonical_name: [member labels]} merge groups (e.g. a human
    supplying a cross-slug merge the slug grouping above can't detect on its own),
    returns any games where both sides belong to the same proposed group - proof the
    two labels were separate opponents at some point and should NOT be merged as-is.
    An empty DataFrame for a group means it's safe to alias every member to one name.
    """
    df = _read_raw_games(raw_dir)
    clashes = {}
    for canonical, members in groups.items():
        member_set = set(members)
        mask = df["Mandante"].isin(member_set) & df["Visitante"].isin(member_set)
        clashes[canonical] = df[mask][["Data", "Mandante", "Visitante", "Torneio"]]
    return clashes


def _fmt(ts) -> Optional[str]:
    return ts.strftime("%Y-%m-%d") if pd.notna(ts) else None


def _print_report(result: dict) -> None:
    print(f"{result['total_games_rows']} games scanned, {result['total_team_appearances']} team appearances")
    print(f"{result['total_slugs_checked']} team pages checked, {result['no_slug_count']} appearances with no captured URL")
    print(f"{result['split_slugs_count']} slugs used under more than one label\n")

    print(f"Already covered by TEAM_NAME_ALIASES: {len(result['already_handled'])}")
    for entry in result["already_handled"]:
        chain = " / ".join(l["label"] for l in entry["labels"])
        print(f"  /{entry['slug']}/  {chain}")

    print(f"\nNOT yet covered ({len(result['new_findings'])}) - review before adding to TEAM_NAME_ALIASES:")
    for entry in result["new_findings"]:
        print(f"\n  /{entry['slug']}/  ({entry['total_games']} appearances)  recommended: {entry['recommended']!r}")
        for l in entry["labels"]:
            print(f"    {l['label']!r}: {l['count']}x, {l['min_date']} to {l['max_date']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=RAW_GAMES_DIR)
    parser.add_argument("--json", type=Path, default=None, help="Also write the full result as JSON to this path.")
    args = parser.parse_args()

    result = find_split_teams(args.raw_dir)
    _print_report(result)

    if args.json:
        args.json.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\nFull result written to {args.json}")
