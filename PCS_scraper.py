import cloudscraper
import numpy as np
import pandas as pd
import re

import urllib.request as urlib
from bs4 import BeautifulSoup as bs
from getuseragent import UserAgent

# Points awarded after every stage or for final classifications. See example .xls file for explanation.
POINTS_DISTRIBUTION = {
    'stage': {
        1: 25,
        2: 19,
        3: 14,
        4: 10,
        5: 7,
        6: 5,
        7: 4,
        8: 3,
        9: 2,
        10: 1,
        'gc': 7,
        'green': 3,
        'kom': 3
    },
    'gc': {
        1: 220,
        2: 160,
        3: 115,
        4: 85,
        5: 65,
        6: 50,
        7: 40,
        8: 30,
        9: 20,
        10: 10,
        11: 7,
        12: 5,
        13: 3,
        14: 2,
        15: 1,
    },
    'green': {
        1: 100,
        2: 50,
        3: 20,
        4: 10,
        5: 5,
    },
    'kom': {
        1: 100,
        2: 50,
        3: 20,
        4: 10,
        5: 5,
    }
}

scraper = cloudscraper.create_scraper()

def get_rider_string(rider_soup):
    """Unpack a rider's name from the html formatting."""
    return rider_soup.span.string.upper()+rider_soup.contents[1]


def get_random_agent():
    """Provides a random spoof user agent for web scraping."""
    return UserAgent("all", requestsPrefix=True).Random()


def get_pcs_url(type, stage=1, year=2025, base_url="https://www.procyclingstats.com/race/tour-de-france/"):
    """Construct the ProCyclingStats url used for scraping race results."""
    if type == 'startlist':
        return base_url+str(year)+"/startlist"
    elif type == 'stage':
        return base_url+str(year)+"/stage-"+str(stage)


def get_startlist_teams(year=2025):
    """Extract the startlist, organized into the different participating teams

        Parameters:
            year (int): year of the Tour

        Returns:
            riders (pandas DataFrame):  Dataframe of all participating riders organized with teams as column headers.
    """
    start_url = get_pcs_url(type='startlist', year=year)
    start_soup = bs(scraper.get(start_url).text, 'html.parser')
    list_soup = start_soup.find("div", class_="page-content")
    riders_soup = list_soup.find_all("a", string=True, href=re.compile("^(rider|team)/", ))
    teams = {}
    team = None
    for rider in riders_soup:
        if 'class' in str(rider):
            if team:
                teams[team] = riders
            team = rider.string[:-5]
            riders = []
        else:
            riders.append(rider.string)
    teams[team] = riders
    startlist_by_team = pd.DataFrame.from_dict(teams, orient='index').transpose()
    return startlist_by_team


def get_startlist(year=2025):
    """Extract the full startlist of competing riders (for a given year).

        Parameters:
            year (int): year of the Tour

        Returns:
            riders (List): A full list of rider names. Each name consists of an uppercase last name followed by their
            first name
    """
    riders = []
    start_url = get_pcs_url(type='startlist', year=year)
    start_soup = bs(scraper.get(start_url).text, 'html.parser')
    riders_soup = start_soup.find_all("a", href=re.compile("^rider/"))
    for rider in riders_soup:
        riders.append(rider.string)
    return riders


def get_stage_results(stage, year=2025):
    """Get all points scored in a specific stage (of a given year).

        Parameters:
            stage (int): stage number (1-21)
            year (int): year of the Tour

        Returns:
            total_stage_points (List): A list of tuples of the top 10 riders of the stage plus jersey wearers. Each
            tuple consists of the rider's name and the accompanying points.
            top10 (list): A list of the top 10 riders for the specific stage. This is the output for the last stage as
            no additional points for jersey wearers are given out. Instead the points of final jersey wearers are
            handled by get_final_results()
    """
    stage_url = get_pcs_url(type='stage', stage=stage, year=year)
    soup = bs(scraper.get(stage_url).text, 'html.parser')
    tables_raw = soup.find_all("table", class_=re.compile("result"))
    stage_table = tables_raw[0]
    stage_list = stage_table.find_all("a", href=re.compile("^rider"))
    top10 = []
    for rank in range(1, 11):
        top10.append((get_rider_string(stage_list[rank - 1]), POINTS_DISTRIBUTION['stage'][rank]))
    if stage != 21:
        gc = (get_rider_string(tables_raw[1].find_all("a", href=re.compile("^rider"))[0]),
              POINTS_DISTRIBUTION['stage']['gc'])
        green = (get_rider_string(tables_raw[2].find_all("a", href=re.compile("^rider"))[0]),
                 POINTS_DISTRIBUTION['stage']['green'])
        kom = (get_rider_string(tables_raw[5].find_all("a", href=re.compile("^rider"))[0]),
               POINTS_DISTRIBUTION['stage']['kom'])
        total_stage_points = top10 + [gc] + [green] + [kom]
        return total_stage_points
    return top10


def get_final_results(stage=21, year=2025):
    """Computes the points for the final classifications (for a given year). If the stage parameter is given, a
    preliminary final point distribution is computed, assuming no changes to the classifications after this stage.

        Parameters:
            stage (int): stage number (1-21)
            year (int): year of the Tour

        Returns:
            total_final_points (list): A list of tuples consisting of riders' names and points in final
            classifications.
    """
    stage_url = get_pcs_url(type='stage', stage=stage, year=year)
    # time.sleep(2)
    soup = bs(scraper.get(stage_url).text, 'html.parser')
    tables_raw = soup.find_all("table", class_=re.compile("result"))

    def distribute_points(table, point_distribution):
        points = []
        for rank in range(1, max(point_distribution)+1):
            points.append((get_rider_string(table[rank-1]), point_distribution[rank]))
        return points

    gc_table = tables_raw[1].find_all("a", href=re.compile("^rider"))
    gc_points = distribute_points(gc_table, POINTS_DISTRIBUTION['gc'])
    green_table = tables_raw[2].find_all("a", href=re.compile("^rider"))
    green_points = distribute_points(green_table, POINTS_DISTRIBUTION['green'])
    kom_table = tables_raw[4].find_all("a", href=re.compile("^rider"))
    kom_points = distribute_points(kom_table, POINTS_DISTRIBUTION['kom'])
    total_final_points = gc_points + green_points + kom_points

    return total_final_points


def update_points_stages(stage, year=2025, include_final_points=False):
    """Consolidate all points obtained up to and including a certain stage. Final classification points can also be
    included.

        Parameters:
            stage (int): stage number (1-21)
            year (int): year of the Tour
            include_final_points (bool): Boolean for inclusion of final classification points

        Returns:
            points_overview (pandas DataFrame):  Dataframe of points obtained with rider names as index and stages as
            columns, including a total column with the sum over all stages for each rider. The riders are sorted by
            total points obtained.
    """
    riders = get_startlist(year=year)

    results = pd.DataFrame(index=riders)
    for stage_number in range(1,stage+1):
        results[stage_number] = np.zeros(results.shape[0])

    for stage in range(1, stage+1):
        points = get_stage_results(stage, year)
        for (rider, point) in points:
            results.loc[rider, stage] += point
        results = results.astype({stage: 'int'})

    if include_final_points:
        results["final"] = np.zeros(results.shape[0])
        final_points = get_final_results(stage, year)
        for (rider, point) in final_points:
            results.loc[rider, 'final'] += point

    results['total'] = results.sum(axis=1)
    points_overview = results.sort_values(by='total', ascending=False)

    return points_overview


