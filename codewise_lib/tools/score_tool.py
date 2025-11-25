from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type

class ScoreToolInput(BaseModel):
    score: int = Field(..., description="A nota numérica atribuída ao usuário (0-10).")
    justification: str = Field(..., description="A justificativa resumida baseada na análise anterior.")
    author_name: str = Field(..., description="Nome do desenvolvedor avaliado.")

class ScoreFormalizerTool(BaseTool):
    name: str = "Registrar nota de performance"
    description: str = (
        "Registra formalmente a nota de performance de um desenvolvedor. "
        "VOCÊ DEVE USAR ESTA FERRAMENTA para registrar a avaliação final. "
        "Parâmetros obrigatórios: "
        "- score (int 0-10): nota numérica baseada na qualidade do código "
        "- justification (str): justificativa resumida da nota "
        "- author_name (str): nome completo do desenvolvedor avaliado"
    )
    args_schema: Type[BaseModel] = ScoreToolInput

    def _run(self, score: int, justification: str, author_name: str) -> str:
        try:
            if score < 0 or score > 10:
                return f"Erro: A nota {score} é inválida. Deve ser entre 0 e 10."

            return (
                f"AVALIAÇÃO REGISTRADA COM SUCESSO\n"
                f"Desenvolvedor: {author_name}\n"
                f"Nota Final: {score}/10\n"
                f"Motivo: {justification}\n"
            )

        except Exception as e:
            return f"Erro ao registrar nota: {e}"