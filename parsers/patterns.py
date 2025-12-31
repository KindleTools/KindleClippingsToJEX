"""
Default Regex patterns for Kindle clippings parsing.
Separated from logic to allow easier updates and multi-language extensions.
"""

DEFAULT_PATTERNS = {
    # Variations of "Highlight"
    "highlight": r"subrayado|Subrayado|Highlight|highlight",
    # Variations of "Note"
    "note": r"nota|Nota|Note|note",
    # Variations of "Page"
    "page": r"página|page|Page|pág\.",
    # Variations of "Added on"
    "added": r"Añadid[oa\.] el|Added on|Agregado el",
    # Variations of "Location"
    "location": r"posición|Pos\.|position|Position|location|Location|loc\.",
}
