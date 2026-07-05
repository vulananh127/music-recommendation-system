def composite_score(confidence: float, lift: float, support: float = None) -> float:
    # Chủ đạo: confidence * lift (optionally cân nhắc support)
    return confidence * lift