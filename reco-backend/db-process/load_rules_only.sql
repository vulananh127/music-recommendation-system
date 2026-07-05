-- Load ONLY rules from staging to main tables
-- Artist Rules
INSERT INTO fp_rules_artists (
    antecedents, consequents, antecedent_names, consequent_names,
    support, confidence, lift, conviction, antecedent_len, consequent_len
)
SELECT
    CASE WHEN antecedents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedents), ', ')
        ELSE string_to_array(TRIM(antecedents), ',')
    END AS antecedents,
    CASE WHEN consequents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequents), ', ')
        ELSE string_to_array(TRIM(consequents), ',')
    END AS consequents,
    CASE WHEN antecedent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedent_names), ', ')
        ELSE string_to_array(TRIM(antecedent_names), ',')
    END AS antecedent_names,
    CASE WHEN consequent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequent_names), ', ')
        ELSE string_to_array(TRIM(consequent_names), ',')
    END AS consequent_names,
    support, confidence, lift, conviction, antecedent_len, consequent_len
FROM staging_artist_rules
WHERE antecedents IS NOT NULL AND TRIM(antecedents) != '';

-- Track Rules
INSERT INTO fp_rules_tracks (
    antecedents, consequents, antecedent_names, consequent_names,
    support, confidence, lift, conviction, antecedent_len, consequent_len
)
SELECT
    CASE WHEN antecedents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedents), ', ')
        ELSE string_to_array(TRIM(antecedents), ',')
    END AS antecedents,
    CASE WHEN consequents LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequents), ', ')
        ELSE string_to_array(TRIM(consequents), ',')
    END AS consequents,
    CASE WHEN antecedent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM antecedent_names), ', ')
        ELSE string_to_array(TRIM(antecedent_names), ',')
    END AS antecedent_names,
    CASE WHEN consequent_names LIKE '[''%' THEN string_to_array(TRIM(BOTH '[]''' FROM consequent_names), ', ')
        ELSE string_to_array(TRIM(consequent_names), ',')
    END AS consequent_names,
    support, confidence, lift, conviction, antecedent_len, consequent_len
FROM staging_track_rules
WHERE antecedents IS NOT NULL AND TRIM(antecedents) != '';
