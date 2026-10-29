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
    CT-e/CT-e OS, nunca numa NF-e de produto nem numa NFS-e. No XML vira
    `infCTeNorm/infModal/rodoOS` (leiaute oficial `cteModalRodoviarioOS_v4.00`):
    `TAF` (12 dígitos) OU `NroRegEstadual` (25 dígitos), e `veic` (placa,
    RENAVAM, UF) quando a placa é impressa. `cnpj_cpf_responsavel` é só
    informativo (o grupo oficial `veic/prop` exige também nome e tipo do
    proprietário, que o DACTE OS não imprime - não é emitido)."""
    termo_autorizacao_fretamento: Optional[str] = None
    registro_estadual: Optional[str] = None
    placa_veiculo: Optional[str] = None
    renavam: Optional[str] = None
    uf_licenciamento: Optional[str] = None
    cnpj_cpf_responsavel: Optional[str] = None


class ImpostoCte(BaseModel):
    """Grade "INFORMAÇÕES RELATIVAS AO IMPOSTO". Os 5 campos federais
    (PIS/COFINS/IR/INSS/CSLL) são retenções sobre o pagamento do serviço,
    não parte do ICMS propriamente - impressos na mesma grade pelo gerador
    do documento ("Master CT-e"/"CT-e Prático"), mantidos aqui como campos
    próprios em vez de forçados dentro do bloco de ICMS - no XML oficial 4.00
    vão para `imp/infTribFed` (vPIS/vCOFINS/vIR/vINSS/vCSLL)."""
    # CST impresso em "CLASSIFICAÇÃO TRIBUTÁRIA DO SERVIÇO" (ex. "40" de
    # "40 - ICMS ISENÇÃO") ou derivado pelo extrator (com aviso) quando o
    # gerador não o imprime - define o grupo oficial `imp/ICMS/ICMSxx`.
    cst_icms: Optional[str] = None
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

    def cst_derivado(self) -> str:
        """CST usado quando o DACTE OS NÃO imprime a "CLASSIFICAÇÃO
        TRIBUTÁRIA DO SERVIÇO" (achado real, gerador Master CT-e, nota 564
        CIATRANS: a caixa sai em branco). Derivado SÓ dos valores impressos
        na mesma grade, nunca de tabela externa: % de redução de BC > 0 ->
        "20" (tributação com redução de BC); ICMS > 0 sem redução -> "00";
        nada disso -> "90" (Outros), o único grupo que comporta valores
        zerados sem afirmar isenção/não incidência. O extrator registra aviso
        sempre que este caminho é usado."""
        if self.percentual_reducao_bc > 0:
            return "20"
        if self.valor_icms > 0:
            return "00"
        return "90"


class CteOS(BaseModel):
    chave_acesso: str
    numero: str
    serie: str = "1"
    modelo: str = "67"
    tipo_cte: str = "Normal"
    tipo_servico: str  # ex.: "Transporte de Pessoas"
    # `ide/tpServ` do leiaute 4.00 (6 = pessoas, 7 = valores, 8 = excesso de
    # bagagem) - derivado de `tipo_servico` pelo extrator.
    tipo_servico_codigo: Optional[str] = None
    # `ide/modal` (01 rodoviário, 02 aéreo, 03 aquaviário, 04 ferroviário) -
    # lido do cabeçalho "MODAL <nome>" impresso.
    modal: Optional[str] = None
    cfop: str
    natureza_operacao: str
    data_emissao: datetime
    protocolo_autorizacao: Optional[str] = None
    protocolo_data_hora: Optional[datetime] = None
    municipio_inicio_prestacao: Optional[str] = None
    codigo_municipio_inicio: Optional[str] = None
    uf_inicio_prestacao: Optional[str] = None
    municipio_fim_prestacao: Optional[str] = None
    codigo_municipio_fim: Optional[str] = None
    uf_fim_prestacao: Optional[str] = None
    # `emit/CRT` - o DACTE OS não imprime o regime tributário; o extrator
    # preenche com aviso (ver `_parse_dacte_os`).
    crt: Optional[str] = None
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
