from typing import TypedDict, Optional, List, Dict


class CollectionState(TypedDict):
    title: str
    authors: str
    tombo: str

    # Saídas do Pesquisador

    searched_synopsis: Optional[str]
    search_source: Optional[str]

    # Saídas do Classificador

    final_synopsis: Optional[str]
    final_tags: Optional[List[str]]
    color_suggestion: Optional[str]
    justification: Optional[str]
    top_3_probabilities: Optional[List[Dict[str, float]]]

    # Controle

    retry_count: int
    save_status: Optional[str]
    processed_at: Optional[str]
