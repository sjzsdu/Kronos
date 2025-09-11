# Bridge to root-level model package if available
try:
    from model.kronos import Kronos, KronosTokenizer, KronosPredictor  # type: ignore
except Exception as e:  # fallback if root model not accessible
    raise
