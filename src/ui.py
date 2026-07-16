import logging
from time import perf_counter, sleep
from random import randint
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
    image_data_url: str,
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
        href=image_data_url,
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
        image_data_url: str,
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
            image_data_url,
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
            image_data_url,
            primary_color="black",
        )
