# Pong Svg generator

<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="examples/pong_dark.svg"
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="examples/pong_light.svg"
  />
  <img alt="Pong Game" src="examples/pong_light.svg" />
</picture>


## How to embed this action into your repository

### Create a Github workflow in your repository (`.github/workflows/pong_game.yaml`) with this content

```yaml
name: Generates Pong SVGs every hour

on:
  schedule:
      - cron: "0 * * * *"
  workflow_dispatch:

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
          git commit -m "Update Pong SVGs"
          git push
```

*NOTE:* The winning score parameter is used to determine the score at which the game stops and SVG generation begins.

### Import the SVGs into your markdown by pasting this:

```markdown
<picture>
  <source
    media="(prefers-color-scheme: dark)"
    srcset="images/pong_dark.svg"
  />
  <source
    media="(prefers-color-scheme: light)"
    srcset="images/pong_light.svg"
  />
  <img alt="Pong Game" src="images/pong_light.svg" />
</picture>
```
