"""
Default Regex patterns for Kindle clippings parsing.
Separated from logic to allow easier updates and multi-language extensions.
"""
import re

DEFAULT_PATTERNS = {
    # Variations of "Highlight"
    "highlight": re.compile(r'subrayado|Subrayado|Highlight|highlight', re.IGNORECASE),
    
    # Variations of "Note"
    "note": re.compile(r'nota|Nota|Note|note', re.IGNORECASE),
    
    # Variations of "Page"
    "page": re.compile(r'página|page|Page|pág\.', re.IGNORECASE),
    
    # Variations of "Added on"
    "added": re.compile(r'Añadid[oa] el|Added on|Agregado el', re.IGNORECASE),
    
    # Variations of "Location"
    "location": re.compile(r'posición|Pos\.|position|Position|location|Location|loc\.', re.IGNORECASE)
}
