"""Pong simulation"""

import argparse
import logging
import urllib.parse
import urllib.request
import json
import os
import sys
import datetime
from random import randint, choice
from time import sleep, perf_counter
from xml.etree import ElementTree as ET

# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
    repos_url = (
        f"https://api.github.com/users/{username}/repos?sort=updated&per_page=10"
    )
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
            stars_url = (
                f"https://api.github.com/repos/{repo_name}/stargazers?per_page=1&page=1"
            )
            req_stars = urllib.request.Request(
                stars_url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/vnd.github.v3.star+json",
                },
            )

            try:
                with urllib.request.urlopen(req_stars) as star_response:
                    stargazers = json.loads(star_response.read().decode())
                    if stargazers:
                        star_info = stargazers[0]
                        starred_at_str = star_info.get(
                            "starred_at", "1970-01-01T00:00:00Z"
                        ).replace("Z", "+00:00")
                        star_time = datetime.datetime.fromisoformat(starred_at_str)

                        if latest_star_time is None or star_time > latest_star_time:
                            latest_star_time = star_time
                            latest_stargazer_avatar = star_info["user"]["avatar_url"]
                            latest_stargazer_login = star_info["user"]["login"]
            except Exception:
                continue

        if latest_stargazer_avatar:
            logging.info(
                f"Absolute last stargazer across account found: {latest_stargazer_login}"
            )
            return latest_stargazer_avatar

        logging.warning(
            "No stargazers found across any recent repository. Falling back to owner avatar."
        )
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
                logging.warning(
                    "No followers found for this account. Falling back to owner avatar."
                )
                return f"https://github.com/{username}.png"
    except Exception as e:
        logging.error(f"Failed to fetch followers from GitHub API: {e}")
        sys.exit(1)


def gen_pong_svg(
    canvas_width: int,
    canvas_height: int,
    ball_radius: float,
    duration: float,
    player_one_x: float,
    player_two_x: float,
    player_width: int,
    player_height: int,
    player_one_frames: list[list[float]],
    player_two_frames: list[list[float]],
    ball_frames: list[list[float]],
    score_frames: list[list],
    output_file_path: str,
    image_filename: str,
    primary_color: str = "gray",
    score_text_area_height: int = 40,
):
    """Generate pong game animation into an svg using frames"""
    logging.debug(f"Generating SVG: {output_file_path}")

    extra_h = score_text_area_height
    total_h = canvas_height + extra_h

    svg = ET.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        width=str(canvas_width),
        height=str(total_h),
    )

    defs = ET.SubElement(svg, "defs")
    clip_path = ET.SubElement(
        defs, "clipPath", id="ball-clip", clipPathUnits="objectBoundingBox"
    )
    ET.SubElement(
        clip_path,
        "circle",
        cx="0.5",
        cy="0.5",
        r="0.5",
    )

    ET.SubElement(
        svg,
        "rect",
        x="0",
        y="0",
        width=str(canvas_width),
        height=str(canvas_height),
        fill="transparent",
    )

    ET.SubElement(
        svg,
        "rect",
        x="0",
        y=str(canvas_height),
        width=str(canvas_width),
        height=str(extra_h),
        fill="transparent",
    )

    score_text = ET.SubElement(
        svg,
        "text",
        x=str(canvas_width // 2),
        y=str(canvas_height + extra_h // 2 + 6),
        fill=primary_color,
    )
    score_text.set("text-anchor", "middle")
    score_text.set("font-size", "24")

    score_key_times = (
        "0;" + ";".join(str(frame[1]) for frame in score_frames[1:-1]) + ";1"
    )

    frame_tspan = ET.SubElement(
        score_text,
        "tspan",
        opacity="1",
        x=str(canvas_width // 2),
        y=str(canvas_height + extra_h // 2 + 6),
    )
    frame_tspan.text = str(score_frames[0][0])

    ET.SubElement(
        frame_tspan,
        "animate",
        attributeName="opacity",
        dur=str(duration),
        calcMode="discrete",
        repeatCount="indefinite",
        values="1;" + ";".join(["0"] * (len(score_frames) - 1)),
        keyTimes=score_key_times,
    )

    for i, score_frame in enumerate(score_frames[1:]):
        frame_tspan = ET.SubElement(
            score_text,
            "tspan",
            opacity="0",
            x=str(canvas_width // 2),
            y=str(canvas_height + extra_h // 2 + 6),
        )
        frame_tspan.text = str(score_frame[0])

        values = ["0"] * (len(score_frames))
        values[i + 1] = "1"

        ET.SubElement(
            frame_tspan,
            "animate",
            attributeName="opacity",
            calcMode="discrete",
            dur=str(duration),
            repeatCount="indefinite",
            values=";".join(values),
            keyTimes=score_key_times,
        )

    ball_group = ET.SubElement(svg, "g")

    ET.SubElement(
        ball_group,
        "animateTransform",
        attributeName="transform",
        type="translate",
        additive="sum",
        dur=str(duration),
        repeatCount="indefinite",
        values=";".join([f"{round(frame[0], 1)} 0" for frame in ball_frames]),
        keyTimes=";".join([str(frame[2]) for frame in ball_frames]),
    )

    ET.SubElement(
        ball_group,
        "animateTransform",
        attributeName="transform",
        type="translate",
        additive="sum",
        dur=str(duration),
        repeatCount="indefinite",
        values=";".join([f"0 {round(frame[1], 1)}" for frame in ball_frames]),
        keyTimes=";".join([str(frame[2]) for frame in ball_frames]),
    )

    ET.SubElement(
        ball_group,
        "circle",
        cx="0",
        cy="0",
        r=str(ball_radius),
        fill=primary_color,
    )

    img_size = ball_radius * 2

    ball_image = ET.SubElement(
        ball_group,
        "image",
        href=image_filename,
        x=str(-img_size / 2),
        y=str(-img_size / 2),
        width=str(img_size),
        height=str(img_size),
        preserveAspectRatio="xMidYMid slice",
    )
    ball_image.set("clip-path", "url(#ball-clip)")

    player_one = ET.SubElement(
        svg,
        "rect",
        x=str(player_one_x),
        y=str(player_one_frames[0][0]),
        width=str(player_width),
        height=str(player_height),
        fill=primary_color,
    )
    ET.SubElement(
        player_one,
        "animate",
        attributeName="y",
        dur=str(duration),
        repeatCount="indefinite",
        values=";".join([str(frame[0]) for frame in player_one_frames]),
        keyTimes=";".join([str(frame[1]) for frame in player_one_frames]),
    )

    player_two = ET.SubElement(
        svg,
        "rect",
        x=str(player_two_x),
        y=str(player_two_frames[0][0]),
        width=str(player_width),
        height=str(player_height),
        fill=primary_color,
    )
    ET.SubElement(
        player_two,
        "animate",
        attributeName="y",
        dur=str(duration),
        repeatCount="indefinite",
        values=";".join([str(frame[0]) for frame in player_two_frames]),
        keyTimes=";".join([str(frame[1]) for frame in player_two_frames]),
    )

    tree = ET.ElementTree(svg)
    tree.write(output_file_path, encoding="utf-8", xml_declaration=True)
    logging.info(f"Successfully saved: {output_file_path}")


class PongGameSvgGenerator:
    def __init__(
        self, canvas_width: int = 824, canvas_height: int = 300, winning_score: int = 1
    ):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.winning_score = winning_score
        self.tick_rate_ms = 10
        self.paddle_width = 10
        self.paddle_height = 75
        self.paddle_speed = 5
        self.paddle_wall_margin = 5
        self.ball_radius = 7.5
        self.starting_ball_speed = 1
        self.ball_speed_increase = 0.5
        self.max_ball_speed = 10
        self.reset_game()

    def reset_game(self):
        self.player_one_score = 0
        self.player_two_score = 0
        self.player_one_paddle = {
            "width": self.paddle_width,
            "height": self.paddle_height,
            "x": self.paddle_wall_margin,
            "y": (self.canvas_height - self.paddle_height) / 2,
        }
        self.player_two_paddle = {
            "width": self.paddle_width,
            "height": self.paddle_height,
            "x": self.canvas_width - self.paddle_width - self.paddle_wall_margin,
            "y": (self.canvas_height - self.paddle_height) / 2,
        }
        self.ball_x = self.canvas_width / 2
        self.ball_y = self.canvas_height / 2
        self.prev_ball_x = self.ball_x
        self.prev_ball_y = self.ball_y
        self.ball_speed = self.starting_ball_speed
        self.ball_x_dir = 0
        self.ball_y_dir = 0
        self.player_one_up = self.player_one_down = self.player_two_up = (
            self.player_two_down
        ) = False
        self.prev_scores = [0, 0]
        self.score_frames = [["0 | 0", 0]]

    def create_ball(self):
        self.ball_speed = self.starting_ball_speed
        self.ball_x_dir = 1 if randint(0, 1) == 1 else -1
        self.ball_y_dir = 1 if randint(0, 1) == 1 else -1
        self.ball_x = self.canvas_width / 2
        self.ball_y = self.canvas_height / 2

    def move_ball(self):
        self.ball_x += self.ball_speed * self.ball_x_dir
        self.ball_y += self.ball_speed * self.ball_y_dir

    def calculate_player_movement(self):
        if self.player_one_up and self.player_one_paddle["y"] > 0:
            self.player_one_paddle["y"] -= self.paddle_speed
        if (
            self.player_one_down
            and self.player_one_paddle["y"]
            < self.canvas_height - self.player_one_paddle["height"]
        ):
            self.player_one_paddle["y"] += self.paddle_speed
        if self.player_two_up and self.player_two_paddle["y"] > 0:
            self.player_two_paddle["y"] -= self.paddle_speed
        if (
            self.player_two_down
            and self.player_two_paddle["y"]
            < self.canvas_height - self.player_two_paddle["height"]
        ):
            self.player_two_paddle["y"] += self.paddle_speed

    def check_collision(self):
        if self.ball_y <= self.ball_radius:
            self.ball_y_dir *= -1
            self.ball_y = self.ball_radius
        if self.ball_y >= self.canvas_height - self.ball_radius:
            self.ball_y_dir *= -1
            self.ball_y = self.canvas_height - self.ball_radius

        if self.ball_x <= 0:
            self.player_two_score += 1
            self.create_ball()
            return
        if self.ball_x >= self.canvas_width:
            self.player_one_score += 1
            self.create_ball()
            return

        if (
            self.ball_x
            <= self.player_one_paddle["x"]
            + self.player_one_paddle["width"]
            + self.ball_radius
        ):
            if (
                self.player_one_paddle["y"]
                < self.ball_y
                < self.player_one_paddle["y"] + self.player_one_paddle["height"]
            ):
                self.ball_x = (
                    self.player_one_paddle["x"]
                    + self.player_one_paddle["width"]
                    + self.ball_radius
                )
                self.ball_x_dir = abs(self.ball_x_dir)
                if self.ball_speed + self.ball_speed_increase <= self.max_ball_speed:
                    self.ball_speed += self.ball_speed_increase

        if self.ball_x >= self.player_two_paddle["x"] - self.ball_radius:
            if (
                self.player_two_paddle["y"]
                < self.ball_y
                < self.player_two_paddle["y"] + self.player_two_paddle["height"]
            ):
                self.ball_x = self.player_two_paddle["x"] - self.ball_radius
                self.ball_x_dir = -abs(self.ball_x_dir)
                if self.ball_speed + self.ball_speed_increase <= self.max_ball_speed:
                    self.ball_speed += self.ball_speed_increase

    def player_ai_movement(self):
        slope = (self.ball_y - self.prev_ball_y) / (
            self.ball_x - self.prev_ball_x + 1e-9
        )
        prediction_y = -slope * self.player_one_paddle["x"] + self.ball_y
        self.prev_ball_x = self.ball_x
        self.prev_ball_y = self.ball_y

        if self.ball_x_dir < 0:
            center = self.player_one_paddle["y"] + self.player_one_paddle["height"] / 2
            self.player_one_down = prediction_y > center + self.paddle_speed
            self.player_one_up = prediction_y < center - self.paddle_speed
        elif self.ball_x_dir > 0:
            center = self.player_two_paddle["y"] + self.player_two_paddle["height"] / 2
            self.player_two_down = prediction_y > center + self.paddle_speed
            self.player_two_up = prediction_y < center - self.paddle_speed

    def next_tick(self):
        if (
            self.player_one_score >= self.winning_score
            or self.player_two_score >= self.winning_score
        ):
            return False
        self.player_ai_movement()
        self.calculate_player_movement()
        self.move_ball()
        self.check_collision()
        return True

    def generate(
        self,
        image_filename: str,
        frames_output_fpath="frames.json",
        dark_svg_path: str = "pong_dark.svg",
        light_svg_path: str = "pong_light.svg",
    ):
        logging.info("Starting simulation...")
        self.create_ball()

        player_one_x = round(self.player_one_paddle["x"], 1)
        player_two_x = round(self.player_two_paddle["x"], 1)

        ball_frames = [[round(self.ball_x, 1), round(self.ball_y, 1), 0]]
        player_one_frames = [[round(self.player_one_paddle["y"], 1), 0]]
        player_two_frames = [[round(self.player_two_paddle["y"], 1), 0]]

        start_time = perf_counter()
        time_offset = 0

        sleep(self.tick_rate_ms / 1000)
        while self.next_tick():
            new_time = perf_counter()
            if new_time == start_time:
                continue
            time_offset = round(time_offset + new_time - start_time, 4)
            start_time = new_time

            ball_frames.append(
                [round(self.ball_x, 1), round(self.ball_y, 1), time_offset]
            )
            player_one_frames.append(
                [round(self.player_one_paddle["y"], 1), time_offset]
            )
            player_two_frames.append(
                [round(self.player_two_paddle["y"], 1), time_offset]
            )

            if (
                self.prev_scores[0] < self.player_one_score
                or self.prev_scores[1] < self.player_two_score
            ):
                self.score_frames.append(
                    [f"{self.player_one_score} | {self.player_two_score}", time_offset]
                )
                self.prev_scores[0] = self.player_one_score
                self.prev_scores[1] = self.player_two_score

            sleep(self.tick_rate_ms / 1000)

        for i in range(len(ball_frames)):
            ball_frames[i][2] = round(ball_frames[i][2] / time_offset, 4)
            player_one_frames[i][1] = round(player_one_frames[i][1] / time_offset, 4)
            player_two_frames[i][1] = round(player_two_frames[i][1] / time_offset, 4)
        for i in range(len(self.score_frames)):
            self.score_frames[i][1] = round(self.score_frames[i][1] / time_offset, 4)

        gen_pong_svg(
            self.canvas_width,
            self.canvas_height,
            self.ball_radius,
            time_offset,
            player_one_x,
            player_two_x,
            self.paddle_width,
            self.paddle_height,
            player_one_frames,
            player_two_frames,
            ball_frames,
            self.score_frames,
            dark_svg_path,
            image_filename,
            primary_color="white",
        )
        gen_pong_svg(
            self.canvas_width,
            self.canvas_height,
            self.ball_radius,
            time_offset,
            player_one_x,
            player_two_x,
            self.paddle_width,
            self.paddle_height,
            player_one_frames,
            player_two_frames,
            ball_frames,
            self.score_frames,
            light_svg_path,
            image_filename,
            primary_color="black",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Game configuration")
    parser.add_argument(
        "-w", "--winning-score", type=int, default=2, help="Set the winning score"
    )
    parser.add_argument(
        "-i", "--image", type=str, help="Filename or URL of the ball image"
    )
    parser.add_argument(
        "-s",
        "--star-mode",
        action="store_true",
        help="Enable gathering the image from the last stargazer of the account",
    )
    parser.add_argument(
        "-a",
        "--avatar-mode",
        action="store_true",
        help="Enable gathering the image from your own GitHub avatar (Default behavior)",
    )
    parser.add_argument(
        "-f",
        "--follower-mode",
        action="store_true",
        help="Enable gathering the image from a random follower of the account",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logs"
    )

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    repo_env = os.getenv("GITHUB_REPOSITORY", "octocat/Hello-World")
    repo_owner = repo_env.split("/")[0]

    # Explicit handling of the typo fix (args.follower_mode)
    # If no flags are provided, it defaults to avatar-mode logic
    if (
        not args.image
        and not args.star_mode
        and not args.avatar_mode
        and not args.follower_mode
    ):
        logging.info("No mode specified. Defaulting to avatar mode.")
        args.avatar_mode = True

    # Image source routing logic
    if args.star_mode:
        img_path = get_last_stargazer_of_account(repo_owner)
    elif args.follower_mode:
        img_path = get_random_follower_avatar(repo_owner)
    elif args.image:
        img_path = args.image
    else:  # avatar_mode or absolute default fallback
        img_path = f"https://github.com/{repo_owner}.png"

    if img_path.startswith("http://") or img_path.startswith("https://"):
        # Scarica comunque localmente per il runner
        download_github_avatar(img_path)

        # Recupera il branch corrente (es. 'main', 'master', 'dev')
        current_branch = os.getenv("GITHUB_REF_NAME", "main")

        # Costruisce l'URL dinamico corretto
        img_path = f"https://raw.githubusercontent.com/{repo_env}/{current_branch}/images/ball_avatar.png"
    else:
        if not os.path.isabs(img_path) and not img_path.startswith("./"):
            img_path = "./" + img_path

    PongGameSvgGenerator(winning_score=args.winning_score).generate(
        image_filename=img_path
    )
