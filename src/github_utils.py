import sys
import json
import logging
import datetime
import urllib.parse
import urllib.request
from random import choice


def download_github_avatar(url: str, output_filename: str = "ball_avatar.png") -> str:
    """Downloads a GitHub avatar from any GitHub URL, removing size constraints, and returns the local path."""
    logging.info(f"Downloading avatar from GitHub: {url}")
    try:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)

        query_params.pop("size", None)
        query_params.pop("s", None)

        new_query = urllib.parse.urlencode(query_params, doseq=True)
        clean_url = urllib.parse.urlunparse(
            (
                parsed_url.scheme,
                parsed_url.netloc,
                parsed_url.path,
                parsed_url.params,
                new_query,
                parsed_url.fragment,
            )
        )

        req = urllib.request.Request(clean_url, headers={"User-Agent": "Mozilla/5.0"})

        with urllib.request.urlopen(req) as response, open(
            output_filename, "wb"
        ) as out_file:
            out_file.write(response.read())

        logging.info(f"Avatar successfully saved locally as: {output_filename}")
        return "./" + output_filename

    except Exception as e:
        logging.error(f"Failed to download GitHub avatar: {e}")
        sys.exit(1)


def get_last_stargazer_of_account(username: str) -> str:
    """Fetches the avatar URL of the user who dropped the latest star across all public repositories of the account."""
    repos_url = f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
    req_repos = urllib.request.Request(repos_url, headers={"User-Agent": "Mozilla/5.0"})

    logging.info(f"Fetching recent repositories for account: {username}")
    try:
        with urllib.request.urlopen(req_repos) as response:
            repos = json.loads(response.read().decode())

        latest_star_time = None
        latest_stargazer_avatar = None
        latest_stargazer_login = None

        for repo in repos:
            if repo["stargazers_count"] == 0:
                continue

            repo_name = repo["full_name"]
            stars_url = f"https://api.github.com/repos/{repo_name}/stargazers?per_page=1&page=1"
            req_stars = urllib.request.Request(stars_url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/vnd.github.v3.star+json"
            })

            try:
                with urllib.request.urlopen(req_stars) as star_response:
                    stargazers = json.loads(star_response.read().decode())
                    if stargazers:
                        star_info = stargazers[0]
                        starred_at_str = star_info.get("starred_at", "1970-01-01T00:00:00Z").replace("Z", "+00:00")
                        star_time = datetime.datetime.fromisoformat(starred_at_str)

                        if latest_star_time is None or star_time > latest_star_time:
                            latest_star_time = star_time
                            latest_stargazer_avatar = star_info["user"]["avatar_url"]
                            latest_stargazer_login = star_info["user"]["login"]
            except Exception:
                continue

        if latest_stargazer_avatar:
            logging.info(f"Absolute last stargazer across account found: {latest_stargazer_login}")
            return latest_stargazer_avatar

        logging.warning("No stargazers found across any recent repository. Falling back to owner avatar.")
        return f"https://github.com/{username}.png"

    except Exception as e:
        logging.error(f"Failed to fetch account stargazers from GitHub API: {e}")
        sys.exit(1)


def get_random_follower_avatar(username: str) -> str:
    """Fetches the avatar URL of a random follower from the account hosting the script."""
    url = f"https://api.github.com/users/{username}/followers?per_page=100"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    logging.info(f"Fetching followers for account: {username}")
    try:
        with urllib.request.urlopen(req) as response:
            followers = json.loads(response.read().decode())
            if followers:
                random_follower = choice(followers)
                logging.info(f"Random follower picked: {random_follower['login']}")
                return random_follower["avatar_url"]
            else:
                logging.warning("No followers found for this account. Falling back to owner avatar.")
                return f"https://github.com/{username}.png"
    except Exception as e:
        logging.error(f"Failed to fetch followers from GitHub API: {e}")
        sys.exit(1)
