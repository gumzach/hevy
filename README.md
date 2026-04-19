# hevy

Hevy Workout App MCP.

## Setup

```bash
# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit .env with your values
```

## Local Development

```bash
# Run the server
./run.sh

# Or directly
uv run hevy
```


## Authentication

This server uses user-provided credentials. In local development, set `ENVIRONMENT=local` and `LOCAL_API_KEY` in your `.env` file.

When deployed to Gumstack, users will enter their api_key in the Gumstack UI.


## Tools

22 tools covering workouts, routines, exercise templates, routine folders, exercise history, body measurements, and user info. See `config.yaml` for the full list.
