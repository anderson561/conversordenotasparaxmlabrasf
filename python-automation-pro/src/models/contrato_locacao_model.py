"""
Modelo de dados para Contratos de Locação.

Mapeamento ABRASF:
  Locador  (quem aluga o bem)  → Tomador  no XML
  Locatário (quem usa o bem)   → Prestador no XML
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EntidadeContrato(BaseModel):
    """Representa uma parte do contrato (Locador ou Locatário)."""
    cnpj_cpf: str
    razao_social: str
    inscricao_municipal: Optional[str] = None
    logradouro: str = "Não informado"
    numero: str = "S/N"
    bairro: str = "Não informado"
    codigo_municipio: str = "2927408"   # Default: Salvador-BA (2927408)
    municipio: str = "Salvador"
    uf: str = "BA"
    cep: str = "00000000"
    email: Optional[str] = None
    telefone: Optional[str] = None


class ContratoLocacao(BaseModel):
    """Dados de um Contrato de Locação para geração de XML ABRASF."""

    # Partes do contrato
    locador: EntidadeContrato    # → Tomador no XML
    locatario: EntidadeContrato  # → Prestador no XML

    # Dados financeiros
    valor_mensal: float          # Valor mensal do aluguel (R$)
    discriminacao: str           # Descrição do bem/serviço

    # Dados temporais (definidos pelo usuário na GUI)
    data_emissao: datetime = Field(default_factory=datetime.now)

    # Código de serviço LC 116/2003
    # 0601 = locação de bens móveis / 0701 = arrendamento, concessão
    servico_codigo: str = "0601"

    # Alíquota ISS (padrão 3% para locação de bens)
    aliquota_iss: float = 0.03

    # Opcionais tributários
    optante_simples_nacional: bool = False
    iss_retido: bool = False
