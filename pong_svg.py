import os
import argparse
import logging
from src import (
    PongGameSvgGenerator,
    get_last_stargazer_of_account,
    get_random_follower_avatar,
    download_github_avatar,
    get_base64_data_url,
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

    # Default fallback routing logic
    if (
        not args.image
        and not args.star_mode
        and not args.avatar_mode
        and not args.follower_mode
    ):
        logging.info("No mode specified. Defaulting to avatar mode.")
        args.avatar_mode = True

    # Image source assignment
    if args.star_mode:
        img_source = get_last_stargazer_of_account(repo_owner)
    elif args.follower_mode:
        img_source = get_random_follower_avatar(repo_owner)
    elif args.image:
        img_source = args.image
    else:
        img_source = f"https://github.com/{repo_owner}.png"

    # Handle downloading if source is a URL
    if img_source.startswith("http://") or img_source.startswith("https://"):
        local_avatar_path = download_github_avatar(img_source)
    else:
        local_avatar_path = img_source
        if not os.path.isabs(local_avatar_path) and not local_avatar_path.startswith(
            "./"
        ):
            local_avatar_path = "./" + local_avatar_path

    # Convert the dynamic image asset directly into an inline Base64 Data URL
    logging.info("Converting avatar to Base64 Data URL for standalone SVG embedding...")
    base64_img_url = get_base64_data_url(local_avatar_path)

    if base64_img_url:
        PongGameSvgGenerator(winning_score=args.winning_score).generate(
            image_data_url=base64_img_url
        )
    else:
        logging.warning(
            "Base64 conversion failed. Falling back to raw source rendering path."
        )
        PongGameSvgGenerator(winning_score=args.winning_score).generate(
            image_data_url=img_source
        )
