# Canonicalizes every raw team-name variant the scraper has ever produced down to one
# name per real team, so the belt algorithm (a linear walk that matches a champion's
# *name* to their next game) never treats one team as two.
#
# Two different kinds of evidence back this dict, and they're not interchangeable:
#
# 1. Bio-page-name entries (added 2026-08-23/24, before team-page URLs were captured
#    on raw game rows): a handful of teams whose site bio page uses a different label
#    than their game-listing rows (e.g. "América Locomotiva" bio page vs. "Locomotiva
#    FA" schedule-table label). Found incidentally, one at a time, via test failures
#    or manual review - not systematically verified against game data.
#
# 2. Slug-audit entries (added 2026-08-26, see docs/DATA_PIPELINE.md's "Team name
#    slug audit" section for the full writeup): every raw game row now carries the
#    team-page URL each side linked to (Mandante URL/Visitante URL columns in
#    data/raw/games/*.csv). Grouping every team appearance by the URL's slug - a
#    stable ID that survives a display-name change - surfaces every team the raw
#    scrape has called by more than one name. Re-run via
#    src/pipeline/audit_team_aliases.py. Canonical name = whichever label appears on
#    that slug's most recently dated game.
#
#    Critical caveat this method depends on: two labels sharing one slug means they're
#    provably the *same site page*, which is strong evidence they're the same team
#    across time. It says nothing about two DIFFERENT slugs - a human claiming two
#    site pages are "the same team" must still be checked against whether the two
#    labels ever played each other (self-play in the game data proves they were once
#    separate opponents, not one team pretending to be two). Several candidate merges
#    surfaced by Victor's review failed exactly this check and were deliberately left
#    unaliased - see the "explicitly NOT merged" note at the bottom of this file.
TEAM_NAME_ALIASES: dict[str, str] = {
    # --- bio-page-name entries (2026-08-23/24) ---
    "Fluminense Imperadores": "Flamengo Imperadores",  # corrected 2026-08-26, was
    # wrongly aliased to "Fluminense FA" - "Fluminense FA" never appears as a raw
    # game-row label at all (verified against the full raw dataset), so that
    # alias was a guess made without slug evidence. The slug audit below found
    # "Fluminense Imperadores"'s real identity instead.
    "Vila Velha Tritões": "Tritões FA",
    "Six Spartans": "Spartans Football",
    "Blaze Futebol Americano": "Blaze FA",
    "Istepôs Futebol Americano": "Istepôs FA",
    "América Locomotiva": "Locomotiva FA",

    # --- found via the 2026-08-26 backend regeneration: bio-page-only verbose names
    # for teams whose short game-listing label is already the games.csv canonical
    # (same class as the entries above, found this time via unresolved-team-count
    # spot checks against the fresh teams re-scrape rather than the slug audit) ---
    "Tritões Futebol Americano": "Tritões FA",
    "Miners Futebol Americano": "Miners FA",
    "Paraná Clube Guardian Saints": "PRC Guardian Saints",
    "Gaspar Black Hawks": "Black Hawks",
    "Tigres Futebol Americano": "Tigres FA",

    # --- already covered before the slug audit (kept for the games-data label,
    # T-Rex/Timbó Rex found 2026-08-24; the other two below are also slug-confirmed
    # via the 2026-08-26 audit but were already correct) ---
    "Foz Black Sharks": "Foz do Iguaçu Black Sharks",
    "Joinville Gladiators": "JEC Gladiators",
    "Juventude FA": "União da Serra/Juventude FA",
    "União da Serra": "União da Serra/Juventude FA",
    "T-Rex": "Timbó Rex",

    # --- slug audit (2026-08-26), reviewed and confirmed by Victor ---
    "RJ Imperadores": "Flamengo Imperadores",
    "Sada Cruzeiro": "Galo FA",  # canonical changed from the old compound
    "Galo Futebol Americano": "Galo FA",  # "Sada Cruzeiro/Galo FA" - "Galo FA" is
    "BH Eagles": "Galo FA",  # the name used on every game since 2018; the compound
    # form was a hedge from before the slug evidence existed to justify simplifying it.
    "Vinhedo Lumberjacks": "Ponte Preta Gorilas",
    "Paulínia Mavericks": "Guarani Indians",
    "Guardian Saints": "PRC Guardian Saints",
    "Betim Bulldogs": "Cruzeiro FA",
    "Vitória All Saints": "Cavalaria 2 de Julho",
    "Vitória FA": "Cavalaria 2 de Julho",
    "Independente Tomahawk": "Tomahawk FA",
    "Leões de Judá": "Gama Leões de Judá",
    "Ceará Cangaceiros": "Ceará Caçadores",
    "Recife Pirates": "Santa Cruz Pirates",
    "Manaus Cavaliers": "São Raimundo C. Cavaliers",
    "Bulls Potiguares": "América Bulls",
    "Goiânia Tigres": "Goiânia Rednecks",
    "Criciuma Slayers": "Miners FA",
    "Campo Grande Gravediggers": "Operário Gravediggers",
    "Lobo Vingador": "Vingadores FA",
    "Campo Grande Predadores": "CG Predadores",
    "Restinga Redskulls": "Cruzeiro Lions",
    "Barueri Guardians": "Scelta Guardians",
    "Lobos do Mar": "Camboriú Broqueiros",
    "Recife Imortais": "Santa Cruz Imortais",
    "ES Black Knights": "Espírito Santo Black Knights",
    "HP Desenvolvimento": "Paraná HP",
    "Armada FA": "Porto Alegre Pumpkins",
    "Armada Lions": "Porto Alegre Pumpkins",
}

# Explicitly NOT merged, despite Victor identifying them as real predecessor
# organizations, because each pair has actual head-to-head games against the name
# it would be merged into - proof they were separate opponents at the time, not one
# team under two names. Per Victor (2026-08-26): these were genuinely separate clubs
# that later merged into/became the surviving name; merging their labels retroactively
# would turn real historical matchups into a team playing itself and corrupt the belt
# algorithm's chain. Left as fully independent teams to preserve that history:
#   - Curitiba Hurricanes / Curitiba Predadores  (both predecessors of Paraná HP;
#     6 games between them, 2011-2013)
#   - Salvador Kings  (predecessor of Cavalaria 2 de Julho; 1 game vs. Vitória All
#     Saints, 2014-05-18)
#   - Dragões do Mar  (predecessor of Ceará Caçadores; 4 games vs. Ceará Cangaceiros,
#     2011-2013)
#   - Paysandu Lobos  (predecessor of Vingadores FA; 4 games vs. Vingadores FA,
#     2018-2019)
#   - Campo Grande Cobras / Jacarés do Pantanal  (both predecessors of CG Predadores;
#     1 game between them, 2014-10-18)
#   - Restinga Redskulls/Cruzeiro Lions (already merged above) is NOT the same team as
#     Porto Alegre Pumpkins/Armada FA/Armada Lions, despite using similar naming - 3
#     games between them, 2016-2017. Two different site slugs (armada-lions,
#     porto-alegre-pumpkins), two different teams.
