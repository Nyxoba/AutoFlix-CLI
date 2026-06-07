from autoflix_cli.scraping.objects import ArkSeries
from autoflix_cli.scraping.objects import Player
from autoflix_cli.scraping.objects import ArkSeason
from curl_cffi import requests as cffi_requests
from .objects import SearchResult, SamaSeries, Episode
from ..proxy import DNS_OPTIONS

website_origin = ""

scraper = cffi_requests.Session(impersonate="chrome", curl_options=DNS_OPTIONS)

from .config import portals


def get_website_url(portal=portals["arkanime"]):
    global website_origin

    return portal


def search(query: str) -> list[SearchResult]:
    page = website_origin + f"/api/anime?q={query}"

    response = scraper.get(page)
    response.raise_for_status()

    results: list[SearchResult] = []

    for result in response.json()["results"]:
        title =  result["titleEnglish"]
        url = str(result["id"])
        img = result["coverImage"]
        genres = result["genres"]

        results.append(SearchResult(title, url, img, genres))

    return results

def get_series(url: str) -> SamaSeries:
    response = scraper.get(website_origin + "/api/anime/" + url)
    response.raise_for_status()

    series = response.json()["result"]

    title = series["titleEnglish"]
    img = series["coverImage"]
    genres = series["genres"]

    seasons:list[ArkSeason] = []
    for season in series["seasons"]:
        id = season["id"]
        season_title = season["title"]
        
        episodes: list[Episode] = []
        for episode in season["episodes"]:
            players = [
                Player("montmyoboky (default)", "montmyoboky:" + str(episode["id"]))
            ]

            episodes.append(Episode(f"Episode {episode['number']} : " + episode["title"], players=players))

        for arc in season["arcs"]:
            arc_url = website_origin + f"/api/anime/{url}/seasons/{id}/episodes?from={arc['episodeStart']}&to={arc['episodeEnd']}"
            arc_response = scraper.get(arc_url)
            arc_response.raise_for_status()

            arc_json = arc_response.json()
            for episode in arc_json["episodes"]:
                players = [
                   Player("montmyoboky (default)", "montmyoboky:" + str(episode["id"]))
                ]

                episodes.append(Episode(f"Episode {episode['number']} : " + episode["title"], players=players))

        seasons.append(ArkSeason(id, season_title, episodes))

    return ArkSeries(title, url, img, genres, seasons)


if __name__ == "__main__":
    #print(search("one piece"))
    #print(get_series("106"))
    print(get_series("313"))

