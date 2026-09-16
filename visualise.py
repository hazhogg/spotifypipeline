import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host='localhost',
    database='spotify_db',
    user='postgres',
    password=os.environ.get('DB_PASSWORD'),
    port='5432'
)

# ── 1. TOP ARTISTS ─────────────────────────────────────────────────────────
def plot_top_artists():
    df = pd.read_sql("""
        SELECT DISTINCT ON (artist_name) artist_name, rank
        FROM top_artists
        WHERE time_range = 'short_term'
        ORDER BY artist_name, rank
        LIMIT 10
    """, conn)
    df = df.sort_values('rank')

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(df['artist_name'][::-1], 
                   [10 - r for r in df['rank'][::-1]], color='#1DB954')
    ax.set_title('Your Top Artists (Last 4 Weeks)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Score (higher = better ranked)')
    ax.set_xticks([])
    for i, (_, row) in enumerate(df[::-1].iterrows()):
        ax.text(0.1, i, f"#{int(row['rank'])} {row['artist_name']}",
                va='center', fontsize=11, color='white', fontweight='bold')
    ax.set_facecolor('#191414')
    fig.patch.set_facecolor('#191414')
    plt.tight_layout()
    plt.savefig('top_artists.png', dpi=150)
    plt.show()
    print('Saved top_artists.png')

# ── 2. TOP TRACKS ──────────────────────────────────────────────────────────
def plot_top_tracks():
    df = pd.read_sql("""
        SELECT DISTINCT ON (track_name) track_name, artist_name, rank
        FROM top_tracks
        WHERE time_range = 'short_term'
        ORDER BY track_name, rank
        LIMIT 10
    """, conn)
    df = df.sort_values('rank')
    labels = [f"{row['track_name'][:30]} — {row['artist_name']}"
              for _, row in df.iterrows()]

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.barh(labels[::-1], [10 - r for r in df['rank'][::-1]], color='#1DB954')
    ax.set_title('Your Top Tracks (Last 4 Weeks)', fontsize=16, fontweight='bold')
    ax.set_xticks([])
    ax.set_facecolor('#191414')
    fig.patch.set_facecolor('#191414')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_edgecolor('#333333')
    plt.tight_layout()
    plt.savefig('top_tracks.png', dpi=150)
    plt.show()
    print('Saved top_tracks.png')

# ── 3. LISTENING ACTIVITY BY HOUR ──────────────────────────────────────────
def plot_listening_by_hour():
    df = pd.read_sql("""
        SELECT EXTRACT(HOUR FROM played_at) as hour,
               COUNT(*) as plays
        FROM recently_played
        GROUP BY hour
        ORDER BY hour
    """, conn)

    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(df['hour'], df['plays'], color='#1DB954')
    ax.set_title('When Do You Listen? (By Hour)', fontsize=16, fontweight='bold')
    ax.set_xlabel('Hour of Day')
    ax.set_ylabel('Number of Plays')
    ax.set_xticks(range(0, 24))
    ax.set_xticklabels([f'{h:02d}:00' for h in range(24)], rotation=45)
    ax.set_facecolor('#191414')
    fig.patch.set_facecolor('#191414')
    ax.tick_params(colors='white')
    ax.yaxis.label.set_color('white')
    ax.xaxis.label.set_color('white')
    ax.title.set_color('white')
    plt.tight_layout()
    plt.savefig('listening_by_hour.png', dpi=150)
    plt.show()
    print('Saved listening_by_hour.png')

# ── 4. MOST PLAYED ARTISTS (RECENTLY) ─────────────────────────────────────
def plot_recent_artists():
    df = pd.read_sql("""
        SELECT artist_name, COUNT(*) as plays
        FROM recently_played
        GROUP BY artist_name
        ORDER BY plays DESC
        LIMIT 10
    """, conn)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(df['artist_name'], df['plays'], color='#1DB954')
    ax.bar_label(bars, padding=3, color='white')
    ax.set_title('Most Played Artists Recently', fontsize=16, fontweight='bold')
    ax.set_ylabel('Number of Plays')
    plt.xticks(rotation=45, ha='right')
    ax.set_facecolor('#191414')
    fig.patch.set_facecolor('#191414')
    ax.tick_params(colors='white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    plt.tight_layout()
    plt.savefig('recent_artists.png', dpi=150)
    plt.show()
    print('Saved recent_artists.png')

# ── 5. TASTE OVER TIME (SHORT vs LONG TERM) ───────────────────────────────
def plot_taste_comparison():
    short = pd.read_sql("""
        SELECT DISTINCT ON (artist_name) artist_name, rank
        FROM top_artists WHERE time_range = 'short_term'
        ORDER BY artist_name, rank LIMIT 10
    """, conn)

    long = pd.read_sql("""
        SELECT DISTINCT ON (artist_name) artist_name, rank
        FROM top_artists WHERE time_range = 'long_term'
        ORDER BY artist_name, rank LIMIT 10
    """, conn)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    ax1.barh(short['artist_name'][::-1],
             [10 - r for r in short['rank'][::-1]], color='#1DB954')
    ax1.set_title('Last 4 Weeks', fontsize=14, fontweight='bold', color='white')
    ax1.set_xticks([])
    ax1.set_facecolor('#191414')

    ax2.barh(long['artist_name'][::-1],
             [10 - r for r in long['rank'][::-1]], color='#1DB954')
    ax2.set_title('All Time', fontsize=14, fontweight='bold', color='white')
    ax2.set_xticks([])
    ax2.set_facecolor('#191414')

    for ax in [ax1, ax2]:
        ax.tick_params(colors='white')

    fig.patch.set_facecolor('#191414')
    fig.suptitle('Your Taste: Recent vs All Time', fontsize=16,
                 fontweight='bold', color='white')
    plt.tight_layout()
    plt.savefig('taste_comparison.png', dpi=150)
    plt.show()
    print('Saved taste_comparison.png')

# ── RUN ALL ────────────────────────────────────────────────────────────────
print('Generating Spotify visualisations...')
plot_top_artists()
plot_top_tracks()
plot_listening_by_hour()
plot_recent_artists()
plot_taste_comparison()

conn.close()
print('\nAll charts saved!')