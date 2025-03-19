import unicodedata


def normalize_str(s):
    """
    Normalise une chaîne en supprimant les accents pour le tri

    Args:
        s: Chaîne à normaliser

    Returns:
        str: Chaîne normalisée
    """
    if not s:
        return ""
    return (
        unicodedata.normalize("NFKD", s)
        .encode("ASCII", "ignore")
        .decode("ASCII")
        .lower()
    )
