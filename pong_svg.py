"""Pong simulation"""

import math
from random import randint
from time import sleep, perf_counter
from json import dump
from xml.etree import ElementTree as ET


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
    primary_color: str = "gray",
    score_text_area_height: int = 40,
):
    """Generate pong game animation into an svg using frames"""

    extra_h = score_text_area_height
    total_h = canvas_height + extra_h

    svg = ET.Element(
        "svg",
        xmlns="http://www.w3.org/2000/svg",
        width=str(canvas_width),
        height=str(total_h),
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

    # Score text area background rectangle
    text_bg_height = extra_h
    ET.SubElement(
        svg,
        "rect",
        x="0",
        y=str(canvas_height),
        width=str(canvas_width),
        height=str(text_bg_height),
        fill="transparent",
    )

    # Bottom centered score text
    score_text = ET.SubElement(
        svg,
        "text",
        x=str(canvas_width // 2),  # center horizontally
        y=str(canvas_height + extra_h // 2 + 6),  # vertically centered in text area
        fill=primary_color,
        **{
            "text-anchor": "middle",
            "font-size": "24",
        },
    )

    score_key_times = (
        "0;" + ";".join(str(frame[1]) for frame in score_frames[1:-1]) + ";1"
    )

    frame_tspan = ET.SubElement(
        score_text,
        "tspan",
        opacity="1",
        x=str(canvas_width // 2),  # center horizontally
        y=str(canvas_height + extra_h // 2 + 6),
    )  # vertically centered in text area)
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
            x=str(canvas_width // 2),  # center horizontally
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

    # Generate ball circle element
    ball_circle = ET.SubElement(
        svg,
        "circle",
        cx=str(ball_frames[0][0]),
        cy=str(ball_frames[0][1]),
        r=str(ball_radius),
        fill=primary_color,
    )

    # Animate cx property of ball
    ET.SubElement(
        ball_circle,
        "animate",
        attributeName="cx",
        dur=str(duration),
        repeatCount="indefinite",
        values=";".join([str(frame[0]) for frame in ball_frames]),
        keyTimes=";".join([str(frame[2]) for frame in ball_frames]),
    )

    # Animate cy property of ball
    ET.SubElement(
        ball_circle,
        "animate",
        attributeName="cy",
        dur=str(duration),
        repeatCount="indefinite",
        values=";".join([str(frame[1]) for frame in ball_frames]),
        keyTimes=";".join([str(frame[2]) for frame in ball_frames]),
    )

    # Create player one
    player_one = ET.SubElement(
        svg,
        "rect",
        x=str(player_one_x),
        y=str(player_one_frames[0][0]),
        width=str(player_width),
        height=str(player_height),
        fill=primary_color,
    )

    # Animate player one
    ET.SubElement(
        player_one,
        "animate",
        attributeName="y",
        dur=str(duration),
        repeatCount="indefinite",
        values=";".join([str(frame[0]) for frame in player_one_frames]),
        keyTimes=";".join([str(frame[1]) for frame in player_one_frames]),
    )

    # Create player two
    player_two = ET.SubElement(
        svg,
        "rect",
        x=str(player_two_x),
        y=str(player_two_frames[0][0]),
        width=str(player_width),
        height=str(player_height),
        fill=primary_color,
    )

    # Animate player two
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


class PongGameSvgGenerator:
    """
    A simple Pong game simulation.

    This class simulates a basic Pong game between two AI-controlled players.
    The game runs for a given duration (or until a winning score is reached),
    and stores ball and paddle positions over time into a JSON file for later analysis.

    Attributes
    ----------
    canvas_width : int
        Width of the game area.
    canvas_height : int
        Height of the game area.
    winning_score : int
        Score threshold to win the game.
    tick_rate_ms : int
        Time between simulation ticks in milliseconds.
    paddle_width, paddle_height : int
        Paddle dimensions.
    paddle_speed : int
        Speed of paddle movement.
    paddle_wall_margin : int
        Horizontal distance of paddles from walls.
    ball_radius : float
        Ball radius.
    starting_ball_speed : float
        Initial speed of the ball.
    ball_speed_increase : float
        Increment applied to the ball speed after collisions.
    max_ball_speed : float
        Maximum speed the ball can reach.
    """

    def __init__(
        self, canvas_width: int = 600, canvas_height: int = 300, winning_score: int = 1
    ):
        """
        Initialize a new Pong game instance with the given canvas size.

        Parameters
        ----------
        canvas_width : int, optional
            Width of the game canvas (default is 600).
        canvas_height : int, optional
            Height of the game canvas (default is 300).
        winning_score : int, optional
            The winning score at which the game stops and the svg generation starts (default is 1)
        """
        # Canvas
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

        # Config
        self.winning_score = winning_score
        self.tick_rate_ms = 10

        # Paddle properties
        self.paddle_width = 10
        self.paddle_height = 75
        self.paddle_speed = 5
        self.paddle_wall_margin = 5

        # Ball properties
        self.ball_radius = 7.5
        self.starting_ball_speed = 1
        self.ball_speed_increase = 0.5
        self.max_ball_speed = 10

        # Game state
        self.reset_game()

        # Ball state
        self.ball_x = self.canvas_width / 2
        self.ball_y = self.canvas_height / 2
        self.prev_ball_x = self.ball_x
        self.prev_ball_y = self.ball_y
        self.ball_speed = self.starting_ball_speed
        self.ball_x_dir = 0
        self.ball_y_dir = 0

        # Controls
        self.player_one_up = False
        self.player_one_down = False
        self.player_two_up = False
        self.player_two_down = False

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

        self.tick_thread = None

        self.prev_scores = [0, 0]  # Initial score memory
        self.score_frames = [["0 | 0", 0]]  # Initial score text frame

    def reset_game(self):
        """
        Reset scores and paddle positions to their initial states.
        """
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

    def create_ball(self):
        """
        Reset the ball position to the center and assign a new starting direction
        based on current score.
        """
        self.ball_speed = self.starting_ball_speed

        if self.player_one_score == self.player_two_score:
            self.ball_x_dir = 1 if randint(0, 1) == 1 else -1
        elif self.player_one_score > self.player_two_score:
            self.ball_x_dir = -1
        else:
            self.ball_x_dir = 1

        self.ball_y_dir = 1 if randint(0, 1) == 1 else -1

        self.ball_x = self.canvas_width / 2
        self.ball_y = self.canvas_height / 2

    def move_ball(self):
        """
        Update the ball's position according to its current speed and direction.
        """
        self.ball_x += self.ball_speed * self.ball_x_dir
        self.ball_y += self.ball_speed * self.ball_y_dir

    def calculate_player_movement(self):
        """
        Update paddle positions based on movement flags and enforce canvas boundaries.
        """
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
        """
        Handle collisions between the ball, walls, and paddles.
        Update ball trajectory and player scores as needed.
        """
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

        # Paddle one
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
                paddle_center = (
                    self.player_one_paddle["y"] + self.player_one_paddle["height"] / 2
                )
                distance = self.ball_y - paddle_center
                normalized = distance / (self.player_one_paddle["height"] / 2)
                bounce_angle = normalized * (math.pi / 3)
                self.ball_x_dir = abs(math.cos(bounce_angle))
                self.ball_y_dir = math.sin(bounce_angle)
                if self.ball_speed + self.ball_speed_increase <= self.max_ball_speed:
                    self.ball_speed += self.ball_speed_increase

        # Paddle two
        if self.ball_x >= self.player_two_paddle["x"] - self.ball_radius:
            if (
                self.player_two_paddle["y"]
                < self.ball_y
                < self.player_two_paddle["y"] + self.player_two_paddle["height"]
            ):
                self.ball_x = self.player_two_paddle["x"] - self.ball_radius
                paddle_center = (
                    self.player_two_paddle["y"] + self.player_two_paddle["height"] / 2
                )
                distance = self.ball_y - paddle_center
                normalized = distance / (self.player_two_paddle["height"] / 2)
                bounce_angle = normalized * (math.pi / 3)
                self.ball_x_dir = -abs(math.cos(bounce_angle))
                self.ball_y_dir = math.sin(bounce_angle)
                if self.ball_speed + self.ball_speed_increase <= self.max_ball_speed:
                    self.ball_speed += self.ball_speed_increase

    def player_ai_movement(self):
        """
        Simple AI logic for predicting ball trajectory and moving paddles
        towards the predicted collision point.
        """
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
        """
        Perform a single game tick:
        - check for winning conditions
        - update AI decisions
        - move paddles and ball
        - check collisions

        Returns
        -------
        bool
            True if the game continues, False if it should stop.
        """
        if (
            self.player_one_score >= self.winning_score
            or self.player_two_score >= self.winning_score
        ):
            self.reset_game()
            return False

        self.player_ai_movement()
        self.calculate_player_movement()
        self.move_ball()
        self.check_collision()

        return True

    def generate(
        self,
        frames_output_fpath="frames.json",
        dark_svg_path: str = "pong_dark.svg",
        light_svg_path: str = "pong_light.svg",
    ):
        """
        Run the Pong game simulation.

        The game runs for up to 60 seconds of simulated time, recording
        the ball and paddle positions at each tick. Results are saved
        to the given output JSON file.

        Parameters
        ----------
        output_path : str, optional
            Path of the JSON file where frames will be saved
            (default is "frames.json").
        """
        self.create_ball()

        player_one_x = round(self.player_one_paddle["x"], 1)
        player_two_x = round(self.player_two_paddle["x"], 1)

        ball_frames = [[round(self.ball_x, 1), round(self.ball_y, 1), 0]]
        player_one_frames = [
            [
                round(self.player_one_paddle["y"], 1),
                0,
            ]
        ]
        player_two_frames = [
            [
                round(self.player_two_paddle["y"], 1),
                0,
            ]
        ]

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
                [
                    round(self.player_one_paddle["y"], 1),
                    time_offset,
                ]
            )
            player_two_frames.append(
                [
                    round(self.player_two_paddle["y"], 1),
                    time_offset,
                ]
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

        # Normalize ball/player frames key times [0, 1.0]
        frame_len = len(ball_frames)
        for i in range(frame_len):
            ball_frames[i][2] = round(ball_frames[i][2] / time_offset, 4)
            player_one_frames[i][1] = round(player_one_frames[i][1] / time_offset, 4)
            player_two_frames[i][1] = round(player_two_frames[i][1] / time_offset, 4)

        # Normalize score text frames key times [0, 1.0]
        frame_len = len(self.score_frames)
        for i in range(frame_len):
            self.score_frames[i][1] = round(self.score_frames[i][1] / time_offset, 4)

        # Generate dark svg
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
            primary_color="white",
        )

        # Generate light svg
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
            primary_color="black",
        )

        # Dump data for debug purposes
        with open(frames_output_fpath, "w", encoding="utf-8", errors="ignore") as fp:
            dump(
                {
                    "duration": time_offset,
                    "player_one_x": player_one_x,
                    "player_two_x": player_two_x,
                    "player_width": self.paddle_width,
                    "player_height": self.paddle_height,
                    "player_one_frames": player_one_frames,
                    "player_two_frames": player_two_frames,
                    "ball_frames": ball_frames,
                    "score_frames": self.score_frames,
                },
                fp,
                indent=4,
            )


if __name__ == "__main__":
    PongGameSvgGenerator(winning_score=3).generate()
