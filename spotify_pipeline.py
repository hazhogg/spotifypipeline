import spotipy
from spotipy.oauth2 import SpotifyOAuth
import psycopg2
import pandas as pd
import os
import schedule
import time
import warnings
from datetime import datetime
from dotenv import load_dotenv
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

warnings.filterwarnings('ignore')
load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     os.environ.get('DB_HOST', 'localhost'),
    'database': 'spotify_db',
    'user':     'postgres',
    'password': os.environ.get('DB_PASSWORD'),
    'port':     '5432'
}

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.environ.get('SPOTIFY_CLIENT_ID'),
    client_secret=os.environ.get('SPOTIFY_CLIENT_SECRET'),
    redirect_uri='https://oauth.pstmn.io/v1/callback',
    scope='user-read-recently-played user-top-read user-library-read'
))

# ── SETUP DATABASE ─────────────────────────────────────────────────────────
def setup_database():
    try:
        setup_conn = psycopg2.connect(
            host='localhost', database='postgres',
            user='postgres', password=os.environ.get('DB_PASSWORD'), port='5432'
        )
        setup_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        setup_conn.cursor().execute('CREATE DATABASE spotify_db')
        setup_conn.close()
        print('spotify_db created!')
    except Exception as e:
        print(f'Database note: {e}')

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recently_played (
            id           SERIAL PRIMARY KEY,
            track_id     VARCHAR(100),
            track_name   VARCHAR(200),
            artist_name  VARCHAR(200),
            album_name   VARCHAR(200),
            played_at    TIMESTAMP,
            duration_ms  INTEGER,
            fetched_at   TIMESTAMP,
            UNIQUE(track_id, played_at)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS top_tracks (
            id           SERIAL PRIMARY KEY,
            track_id     VARCHAR(100),
            track_name   VARCHAR(200),
            artist_name  VARCHAR(200),
            album_name   VARCHAR(200),
            popularity   INTEGER,
            time_range   VARCHAR(20),
            rank         INTEGER,
            duration_ms  INTEGER,
            fetched_at   TIMESTAMP,
            UNIQUE(track_id, time_range, fetched_at)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS top_artists (
            id           SERIAL PRIMARY KEY,
            artist_id    VARCHAR(100),
            artist_name  VARCHAR(200),
            genres       TEXT,
            popularity   INTEGER,
            followers    INTEGER,
            time_range   VARCHAR(20),
            rank         INTEGER,
            fetched_at   TIMESTAMP,
            UNIQUE(artist_id, time_range, fetched_at)
        )
    """)

    conn.commit()
    conn.close()
    print('Database ready!')

# ── EXTRACT & TRANSFORM ────────────────────────────────────────────────────
def extract_recently_played():
    print('  Extracting recently played...')
    results = sp.current_user_recently_played(limit=50)
    rows = []
    for item in results['items']:
        track = item['track']
        rows.append({
            'track_id':    track['id'],
            'track_name':  track['name'],
            'artist_name': track['artists'][0]['name'],
            'album_name':  track['album']['name'],
            'played_at':   item['played_at'],
            'duration_ms': track['duration_ms'],
            'fetched_at':  datetime.now(),
        })
    return pd.DataFrame(rows)

def extract_top_tracks(time_range='short_term'):
    print(f'  Extracting top tracks ({time_range})...')
    results = sp.current_user_top_tracks(limit=50, time_range=time_range)
    rows = []
    for i, track in enumerate(results['items'], 1):
        rows.append({
            'track_id':    track['id'],
            'track_name':  track['name'],
            'artist_name': track['artists'][0]['name'],
            'album_name':  track['album']['name'],
            'popularity':  track.get('popularity', 0),  # ← add .get()
            'time_range':  time_range,
            'rank':        i,
            'duration_ms': track.get('duration_ms', 0),  # ← add .get()
            'fetched_at':  datetime.now(),
        })
    return pd.DataFrame(rows)

def extract_top_artists(time_range='short_term'):
    print(f'  Extracting top artists ({time_range})...')
    results = sp.current_user_top_artists(limit=50, time_range=time_range)
    rows = []
    for i, artist in enumerate(results['items'], 1):
        rows.append({
            'artist_id':   artist.get('id', ''),
            'artist_name': artist.get('name', ''),
            'genres':      ', '.join(artist.get('genres', [])),
            'popularity':  artist.get('popularity', 0),
            'followers':   artist.get('followers', {}).get('total', 0),
            'time_range':  time_range,
            'rank':        i,
            'fetched_at':  datetime.now(),
        })
    return pd.DataFrame(rows)
    
# ── LOAD ───────────────────────────────────────────────────────────────────
def load_recently_played(df, conn):
    print(f'  Loading {len(df)} recently played tracks...')
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO recently_played
                (track_id, track_name, artist_name, album_name,
                 played_at, duration_ms, fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (track_id, played_at) DO NOTHING
            """, tuple(row))
        except Exception as e:
            continue
    conn.commit()

def load_top_tracks(df, conn):
    print(f'  Loading {len(df)} top tracks...')
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO top_tracks
                (track_id, track_name, artist_name, album_name,
                 popularity, time_range, rank, duration_ms, fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (track_id, time_range, fetched_at) DO NOTHING
            """, tuple(row))
        except Exception as e:
            continue
    conn.commit()

def load_top_artists(df, conn):
    print(f'  Loading {len(df)} top artists...')
    cursor = conn.cursor()
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO top_artists
                (artist_id, artist_name, genres, popularity,
                 followers, time_range, rank, fetched_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (artist_id, time_range, fetched_at) DO NOTHING
            """, tuple(row))
        except Exception as e:
            continue
    conn.commit()

# ── MAIN PIPELINE ──────────────────────────────────────────────────────────
def run_pipeline():
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] Running Spotify pipeline...')
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True

        # Recently played
        print('\nRecently Played:')
        rp_df = extract_recently_played()
        load_recently_played(rp_df, conn)

        # Top tracks — all 3 time ranges
        print('\nTop Tracks:')
        for time_range in ['short_term', 'medium_term', 'long_term']:
            df = extract_top_tracks(time_range)
            load_top_tracks(df, conn)

        # Top artists — all 3 time ranges
        print('\nTop Artists:')
        for time_range in ['short_term', 'medium_term', 'long_term']:
            df = extract_top_artists(time_range)
            load_top_artists(df, conn)

        # Summary
        print('\n--- Your Spotify Summary ---')

        print('\nTop 5 tracks (last 4 weeks):')
        top5 = pd.read_sql("""
            SELECT rank, track_name, artist_name, popularity
            FROM top_tracks
            WHERE time_range = 'short_term'
            ORDER BY fetched_at DESC, rank
            LIMIT 5
        """, conn)
        print(top5.to_string(index=False))

        print('\nTop 5 artists (last 4 weeks):')
        top5a = pd.read_sql("""
            SELECT DISTINCT ON (artist_name) rank, artist_name, genres, popularity
            FROM top_artists
            WHERE time_range = 'short_term'
            ORDER BY artist_name, rank
            LIMIT 5
        """, conn)
        print(top5a.to_string(index=False))

        print('\nMost recently played:')
        recent = pd.read_sql("""
            SELECT track_name, artist_name, played_at
            FROM recently_played
            ORDER BY played_at DESC
            LIMIT 5
        """, conn)
        print(recent.to_string(index=False))

        conn.close()
        print('\n✅ Pipeline complete!')

    except Exception as e:
        print(f'❌ Pipeline failed: {e}')

# ── RUN ────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    setup_database()
    run_pipeline()

    # Update every 6 hours
    schedule.every(6).hours.do(run_pipeline)

    print('\nScheduler running — updates every 6 hours.')
    print('Press Ctrl+C to stop.\n')

    while True:
        schedule.run_pending()
        time.sleep(60)