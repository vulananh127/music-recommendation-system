import psycopg2
import os
import sys

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = int(os.environ.get("DB_PORT", "5432"))
DB_USER = os.environ.get("DB_USER", "reco_user")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "reco_pass")
DB_NAME = os.environ.get("DB_NAME", "reco_db")

def connect_db():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT,
        user=DB_USER, password=DB_PASSWORD,
        dbname=DB_NAME
    )

def load_tracks(csv_path):
    conn = connect_db()
    conn.autocommit = True
    cur = conn.cursor()
    print("Delete all old data if it exists")
    cur.execute(""" TRUNCATE TABLE staging_tracks; """)
    cur.execute(""" SELECT COUNT(*) FROM staging_tracks; """)
    after_truncated = cur.fetchone()[0]
    truncated_count = after_truncated
    print("Totals records after truncated: ", truncated_count)
    print("Import tracks CSV -> staging_tracks")
    with open(csv_path, "r", encoding="utf-8") as f:
        cur.copy_expert("""
            COPY staging_tracks(pid,pos,track_uri,track_name,artist_name,artist_uri,album_name,album_uri,duration_ms)
            FROM STDIN WITH CSV HEADER
        """, f)
    print("import tracks successfully !!!")
    cur.execute(""" SELECT COUNT(*) FROM staging_tracks; """)
    records_count = cur.fetchone()[0]
    inserted_count = records_count
    print("Totals records: ", inserted_count)
    cur.close()
    conn.close()

def load_playlists(csv_path):
    conn = connect_db()
    conn.autocommit = True
    cur = conn.cursor()
    print("Delete all old data if it exists")
    cur.execute("""TRUNCATE TABLE staging_playlists""")
    cur.execute(""" SELECT COUNT(*) FROM staging_playlists; """)
    after_truncated = cur.fetchone()[0]
    truncated_count = after_truncated
    print("Totals records after truncated: ", truncated_count)
    print("Import playlists CSV -> staging_playlists")
    with open(csv_path, "r", encoding="utf-8") as f:
        cur.copy_expert("""
            COPY staging_playlists(pid,name,num_tracks,num_samples,num_holdouts,actual_track_count)
            FROM STDIN WITH CSV HEADER
        """, f)
    print("import playlists successfully !!!")
    cur.execute(""" SELECT COUNT(*) FROM staging_playlists; """)
    records_count = cur.fetchone()[0]
    inserted_count = records_count
    print("Totals records: ", inserted_count)
    cur.close()
    conn.close()

def load_artist_rules(csv_path):
    conn = connect_db()
    conn.autocommit = True
    cur = conn.cursor()
    print("Delete all old data if it exists")
    cur.execute("""TRUNCATE TABLE staging_artist_rules""")
    cur.execute(""" SELECT COUNT(*) FROM staging_artist_rules; """)
    after_truncated = cur.fetchone()[0]
    truncated_count = after_truncated
    print("Totals records after truncated: ", truncated_count)
    print("Import artist_rules CSV -> staging_artist_rules")
    with open(csv_path, "r", encoding="utf-8") as f:
        cur.copy_expert("""
            COPY staging_artist_rules(antecedents,consequents,antecedent_names,consequent_names,support,confidence,lift,conviction,antecedent_len,consequent_len)
            FROM STDIN WITH CSV HEADER
        """, f)
    print("import artist_rules successfully !!!")
    cur.execute(""" SELECT COUNT(*) FROM staging_artist_rules; """)
    records_count = cur.fetchone()[0]
    inserted_count = records_count
    print("Totals records: ", inserted_count)
    cur.close()
    conn.close()

def load_track_rules(csv_path):
    conn = connect_db()
    conn.autocommit = True
    cur = conn.cursor()
    print("Delete all old data if it exists")
    cur.execute("""TRUNCATE TABLE staging_track_rules""")
    cur.execute(""" SELECT COUNT(*) FROM staging_track_rules; """)
    after_truncated = cur.fetchone()[0]
    truncated_count = after_truncated
    print("Totals records after truncated: ", truncated_count)
    print("Import track_rules CSV -> staging_track_rules")
    with open(csv_path, "r", encoding="utf-8") as f:
        cur.copy_expert("""
            COPY staging_track_rules(antecedents,consequents,antecedent_names,consequent_names,support,confidence,lift,conviction,antecedent_len,consequent_len)
            FROM STDIN WITH CSV HEADER
        """, f)
    print("Import track_rules CSV -> staging_track_rules Done")
    cur.execute(""" SELECT COUNT(*) FROM staging_track_rules; """)
    records_count = cur.fetchone()[0]
    inserted_count = records_count
    print("Totals records: ", inserted_count)
    cur.close()
    conn.close()

def load_track_frequency(csv_path):
    conn = connect_db()
    conn.autocommit = True
    cur = conn.cursor()
    print("Delete all old data if it exists")
    cur.execute("""TRUNCATE TABLE staging_track_frequency""")
    cur.execute(""" SELECT COUNT(*) FROM staging_track_frequency; """)
    after_truncated = cur.fetchone()[0]
    truncated_count = after_truncated
    print("Totals records after truncated: ", truncated_count)
    print("Import track_frequency CSV -> staging_track_frequency")
    with open(csv_path, "r", encoding="utf-8") as f:
        cur.copy_expert("""
            COPY staging_track_frequency(track_uri, frequency, track_name, artist_name, artist_uri)
            FROM STDIN WITH CSV HEADER
        """, f)
    print("import track_frequency successfully !!!")
    cur.execute(""" SELECT COUNT(*) FROM staging_track_frequency; """)
    records_count = cur.fetchone()[0]
    inserted_count = records_count
    print("Totals records: ", inserted_count)
    cur.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python loader.py [table]")
        print("table = tracks | playlists | artist_rules | track_rules")
        sys.exit(1)

    table = sys.argv[1]
    csv_path = sys.argv[2]


    if table == "tracks":
        load_tracks(csv_path)
    elif table == "playlists":
        load_playlists(csv_path)
    elif table == "artist_rules":
        load_artist_rules(csv_path)
    elif table == "track_rules":
        load_track_rules(csv_path)
    elif table == "track_frequency":
        load_track_frequency(csv_path)
    else:
        print("Unknown table option")   

# Example usage:
#python loaders/loader.py tracks data/track.csv batch_20251214
#python loaders/loader.py playlists data/playlist.csv batch_20251214
#python loaders/loader.py artist_rules data/rules_artist.csv batch_20251214
#python loaders/loader.py track_rules data/rules_track.csv batch_20251214
#python loaders/loader.py track_frequency data/track_frequency.csv batch_20251214 