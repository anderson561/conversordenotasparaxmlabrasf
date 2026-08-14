"""
Modelo de dados para NF-e de PRODUTO (Modelo 55 - DANFE Estadual), tributada
por ICMS/IPI - distinto do modelo `Nfse` (NFS-e de SERVIÇO, ABRASF/municipal,
tributada por ISS). Uma NF-e de produto tem uma tabela de N itens (NCM/CFOP),
grade de ICMS e um bloco de transportador/volumes que não existem em nenhuma
nota de serviço.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .nfse_models import Endereco


class EntidadeNfe(BaseModel):
    cnpj_cpf: str
    inscricao_estadual: Optional[str] = None
    razao_social: str
    endereco: Endereco
    telefone: Optional[str] = None
    email: Optional[str] = None


class ItemProduto(BaseModel):
    codigo: str
    descricao: str
    ncm: str
    cfop: str
    cst_icms: Optional[str] = None
    unidade: str
    quantidade: float
    valor_unitario: float
    valor_total: float
    base_calculo_icms: float = 0.0
    valor_icms: float = 0.0
    aliquota_icms: float = 0.0
    valor_ipi: float = 0.0
    aliquota_ipi: float = 0.0


class Transportador(BaseModel):
    razao_social: Optional[str] = None
    cnpj_cpf: Optional[str] = None
    inscricao_estadual: Optional[str] = None
    endereco: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    frete_por_conta: Optional[str] = None  # código CST do frete: "0"=emitente, "1"=destinatário etc.
    placa_veiculo: Optional[str] = None
    quantidade_volumes: Optional[float] = None
    especie: Optional[str] = None
    marca: Optional[str] = None
    peso_bruto: Optional[float] = None
    peso_liquido: Optional[float] = None


class ValoresNfe(BaseModel):
    base_calculo_icms: float = 0.0
    valor_icms: float = 0.0
    base_calculo_icms_st: float = 0.0
    valor_icms_st: float = 0.0
    valor_total_produtos: float = 0.0
    valor_frete: float = 0.0
    valor_seguro: float = 0.0
    desconto: float = 0.0
    outras_despesas: float = 0.0
    valor_ipi: float = 0.0
    valor_total_nota: float = 0.0


class NfeProduto(BaseModel):
    chave_acesso: str
    numero: str
    serie: str = "1"
    natureza_operacao: str
    tipo_operacao: str = "1"  # 0=entrada, 1=saída
    data_emissao: datetime
    data_saida_entrada: Optional[datetime] = None
    protocolo_autorizacao: Optional[str] = None
    protocolo_data_hora: Optional[datetime] = None
    emitente: EntidadeNfe
    destinatario: EntidadeNfe
    itens: List[ItemProduto] = Field(default_factory=list)
    transportador: Optional[Transportador] = None
    valores: ValoresNfe
    fatura_duplicata: Optional[str] = None
    informacoes_complementares: Optional[str] = None
    pagina_origem: Optional[int] = None
    avisos: List[str] = Field(default_factory=list)
