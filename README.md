# Spotify Listening Pipeline

An automated data pipeline that pulls your personal Spotify listening data, stores it in PostgreSQL and generates visualisations showing your music taste and listening patterns.

## What it does

- Fetches your recently played tracks (last 50)
- Pulls your top tracks across 3 time ranges (last 4 weeks, 6 months, all time)
- Pulls your top artists across 3 time ranges
- Stores all data in PostgreSQL
- Generates 5 Spotify-themed visualisation charts
- Updates automatically every 6 hours

## Time ranges

| Range | Description |
|---|---|
| short_term | Last 4 weeks |
| medium_term | Last 6 months |
| long_term | All time |

## Tech stack

- Python
- pandas
- PostgreSQL
- psycopg2
- Spotipy (Spotify API wrapper)
- Spotify Web API
- schedule
- matplotlib

## Sample output

```
Top 5 tracks (last 4 weeks):
 rank               track_name   artist_name
    1                    BANG!  Trippie Redd
    2             Heart On Ice      Rod Wave
    3         Look At Me Momma      Rod Wave
    4 Mainstay (feat. Luv Von)      Rod Wave
    5            Taking A Walk  Trippie Redd

Top 5 artists (last 4 weeks):
 rank   artist_name
    1      Rod Wave
    2  Trippie Redd

Most recently played:
                      track_name   artist_name               played_at
                   It Takes Time  Trippie Redd 2026-09-13 18:13:22
                   Taking A Walk  Trippie Redd 2026-09-13 18:06:26
       Immortal (feat. The Game)  Trippie Redd 2026-09-13 18:04:16
                     Janice STFU         Drake 2026-09-13 16:11:45
Turks & Caicos (feat. 21 Savage)      Rod Wave 2026-09-13 14:53:05
```

## Database tables

### recently_played
Your listening history:

| Column | Description |
|---|---|
| track_id | Spotify track ID |
| track_name | Track title |
| artist_name | Artist name |
| album_name | Album name |
| played_at | When you listened |
| duration_ms | Track length in milliseconds |

### top_tracks
Your top tracks per time range:

| Column | Description |
|---|---|
| track_id | Spotify track ID |
| track_name | Track title |
| artist_name | Artist name |
| popularity | Spotify popularity score |
| time_range | short_term / medium_term / long_term |
| rank | Position in your top 50 |

### top_artists
Your top artists per time range:

| Column | Description |
|---|---|
| artist_id | Spotify artist ID |
| artist_name | Artist name |
| genres | Music genres |
| popularity | Spotify popularity score |
| followers | Total followers on Spotify |
| time_range | short_term / medium_term / long_term |
| rank | Position in your top 50 |

## Setup

### 1. Create a Spotify Developer App

1. Go to https://developer.spotify.com/dashboard
2. Click **Create App**
3. Fill in app name and description
4. Add redirect URI: `https://oauth.pstmn.io/v1/callback`
5. Select **Web API**
6. Copy your **Client ID** and **Client Secret**

### 2. Clone the repo

```bash
git clone https://github.com/yourusername/spotify-pipeline.git
cd spotify-pipeline
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

```
DB_PASSWORD=yourpassword
DB_HOST=localhost
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
```

### 5. Run the pipeline

```bash
python spotify_pipeline.py
```

On first run a browser window will open asking you to log in to Spotify and authorise the app. After that it runs automatically.

## Visualisations

```bash
python visualise.py
```

Generates 5 Spotify-themed dark mode charts:
- Top artists (last 4 weeks)
- Top tracks (last 4 weeks)
- Listening activity by hour of day
- Most played artists recently
- Taste comparison — recent vs all time

## Example queries

```sql
-- Your most listened to artists ever
SELECT artist_name, rank
FROM top_artists
WHERE time_range = 'long_term'
ORDER BY rank
LIMIT 10;

-- What time of day do you listen most?
SELECT EXTRACT(HOUR FROM played_at) as hour,
       COUNT(*) as plays
FROM recently_played
GROUP BY hour
ORDER BY plays DESC;

-- Tracks you keep coming back to
SELECT track_name, artist_name, COUNT(*) as times_played
FROM recently_played
GROUP BY track_name, artist_name
ORDER BY times_played DESC
LIMIT 10;

-- How has your taste changed?
SELECT time_range, artist_name, rank
FROM top_artists
WHERE artist_name = 'Rod Wave'
ORDER BY time_range;
```

## Schedule

Pipeline runs automatically every 6 hours collecting your latest listening data. The longer you run it the more historical data you accumulate.

## Project structure

```
spotify-pipeline/
├── spotify_pipeline.py  ← main ETL pipeline
├── visualise.py         ← chart generation
├── requirements.txt     ← dependencies
├── .gitignore           ← excludes .env, .cache and charts
└── .env                 ← Spotify credentials (not pushed)
```

## Note on OAuth

Spotify uses OAuth 2.0 authentication. On first run you will be redirected to Spotify to log in and authorise the app. Spotipy saves your token in a `.cache` file locally so you only need to do this once. The `.cache` file is excluded from GitHub via `.gitignore`.

## Author

Harry
