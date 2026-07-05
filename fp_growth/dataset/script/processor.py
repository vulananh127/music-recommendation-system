import json
import pandas as pd
from collections import Counter
from itertools import combinations
import numpy as np

class SpotifyDataPreprocessing:

    def __init__(self, json_path):
        self.json_path = json_path
        self.raw_data = None
        self.df_playlist = None
        self.df_track = None
        self.track_frequency = None
        self.pair_cooccurrence = None
        self.artist_frequency = None
        self.artist_cooccurrence = None
        
    def load_json(self):
        print("Đang load dữ liệu JSON...")
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        
        print(f"Đã load {len(self.raw_data['playlists'])} playlists")
        print(f"   Dataset version: {self.raw_data['version']}")
        print(f"   Date: {self.raw_data['date']}")
        return self
    
    def split_tables(self):
        print("\n Đang tách dữ liệu thành 2 bảng...")
        
        playlist_records = []
        track_records = []
        
        for playlist in self.raw_data['playlists']:
            pid = playlist['pid']
            playlist_records.append({
                'pid': pid,
                'name': playlist.get('name', ''),
                'num_tracks': playlist['num_tracks'],
                'num_samples': playlist['num_samples'],
                'num_holdouts': playlist['num_holdouts']
            })
            
            for track in playlist.get('tracks', []):
                track_records.append({
                    'pid': pid,
                    'pos': track['pos'],
                    'track_uri': track['track_uri'],
                    'track_name': track['track_name'],
                    'artist_name': track['artist_name'],
                    'artist_uri': track['artist_uri'],
                    'album_name': track['album_name'],
                    'album_uri': track['album_uri'],
                    'duration_ms': track['duration_ms']
                })
        
        self.df_playlist = pd.DataFrame(playlist_records)
        self.df_track = pd.DataFrame(track_records)
        
        print(f" Playlist table: {len(self.df_playlist)} playlists")
        print(f" Track table: {len(self.df_track)} track records")
        return self
    
    def clean_and_filter(self, min_tracks=3):
        print(f"\n Đang làm sạch dữ liệu...")
        
        print("   → Loại bỏ duplicate tracks (cùng pid, track_uri, pos)...")
        original_track_count = len(self.df_track)
        self.df_track = self.df_track.drop_duplicates(
            subset=['pid', 'track_uri', 'pos'],
            keep='first'
        )
        removed_duplicates = original_track_count - len(self.df_track)
        print(f"     Đã loại {removed_duplicates} duplicate records")
        
        track_counts = self.df_track.groupby('pid').size().reset_index(name='actual_track_count')
        self.df_playlist = self.df_playlist.merge(track_counts, on='pid', how='left')
        self.df_playlist['actual_track_count'] = self.df_playlist['actual_track_count'].fillna(0).astype(int)

        print(f"   → Lọc playlists có ít hơn {min_tracks} bài hát...")
        original_playlist_count = len(self.df_playlist)
        valid_playlists = self.df_playlist[self.df_playlist['actual_track_count'] >= min_tracks]['pid']
        self.df_playlist = self.df_playlist[self.df_playlist['pid'].isin(valid_playlists)]
        self.df_track = self.df_track[self.df_track['pid'].isin(valid_playlists)]
        removed_playlists = original_playlist_count - len(self.df_playlist)
        print(f"     Đã loại {removed_playlists} playlists ngắn")
        
        print("   → Chuẩn hóa track_uri làm định danh chính...")
        print(f"     Số track_uri duy nhất: {self.df_track['track_uri'].nunique()}")
        
        print(f"\n Kết quả sau làm sạch:")
        print(f"   Playlists: {len(self.df_playlist)}")
        print(f"   Track records: {len(self.df_track)}")
        print(f"   Unique tracks: {self.df_track['track_uri'].nunique()}")
        print(f"   Unique artists: {self.df_track['artist_uri'].nunique()}")
        return self
    
    def analyze_data_richness(self, top_n=20, min_cooccurrence=5):
        print(f"\n Phân tích độ giàu dữ liệu...")
        
        # Phân tích tần suất track
        print(f"   → Tính tần suất xuất hiện của bài hát...")
        track_freq = self.df_track['track_uri'].value_counts()
        self.track_frequency = track_freq.to_frame('frequency').reset_index()
        self.track_frequency.columns = ['track_uri', 'frequency']
        
        track_info = self.df_track[['track_uri', 'track_name', 'artist_name', 'artist_uri']].drop_duplicates()
        self.track_frequency = self.track_frequency.merge(track_info, on='track_uri', how='left')

        
        print(f"\n   🎵 TOP {top_n} BÀI HÁT PHỔ BIẾN NHẤT:")
        for idx, row in self.track_frequency.head(top_n).iterrows():
            print(f"      {idx+1}. {row['track_name']} - {row['artist_name']} ({row['frequency']} playlists)")
        
        # Phân tích tần suất artist
        print(f"\n   → Tính tần suất xuất hiện của nghệ sĩ...")
        artist_freq = self.df_track['artist_uri'].value_counts()
        self.artist_frequency = artist_freq.to_frame('frequency').reset_index()
        self.artist_frequency.columns = ['artist_uri', 'frequency']
        
        artist_info = self.df_track[['artist_uri', 'artist_name']].drop_duplicates()
        self.artist_frequency = self.artist_frequency.merge(artist_info, on='artist_uri', how='left')
        
        print(f"\n   🎤 TOP {top_n} NGHỆ SĨ PHỔ BIẾN NHẤT:")
        for idx, row in self.artist_frequency.head(top_n).iterrows():
            print(f"      {idx+1}. {row['artist_name']} ({row['frequency']} playlists)")
        
        # Đồng xuất hiện track
        print(f"\n   → Tính đồng xuất hiện cặp bài hát...")
        track_pair_counts = Counter()
        
        playlist_track_groups = self.df_track.groupby('pid')['track_uri'].apply(list)
        
        for tracks in playlist_track_groups:
            if len(tracks) >= 2:
                for pair in combinations(sorted(set(tracks)), 2):
                    track_pair_counts[pair] += 1
        
        filtered_track_pairs = {pair: count for pair, count in track_pair_counts.items() 
                               if count >= min_cooccurrence}
        
        self.pair_cooccurrence = pd.DataFrame([
            {'track_uri_1': pair[0], 'track_uri_2': pair[1], 'cooccurrence': count}
            for pair, count in filtered_track_pairs.items()
        ]).sort_values('cooccurrence', ascending=False)
        
        print(f"    Tìm thấy {len(self.pair_cooccurrence)} cặp bài hát (cooccurrence >= {min_cooccurrence})")
        
        if len(self.pair_cooccurrence) > 0:
            print(f"\n   TOP 10 CẶP BÀI HÁT ĐỒNG XUẤT HIỆN NHẤT:")
            for idx, row in self.pair_cooccurrence.head(10).iterrows():
                track1_name = self.df_track[self.df_track['track_uri'] == row['track_uri_1']]['track_name'].iloc[0]
                track2_name = self.df_track[self.df_track['track_uri'] == row['track_uri_2']]['track_name'].iloc[0]
                print(f"      {idx+1}. [{track1_name}] <-> [{track2_name}] ({row['cooccurrence']} playlists)")
        
        # Đồng xuất hiện artist
        print(f"\n   → Tính đồng xuất hiện cặp nghệ sĩ...")
        artist_pair_counts = Counter()
        
        playlist_artist_groups = self.df_track.groupby('pid')['artist_uri'].apply(list)
        
        for artists in playlist_artist_groups:
            if len(artists) >= 2:
                for pair in combinations(sorted(set(artists)), 2):
                    artist_pair_counts[pair] += 1
        
        filtered_artist_pairs = {pair: count for pair, count in artist_pair_counts.items() 
                                if count >= min_cooccurrence}
        
        self.artist_cooccurrence = pd.DataFrame([
            {'artist_uri_1': pair[0], 'artist_uri_2': pair[1], 'cooccurrence': count}
            for pair, count in filtered_artist_pairs.items()
        ]).sort_values('cooccurrence', ascending=False)
        
        print(f"    Tìm thấy {len(self.artist_cooccurrence)} cặp nghệ sĩ (cooccurrence >= {min_cooccurrence})")
        
        if len(self.artist_cooccurrence) > 0:
            print(f"\n   TOP 10 CẶP NGHỆ SĨ ĐỒNG XUẤT HIỆN NHẤT:")
            for idx, row in self.artist_cooccurrence.head(10).iterrows():
                artist1_name = self.df_track[self.df_track['artist_uri'] == row['artist_uri_1']]['artist_name'].iloc[0]
                artist2_name = self.df_track[self.df_track['artist_uri'] == row['artist_uri_2']]['artist_name'].iloc[0]
                print(f"      {idx+1}. [{artist1_name}] <-> [{artist2_name}] ({row['cooccurrence']} playlists)")
        
        return self
    
    def get_summary_statistics(self):
        stats = {
            'total_playlists': len(self.df_playlist),
            'total_track_records': len(self.df_track),
            'unique_tracks': self.df_track['track_uri'].nunique(),
            'unique_artists': self.df_track['artist_uri'].nunique(),
            'unique_albums': self.df_track['album_uri'].nunique(),
            'avg_tracks_per_playlist': self.df_track.groupby('pid').size().mean(),
            'median_tracks_per_playlist': self.df_track.groupby('pid').size().median(),
            'total_cooccurrence_pairs': len(self.pair_cooccurrence) if self.pair_cooccurrence is not None else 0,
            'total_artist_cooccurrence_pairs': len(self.artist_cooccurrence) if self.artist_cooccurrence is not None else 0
        }
        return stats
    
    def save_cleaned_data(self, output_dir='../data/processed'):
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n Đang lưu dữ liệu đã xử lý vào {output_dir}...")
        
        self.df_playlist.to_csv(f'{output_dir}/playlist_clean.csv', index=False, encoding='utf-8')
        self.df_track.to_csv(f'{output_dir}/track_clean.csv', index=False, encoding='utf-8')
        self.track_frequency.to_csv(f'{output_dir}/track_frequency.csv', index=False, encoding='utf-8')
        self.artist_frequency.to_csv(f'{output_dir}/artist_frequency.csv', index=False, encoding='utf-8')
        
        if self.pair_cooccurrence is not None and len(self.pair_cooccurrence) > 0:
            self.pair_cooccurrence.to_csv(f'{output_dir}/pair_cooccurrence.csv', index=False, encoding='utf-8')
        
        if self.artist_cooccurrence is not None and len(self.artist_cooccurrence) > 0:
            self.artist_cooccurrence.to_csv(f'{output_dir}/artist_cooccurrence.csv', index=False, encoding='utf-8')
        
        print(" Đã lưu thành công!")
        print(f"   - playlist_clean.csv")
        print(f"   - track_clean.csv")
        print(f"   - track_frequency.csv")
        print(f"   - artist_frequency.csv")
        print(f"   - pair_cooccurrence.csv")
        print(f"   - artist_cooccurrence.csv")
        return self
    
    def prepare_transactions_for_fpgrowth(self, level='track'):
        """
        Chuẩn bị transactions cho FP-Growth
        
        Parameters:
        -----------
        level : str
            'track' để tạo transactions ở cấp độ bài hát
            'artist' để tạo transactions ở cấp độ nghệ sĩ
            'both' để tạo cả hai loại transactions
        
        Returns:
        --------
        dict hoặc list tùy theo level
        """
        if level == 'track':
            print("\n Chuẩn bị transactions cấp độ TRACK cho FP-Growth...")
            transactions = self.df_track.groupby('pid')['track_uri'].apply(list).tolist()
            
            print(f" Đã tạo {len(transactions)} transactions (track level)")
            print(f"   Độ dài trung bình: {np.mean([len(t) for t in transactions]):.2f} items")
            print(f"   Độ dài min/max: {min([len(t) for t in transactions])}/{max([len(t) for t in transactions])} items")
            
            return transactions
        
        elif level == 'artist':
            print("\n Chuẩn bị transactions cấp độ ARTIST cho FP-Growth...")
            
            # Lấy danh sách artist duy nhất trong mỗi playlist
            transactions = self.df_track.groupby('pid')['artist_uri'].apply(lambda x: list(set(x))).tolist()
            
            print(f" Đã tạo {len(transactions)} transactions (artist level)")
            print(f"   Độ dài trung bình: {np.mean([len(t) for t in transactions]):.2f} items")
            print(f"   Độ dài min/max: {min([len(t) for t in transactions])}/{max([len(t) for t in transactions])} items")
            
            return transactions
        
        elif level == 'both':
            print("\n Chuẩn bị transactions cho cả hai cấp độ...")
            
            # Transactions cấp độ track
            track_transactions = self.df_track.groupby('pid')['track_uri'].apply(list).tolist()
            
            # Transactions cấp độ artist (loại bỏ trùng lặp trong mỗi playlist)
            artist_transactions = self.df_track.groupby('pid')['artist_uri'].apply(lambda x: list(set(x))).tolist()
            
            print(f" Đã tạo {len(track_transactions)} transactions (track level)")
            print(f" Đã tạo {len(artist_transactions)} transactions (artist level)")
            
            return {
                'track_transactions': track_transactions,
                'artist_transactions': artist_transactions,
                'track_info': self.df_track[['track_uri', 'track_name', 'artist_name']].drop_duplicates().set_index('track_uri').to_dict('index'),
                'artist_info': self.df_track[['artist_uri', 'artist_name']].drop_duplicates().set_index('artist_uri').to_dict('index')
            }
        
        else:
            raise ValueError("Level phải là 'track', 'artist' hoặc 'both'")


if __name__ == "__main__":
    # Khởi tạo và xử lý dữ liệu
    preprocessor = SpotifyDataPreprocessing('../data/raw/challenge_set.json')
    
    preprocessor.load_json() \
                .split_tables() \
                .clean_and_filter(min_tracks=3) \
                .analyze_data_richness(top_n=20, min_cooccurrence=5) \
                .save_cleaned_data()
    
    print("\n" + "="*60)
    print(" THỐNG KÊ TỔNG QUAN")
    print("="*60)
    stats = preprocessor.get_summary_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Chuẩn bị transactions cho cả hai cấp độ
    print("\n" + "="*60)
    print(" CHUẨN BỊ TRANSACTIONS CHO FP-GROWTH")
    print("="*60)
    
    # Lấy cả hai loại transactions
    transactions_data = preprocessor.prepare_transactions_for_fpgrowth(level='both')
    
    # Phân tích sâu hơn
    track_transactions = transactions_data['track_transactions']
    artist_transactions = transactions_data['artist_transactions']
    
    print("\n PHÂN TÍCH SÂU TRANSACTIONS:")
    print(f"\n 1. Cấp độ TRACK:")
    print(f"    - Số transactions: {len(track_transactions)}")
    print(f"    - Tổng số items: {sum([len(t) for t in track_transactions])}")
    print(f"    - Items duy nhất: {len(set([item for t in track_transactions for item in t]))}")
    
    print(f"\n 2. Cấp độ ARTIST:")
    print(f"    - Số transactions: {len(artist_transactions)}")
    print(f"    - Tổng số items: {sum([len(t) for t in artist_transactions])}")
    print(f"    - Items duy nhất: {len(set([item for t in artist_transactions for item in t]))}")
    
    print("\n Tiền xử lý hoàn tất! Dữ liệu sẵn sàng cho FP-Growth.")
    print("\n Bước tiếp theo cho luật kết hợp 2 levels:")
    print("   1. Chạy FP-Growth với track_transactions để được luật {track_A} → {track_B}")
    print("   2. Chạy FP-Growth với artist_transactions để được luật {artist_X} → {artist_Y}")
    print("   3. Kết hợp cả hai loại luật cho hệ thống gợi ý đa cấp độ")