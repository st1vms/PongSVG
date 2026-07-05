# Pong SVG Generator

Dynamically generate beautiful, dark/light mode-adaptive Pong game animations in SVG format for your GitHub Profile README. The ball features an integrated GitHub avatar, defaulting to your own profile picture!

```html
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="images/pong_dark.svg" />
  <source media="(prefers-color-scheme: light)" srcset="images/pong_light.svg" />
  <img alt="Pong Game Animation" src="images/pong_light.svg" />
</picture>
```

## Features

- **Adaptive Themes:** Generates both dark-mode and light-mode SVGs automatically.
- **Dynamic Avatars:** The game ball displays:
  - Your own profile **avatar** (Default).
  - The avatar of the user who dropped the latest **star** on your account.
  - A **random follower's** avatar.
  - Any **custom image** via URL or local path.
- **Asset Isolation:** The action pre-downloads remote assets locally to ensure they load smoothly in modern web browsers without violating Content Security Policies (CSP).

---

## Configuration Options

| Input | Description | Required | Default |
| :--- | :--- | :--- | :--- |
| `winning-score` | Score at which the match ends and the animation loop resets. | No | `2` |
| `mode` | Dynamic avatar mode: `avatar`, `star`, `follower`, or `custom`. | No | `avatar` |
| `image` | URL or path to a custom image. Only evaluated if `mode: custom`. | No | `""` |

---

## How to Embed This Action Into Your Repository

### 1. Create a GitHub Workflow

Create a new file in your repository at `.github/workflows/pong_game.yaml` with the following contents:

```yaml
name: Generate Pong SVGs

on:
  schedule:
    - cron: "0 * * * *" # Runs every hour
  workflow_dispatch: # Allows manual trigger

jobs:
  generate-pong-svg:
    permissions:
      contents: write
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Generate Pong SVGs
        uses: st1vms/PongSVG@v1.0.0
        with:
          winning-score: 3
          mode: "avatar" # Options: avatar, star, follower, custom (Defaults to avatar)

      - name: Move generated SVGs
        run: |
          mkdir -p images
          mv pong_light.svg images/pong_light.svg
          mv pong_dark.svg images/pong_dark.svg

      - name: Configure git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Commit and push SVGs
        run: |
          git add images/pong_light.svg images/pong_dark.svg
          git commit -m "Update Pong SVGs with latest avatar"
          git push
