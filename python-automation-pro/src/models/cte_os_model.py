"""
Modelo de dados para CT-e OS (Conhecimento de Transporte Eletrônico para
Outros Serviços) - Modelo 67, DACTE OS - documento fiscal DISTINTO tanto da
NFS-e ABRASF (`Nfse`, serviço/ISS, municipal) quanto da NF-e de produto
(`NfeProduto`, Modelo 55/ICMS de mercadoria, estadual): tributado por ICMS
como a NF-e de produto (documento fiscal estadual), mas sem tabela de
itens/NCM/CFOP por mercadoria - o que se transporta aqui é um SERVIÇO
(transporte de pessoas/cargas para outros fins que não mercadoria), com sua
própria grade de ICMS (base de cálculo/alíquota/percentual de redução de
base) e um bloco "modal rodoviário" (placa/RENAVAM/UF de licenciamento) que
não existe em nenhum dos outros dois modelos. Usar as tags de NF-e (mod=55,
`infNFe`) para representar um CT-e (mod=67, `infCte`) seria uma inverdade
estrutural equivalente a fabricar dado fiscal - por isso um modelo e um
transformer dedicados (ver `CteTransformer`), em vez de reaproveitar
`NfeProduto`/`NfeProdutoTransformer`. Ver LAYOUT_DACTE_OS no extrator.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .nfse_models import Endereco


class EntidadeCte(BaseModel):
    cnpj_cpf: str
    inscricao_estadual: Optional[str] = None
    razao_social: str
    endereco: Endereco
    telefone: Optional[str] = None
    email: Optional[str] = None


class ModalRodoviario(BaseModel):
    """Bloco "INFORMAÇÕES ESPECÍFICAS DO MODAL RODOVIÁRIO" - só existe em
    CT-e/CT-e OS, nunca numa NF-e de produto nem numa NFS-e."""
    registro_estadual: Optional[str] = None
    placa_veiculo: Optional[str] = None
    renavam: Optional[str] = None
    uf_licenciamento: Optional[str] = None
    cnpj_cpf_responsavel: Optional[str] = None


class ImpostoCte(BaseModel):
    """Grade "INFORMAÇÕES RELATIVAS AO IMPOSTO". Os 5 campos federais
    (PIS/COFINS/IR/INSS/CSLL) são retenções sobre o pagamento do serviço,
    não parte do ICMS propriamente - impressos na mesma grade pelo gerador
    do documento ("Master CT-e"), mantidos aqui como campos próprios em vez
    de forçados dentro do bloco de ICMS."""
    base_calculo_icms: float = 0.0
    aliquota_icms: float = 0.0
    valor_icms: float = 0.0
    percentual_reducao_bc: float = 0.0
    valor_icms_st: float = 0.0
    valor_pis: float = 0.0
    valor_cofins: float = 0.0
    valor_ir: float = 0.0
    valor_inss: float = 0.0
    valor_csll: float = 0.0


class CteOS(BaseModel):
    chave_acesso: str
    numero: str
    serie: str = "1"
    modelo: str = "67"
    tipo_cte: str = "Normal"
    tipo_servico: str  # ex.: "Transporte de Pessoas"
    cfop: str
    natureza_operacao: str
    data_emissao: datetime
    protocolo_autorizacao: Optional[str] = None
    protocolo_data_hora: Optional[datetime] = None
    municipio_inicio_prestacao: Optional[str] = None
    codigo_municipio_inicio: Optional[str] = None
    municipio_fim_prestacao: Optional[str] = None
    codigo_municipio_fim: Optional[str] = None
    emitente: EntidadeCte
    tomador: EntidadeCte
    quantidade_servico: float = 0.0
    descricao_servico: str
    valor_total_prestacao: float = 0.0
    valor_a_receber: float = 0.0
    imposto: ImpostoCte
    modal_rodoviario: Optional[ModalRodoviario] = None
    observacoes: Optional[str] = None
    numero_pedido: Optional[str] = None
    pagina_origem: Optional[int] = None
    avisos: List[str] = Field(default_factory=list)
