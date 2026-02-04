import pathlib

from PCS_scraper import update_points_stages, get_startlist_teams

TDF_YEAR = 2024
CURRENT_STAGE = 21

# Extract the full startlist, useful for creating participation forms for the TdF game
start_teams = get_startlist_teams(year=TDF_YEAR)
start_teams.to_csv(pathlib.Path("outputs", "TDF"+str(TDF_YEAR)+" startlist.csv"))

# This is how you can obtain intermediate points standings after a specific stage
for stage in [1, 6, 11, 21]:
    points = update_points_stages(stage=stage, year=TDF_YEAR)
    points.to_csv(pathlib.Path("outputs", "TDF"+str(TDF_YEAR)+" Stage "+str(stage)+" points.csv"))

# This extracts the full point distribution after completion of the race
final = update_points_stages(stage=CURRENT_STAGE, year=TDF_YEAR, include_final_points=True)
final.to_csv(pathlib.Path("outputs", "TDF"+str(TDF_YEAR)+" Stage "+str(CURRENT_STAGE)+" final points.csv"))