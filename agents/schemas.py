from pydantic import BaseModel, Field
from typing import List


class ColorProbability(BaseModel):
    """
    Sub-molde para estruturar as probabilidades individuais.
    """

    color: str = Field(
        description="O nome da categoria da cor (ex: Azul, Amarelo, Vermelho, Ouro, Prata)."
    )
    score: float = Field(
        description="O nível de confiança do modelo nesta cor, variando de 0.0 a 1.0."
    )


class ClassificationOutput(BaseModel):
    """
    O state que o LLM deve preencher ao classificar um livro. Traz rigor a saída do modelo.
    """

    color_suggestion: str = Field(
        description="A cor vencedora sugerida para o livro, baseada nas regras da biblioteca."
    )

    justification: str = Field(
        description="A justificativa detalhada explicando o raciocínio que levou à escolha desta cor."
    )

    top_3_probabilities: List[ColorProbability] = Field(
        description="Uma lista contendo as 3 cores mais prováveis. A soma dos scores não deve ultrapassar 1.0."
    )

    final_synopsis: str = Field(
        description="A sinopse revisada e limpa do livro, pronta para o banco de dados."
    )
    final_tags: List[str] = Field(
        description="Uma lista contendo no máximo 4 palavras-chave ou gêneros literários principais."
    )
