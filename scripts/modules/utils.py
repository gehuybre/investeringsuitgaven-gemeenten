"""
Utility functies die gedeeld worden over meerdere scripts.
"""


def normalize_municipality_name(name: str) -> str:
    """
    Normaliseer gemeentenaam voor matching.
    
    Verwijdert 'Gemeente en OCMW' prefix en maakt lowercase.
    
    Args:
        name: De originele gemeentenaam
        
    Returns:
        Genormaliseerde gemeentenaam (lowercase, zonder prefix)
    """
    name = str(name).strip()
    if name.startswith("Gemeente en OCMW "):
        name = name.replace("Gemeente en OCMW ", "")
    return name.lower()


def parse_value(value: str) -> float | None:
    """
    Converteer CSV waarde naar float.
    
    Handelt komma als decimaal scheidingsteken, lege waarden en errors af.
    
    Args:
        value: String waarde uit CSV
        
    Returns:
        Float waarde of None als parsing faalt
    """
    if not value or not str(value).strip():
        return None
    try:
        return float(str(value).strip().replace(',', '.'))
    except (ValueError, TypeError):
        return None
