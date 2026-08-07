from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class Endereco(BaseModel):
    logradouro: str
    numero: str
    complemento: Optional[str] = None
    bairro: str
    codigo_municipio: str
    municipio: Optional[str] = None
    uf: str
    cep: str

class Entidade(BaseModel):
    cnpj_cpf: str
    inscricao_municipal: Optional[str] = None
    razao_social: str
    endereco: Endereco
    email: Optional[str] = None
    telefone: Optional[str] = None

class Valores(BaseModel):
    valor_servicos: float
    valor_deducoes: float = 0.0
    valor_pis: float = 0.0
    valor_cofins: float = 0.0
    valor_inss: float = 0.0
    valor_ir: float = 0.0
    valor_csll: float = 0.0
    iss_retido: bool = False
    valor_iss: float = 0.0
    valor_iss_retido: float = 0.0
    outras_retencoes: float = 0.0
    base_calculo: float
    aliquota: float  # Ex: 0.05 para 5%
    valor_liquido_nfse: float
    desconto_incondicionado: float = 0.0
    desconto_condicionado: float = 0.0

class Nfse(BaseModel):
    numero: str
    codigo_verificacao: str
    data_emissao: datetime
    competencia: datetime
    prestador: Entidade
    tomador: Entidade
    intermediario: Optional[Entidade] = None
    discriminacao: str
    servico_codigo: str  # Ex: 03115
    valores: Valores
    optante_simples_nacional: bool = False
    regime_especial_tributacao: Optional[str] = None
    incentivador_cultural: bool = False
    status: str = "Normal"
    pagina_origem: Optional[int] = None
    avisos: List[str] = Field(default_factory=list)
    # Sobrepõe o município padrão de incidência do ISSQN (município do
    # prestador) quando a própria nota indica que o serviço foi tributado
    # em OUTRO município (ex.: construção civil executada fora da sede do
    # prestador, LC 116/2003 art. 3º III). None em todos os layouts que não
    # setam isso explicitamente.
    municipio_incidencia_override: Optional[str] = None
