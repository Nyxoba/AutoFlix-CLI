from ..scraping import arkanime, player
from ..cli_utils import (
    select_from_list,
    print_header,
    print_info,
    print_error,
    print_warning,
    get_user_input,
    console,
    pause,
)
from ..player_manager import play_video
from ..tracker import tracker
from .playback import play_episode_flow

def handle_arkanime():
    """Handle ArkAnime provider flow."""
    arkanime.get_website_url()

    print_header("⛩️ ArkAnime")

    while True:
        query = get_user_input("Search query (or 'exit' to back)")
        if not query or query.lower() == "exit":
            break

        print_info(f"Searching for: [cyan]{query}[/cyan]")
        try:
            results = arkanime.search(query)
        except Exception as e:
            print_error(f"Error searching: {e}")
            pause()
            continue

        if not results:
            print_warning("No results found.")
            pause()
            continue

        options = [f"{r.title}" for r in results] + ["← Back"]
        choice_idx = select_from_list(options, "📺 Search Results:")

        if choice_idx == len(results):
            continue

        selection = results[choice_idx]

        print_info(f"Loading [cyan]{selection.title}[/cyan]...")
        try:
            series = arkanime.get_series(selection.url)
        except Exception as e:
            print_error(f"Error loading series: {e}")
            pause()
            continue

        if not series.seasons:
            print_warning("No seasons found.")
            pause()
            continue

        # Check for saved progress for this specific series
        saved_progress = tracker.get_series_progress("ArkAnime", series.title)
        if saved_progress:
            choice = select_from_list(
                [
                    f"Resume {saved_progress['season_title']} - {saved_progress['episode_title']}",
                    "Browse Seasons",
                ],
                f"Found saved progress for {series.title}:",
            )
            if choice == 0:
                resume_arkanime(saved_progress)
                continue

        season_idx = select_from_list(
            [s.title for s in series.seasons], "📺 Select Season:"
        )
        season = series.seasons[season_idx]

        if not season.episodes:
            print_warning("No episodes found.")
            pause()
            continue

        ep_idx = select_from_list(
            [e.title for e in season.episodes], "📺 Select Episode:"
        )

        while True:
            selected_episode = season.episodes[ep_idx]
            headers = {"Referer": arkanime.website_origin}

            success = play_episode_flow(
                provider_name="ArkAnime",
                series_title=series.title,
                season_title=season.title,
                episode=selected_episode,
                series_url=series.id,  # using id for url since we matched it
                season_url=str(season.id), # Using id for season url
                logo_url=series.img,
                headers=headers,
            )

            if success:
                if ep_idx + 1 < len(season.episodes):
                    next_ep = season.episodes[ep_idx + 1]
                    choice = select_from_list(
                        ["Yes", "No"], f"Play next episode: {next_ep.title}?"
                    )
                    if choice == 0:
                        ep_idx += 1
                        continue
                break
            else:
                break


def resume_arkanime(data):
    """Resume ArkAnime playback."""
    arkanime.get_website_url()

    print_info(f"Resuming [cyan]{data['series_title']}[/cyan]...")

    try:
        series = arkanime.get_series(data["series_url"])
    except Exception as e:
        print_error(f"Could not load series: {e}")
        pause()
        return

    season = None
    for s in series.seasons:
        if str(s.id) == data.get("season_url") or s.title == data.get("season_title"):
            season = s
            break

    if not season:
        print_error("Could not find the saved season.")
        pause()
        return

    if not season.episodes:
        print_warning("No episodes found in season.")
        pause()
        return

    # Find episode index
    start_ep_idx = 0
    saved_ep_title = data["episode_title"]

    for i, ep in enumerate(season.episodes):
        if ep.title == saved_ep_title:
            start_ep_idx = i
            break

    options = [
        (
            f"Continue (Next: {season.episodes[start_ep_idx+1].title})"
            if start_ep_idx + 1 < len(season.episodes)
            else "No next episode"
        ),
        f"Watch again ({saved_ep_title})",
        "Cancel",
    ]
    choice = select_from_list(options, "What would you like to do?")

    if choice == 2:
        return
    elif choice == 0:
        if start_ep_idx + 1 < len(season.episodes):
            start_ep_idx += 1
        else:
            return

    ep_idx = start_ep_idx

    while True:
        selected_episode = season.episodes[ep_idx]
        headers = {"Referer": arkanime.website_origin}

        success = play_episode_flow(
            provider_name="ArkAnime",
            series_title=data["series_title"],
            season_title=season.title,
            episode=selected_episode,
            series_url=data["series_url"],
            season_url=str(season.id),
            logo_url=data.get("logo_url"),
            headers=headers,
        )

        if success:
            if ep_idx + 1 < len(season.episodes):
                if (
                    select_from_list(
                        ["Yes", "No"],
                        f"Play next: {season.episodes[ep_idx+1].title}?",
                    )
                    == 0
                ):
                    ep_idx += 1
                    continue
            break
        else:
            return
