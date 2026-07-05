#!/usr/bin/env python3
"""
fpgrowth_recommender.py

FP-Growth pipeline for track-level playlists using mlxtend with safety filters.

This script mirrors the artist-version and adds these controls:
- --max-itemset-len: limit size of frequent itemsets (passed to mlxtend.fpgrowth)
- --max-antecedent-len: drop rules with antecedent length > N
- --min-lift: drop rules with lift < value
- --only-consequent-len: keep rules whose consequent length == N

Output CSV columns:
antecedents,consequents,antecedent_names,consequent_names,support,confidence,lift,conviction,antecedent_len,consequent_len

Usage example:
  python fpgrowth_recommender.py \
    --input Playlist_track.csv \
    --output rules_track.csv \
    --min-support 0.0025 --min-confidence 0.4 \
    --max-itemset-len 3 --max-antecedent-len 2 --min-lift 1.2 \
    --only-consequent-len 1 --map track_uri_map.csv

python fpgrowth_recommender.py -i Playlist_track.csv -o rules_track.csv -m track_uri_map.csv -s 0.0025 -c 0.4 --max-itemset-len 3 --max-antecedent-len 2

Requirements:
  pip install pandas mlxtend numpy
"""

import argparse
import pandas as pd
import numpy as np
import math
import json
import sys
import csv
import re
from collections import Counter
from typing import List, Dict
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules


def parse_list_field(s: str, item_kind: str = "track") -> List[str]:
    """
    Parse a CSV cell containing comma-separated track URIs (possibly quoted).
    Returns deduplicated list preserving first-seen order.
    """
    if pd.isna(s):
        return []
    s = str(s).strip()
    # strip outer quotes
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        s = s[1:-1]
    parts = [p.strip() for p in s.split(',')]
    parts = [p for p in parts if p != '']
    # fallback regex to find spotify:track:... or spotify:artist:...
    if not parts or any(',' in p for p in parts):
        if item_kind == 'track':
            found = re.findall(r"(spotify:track:[A-Za-z0-9]+)", s)
        else:
            found = re.findall(r"(spotify:artist:[A-Za-z0-9]+)", s)
        if found:
            parts = found
    # deduplicate preserving order
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def load_uri_name_map(map_path: str) -> Dict[str, str]:
    """
    Load a mapping CSV (uri,name) and return dict {uri: name}.
    Accepts headers 'uri','name' or falls back to first two columns.
    """
    try:
        mdf = pd.read_csv(map_path, dtype=str)
    except Exception as e:
        raise RuntimeError(f"Could not read mapping file '{map_path}': {e}")
    cols = [c.lower() for c in mdf.columns]
    if 'uri' in cols and 'name' in cols:
        uri_col = mdf.columns[cols.index('uri')]
        name_col = mdf.columns[cols.index('name')]
    elif 'track_uri' in cols and 'track_name' in cols:
        uri_col = mdf.columns[cols.index('track_uri')]
        name_col = mdf.columns[cols.index('track_name')]
    else:
        if mdf.shape[1] >= 2:
            uri_col = mdf.columns[0]
            name_col = mdf.columns[1]
        else:
            raise RuntimeError("Mapping CSV must have at least two columns: uri and name")
    mapping = {}
    for _, r in mdf.iterrows():
        uri = str(r[uri_col]).strip()
        name = str(r[name_col]).strip()
        if uri:
            mapping[uri] = name
    return mapping


def frozenset_to_pylist_str(fs) -> str:
    """Return Python-list style string for a set/iterable, deterministic ordering."""
    if isinstance(fs, (set, frozenset)):
        lst = sorted(list(fs))
    elif isinstance(fs, (list, tuple)):
        lst = list(fs)
    else:
        lst = [fs]
    return repr(lst)


def map_items_to_names(items, mapping: Dict[str, str]) -> str:
    if isinstance(items, (set, frozenset)):
        uris = sorted(list(items))
    elif isinstance(items, (list, tuple)):
        uris = list(items)
    else:
        uris = [items]
    names = [mapping.get(u, u) for u in uris]
    return repr(names)


def main(args):
    # Load input
    print("Loading input CSV:", args.input)
    try:
        df = pd.read_csv(args.input, dtype=str)
    except Exception as e:
        print(f"Error reading input CSV '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)

    # Detect list column
    cols_lower = {c.lower(): c for c in df.columns}
    if 'list_track_uri' in cols_lower:
        list_col = cols_lower['list_track_uri']; item_kind = 'track'
    elif 'list_track_uris' in cols_lower:
        list_col = cols_lower['list_track_uris']; item_kind = 'track'
    else:
        list_col = None; item_kind = 'track'
        for c in df.columns:
            lc = c.lower()
            if 'track' in lc and ('list' in lc or 'uri' in lc):
                list_col = c; item_kind = 'track'; break
        if list_col is None:
            for c in df.columns:
                lc = c.lower()
                if 'artist' in lc and ('list' in lc or 'uri' in lc):
                    list_col = c; item_kind = 'artist'; break
    if list_col is None:
        print("Could not find a 'list_track_uri' or similar column in input CSV.", file=sys.stderr)
        sys.exit(1)
    print(f"Using column '{list_col}' (interpreted as {item_kind})")

    # Parse transactions
    print("Parsing playlists into transactions...")
    transactions = []
    for _, cell in df[list_col].items():
        items = parse_list_field(cell, item_kind)
        if items:
            transactions.append(items)

    if not transactions:
        print("No transactions extracted from input. Exiting.", file=sys.stderr)
        sys.exit(1)

    n_trans = len(transactions)
    print(f"Number of transactions (playlists): {n_trans}")

    # compute integer min_count (ceil)
    min_support = float(args.min_support)
    min_count = math.ceil(min_support * n_trans)
    print(f"min_support (fraction): {min_support} => min_count (ceil): {min_count} playlists")

    # diagnostics: item frequency
    cnt = Counter()
    for t in transactions:
        for it in set(t):
            cnt[it] += 1
    distinct_items = len(cnt)
    popular_items = [item for item,c in cnt.items() if c >= min_count]
    print("Distinct items:", distinct_items)
    print("Items with count >= min_count:", len(popular_items))
    top = sorted(cnt.items(), key=lambda x: x[1], reverse=True)[:20]
    print("Top items (item, count):")
    for it,c in top:
        print(it, c)

    # optional mapping
    uri_name_map = {}
    if args.map:
        print("Loading URI->name mapping from:", args.map)
        try:
            uri_name_map = load_uri_name_map(args.map)
            print(f"Loaded {len(uri_name_map)} mappings.")
        except Exception as e:
            print("Failed to load mapping:", e, file=sys.stderr)
            sys.exit(1)

    # encode transactions
    print("Encoding transactions with TransactionEncoder...")
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions, sparse=False)
    trans_df = pd.DataFrame(te_ary, columns=te.columns_)
    print(f"Encoded matrix: {trans_df.shape[0]} rows x {trans_df.shape[1]} distinct items")

    # run fpgrowth with max_len param if provided
    print(f"Running fpgrowth (min_support={min_support}, max_len={args.max_itemset_len}) ...")
    freq_itemsets = fpgrowth(trans_df, min_support=min_support, use_colnames=True, max_len=args.max_itemset_len)
    if freq_itemsets.empty:
        print("No frequent itemsets found with the given min_support. Try lowering --min-support.", file=sys.stderr)
        sys.exit(1)
    print(f"Found {len(freq_itemsets)} frequent itemsets")

    # diagnostics: distribution by itemset size
    freq_itemsets['length'] = freq_itemsets['itemsets'].apply(lambda s: len(s))
    dist = freq_itemsets['length'].value_counts().sort_index()
    print("Frequent itemsets distribution by length:")
    for length, count in dist.items():
        print(f" length={length}: {count}")

    # generate association rules
    print(f"Generating association rules (min_confidence={args.min_confidence}) ...")
    rules = association_rules(freq_itemsets, metric="confidence", min_threshold=args.min_confidence)
    if rules.empty:
        print("No association rules found with the given thresholds. Try lowering min_support or min_confidence.", file=sys.stderr)
        sys.exit(1)
    print(f"Generated {len(rules)} raw rules")

    # compute antecedent_len and consequent_len columns
    rules['antecedent_len'] = rules['antecedents'].apply(lambda s: len(s))
    rules['consequent_len'] = rules['consequents'].apply(lambda s: len(s))

    # apply filters: only_consequent_len, max_antecedent_len, min_lift
    before = len(rules)
    if args.only_consequent_len is not None:
        rules = rules[rules['consequent_len'] == args.only_consequent_len]
    if args.max_antecedent_len is not None:
        rules = rules[rules['antecedent_len'] <= args.max_antecedent_len]
    if args.min_lift is not None:
        rules = rules[rules['lift'] >= args.min_lift]
    after = len(rules)
    print(f"Rules after filtering: {before} -> {after}")

    if rules.empty:
        print("No rules remain after filtering. Adjust filters.", file=sys.stderr)
        sys.exit(1)

    # prepare output rows
    out_rows = []
    for _, row in rules.iterrows():
        ants = row['antecedents']
        cons = row['consequents']
        support = float(row['support'])
        confidence = float(row['confidence'])
        lift = float(row['lift'])
        conviction = float(row['conviction']) if 'conviction' in row else np.nan

        antecedents_str = frozenset_to_pylist_str(ants)
        consequents_str = frozenset_to_pylist_str(cons)
        antecedent_names_str = map_items_to_names(ants, uri_name_map) if uri_name_map else antecedents_str
        consequent_names_str = map_items_to_names(cons, uri_name_map) if uri_name_map else consequents_str

        out_rows.append({
            'antecedents': antecedents_str,
            'consequents': consequents_str,
            'antecedent_names': antecedent_names_str,
            'consequent_names': consequent_names_str,
            'support': support,
            'confidence': confidence,
            'lift': lift,
            'conviction': conviction,
            'antecedent_len': int(len(ants)),
            'consequent_len': int(len(cons))
        })

    out_df = pd.DataFrame(out_rows)
    # sort for convenience
    out_df = out_df.sort_values(by=['support', 'confidence'], ascending=[False, False]).reset_index(drop=True)

    ordered_cols = ['antecedents','consequents','antecedent_names','consequent_names',
                    'support','confidence','lift','conviction','antecedent_len','consequent_len']
    out_df = out_df[ordered_cols]

    print("Writing output CSV to:", args.output)
    out_df.to_csv(args.output, index=False, quoting=csv.QUOTE_MINIMAL)
    print("Done. Output rows:", len(out_df))
    print(out_df.head(10).to_string(index=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="FP-Growth (mlxtend) for tracks with filters to limit explosion")
    parser.add_argument('--input', '-i', required=True, help="Input CSV path (must contain a column like 'list_track_uri')")
    parser.add_argument('--output', '-o', default='rules_track_output.csv', help="Output CSV path")
    parser.add_argument('--min-support', '-s', type=float, default=0.003, help="Minimum support (fraction). Default 0.01")
    parser.add_argument('--min-confidence', '-c', type=float, default=0.5, help="Minimum confidence for association rules. Default 0.5")
    parser.add_argument('--max-itemset-len', type=int, default=3, help="Max itemset length to find (passed to fpgrowth.max_len). Default 3")
    parser.add_argument('--max-antecedent-len', type=int, default=2, help="Drop rules whose antecedent length > N. Default 2")
    parser.add_argument('--min-lift', type=float, default=1.2, help="Drop rules whose lift < value. Default 1.2")
    parser.add_argument('--only-consequent-len', type=int, default=1, help="If set, only keep rules with consequent length == N. Default 1")
    parser.add_argument('--map', '-m', default=None, help="Optional CSV mapping file of uri -> name (columns: uri,name)")
    args = parser.parse_args()

    main(args)
