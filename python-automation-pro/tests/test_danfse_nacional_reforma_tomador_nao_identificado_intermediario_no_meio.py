# -*- coding: utf-8 -*-
r"""DANFSe Nacional v2.0 (pós-reforma), nota nº 59 (Campo Grande/MS, Marcos
Antonio da Silva Borges -> tomador não identificado, intermediário ELOS
ESTUDIO E SERVICOS LTDA). Reportada pelo usuário em duas rodadas:

Rodada 1 ("tomador do serviço extraído incorreto"): duas causas-raiz, as
DUAS ligadas à ordem de leitura desta nota específica (PRESTADOR ->
INTERMEDIÁRIO -> TOMADOR, diferente da ordem usual assumida em
`_extrair_entidade_nacional_reforma`, PRESTADOR -> TOMADOR ->
INTERMEDIÁRIO):

1. **Endereço do tomador saía "Não informado"** apesar de estar impresso
   ("ANTONIO CARLOS MAGALHAES, 2671, SALA 1202 EDIF BAHIA CENTER, BROTAS").
   O cabeçalho "TOMADOR / ADQUIRENTE" desta nota é seguido, na mesma
   respiração, por "DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\nDESTINATÁRIO DA
   OPERAÇÃO NÃO IDENTIFICADO NA NFS-e" — e o marcador de fim de bloco
   resiliente "IDENTIFICADO NA NFS" (usado para notas com OCR degradado)
   casava DENTRO dessa MESMA frase do próprio cabeçalho, cortando o bloco do
   tomador a quase nada e perdendo o Endereço real, impresso logo abaixo.
2. **Código de Município/CEP do tomador saía com o dado do INTERMEDIÁRIO**
   (contagem ordinal de ocorrência contaminada pela 3ª entidade no meio).

Rodada 2 (pedido explícito do usuário, mesma nota: "quando [o layout
nacional] não tiver o trecho tomador de serviço preenchido, porém, tiver o
trecho intermediário do serviço preenchido, utilizar como o tomador de
serviço"): regra de negócio já existente para `LAYOUT_NACIONAL` (v1.0,
decisão do usuário 2026-08-04, ver `test_danfse_intermediario_vira_tomador.py`)
estendida para `LAYOUT_NACIONAL_REFORMA` (v2.0). Quando o tomador vem
"NÃO IDENTIFICADO" (CNPJ sentinela ou a própria tarja na razão social) e há
um intermediário IDENTIFICADO, o intermediário é promovido a tomador e o
`<Intermediario>` é esvaziado (a mesma entidade não fica nos dois papéis).
Isso SUPERSEDE o fix nº 1 desta nota específica (o Endereço próprio do
tomador, uma vez recuperado, é descartado mesmo assim porque a Entidade
inteira é substituída pela do intermediário) — por isso este arquivo cobre
os dois cenários separadamente: COM intermediário (promoção) e SEM
intermediário (o fix nº 1 sozinho, tomador continua "Não Identificado" mas
com o endereço próprio recuperado).

Texto REAL extraído via pdfminer (PDF digital, nunca escaneado), direto do
PDF original - nunca digitado à mão (a variante "sem intermediário" é o
mesmo texto com só a seção do intermediário removida)."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor

MOCK_TEXT_COM_INTERMEDIARIO = """DANFSe v2.0
Documento Auxiliar da NFS-e

Município: Campo Grande - MS
Ambiente Gerador: 2
Tipo de Ambiente: 1

CHAVE DE ACESSO DA NFS-e
50027042222267787000195000000000005926088195572837

NÚMERO DA NFS-e
59

NÚMERO DA DPS
11

EMITENTE DA NFS-e
Prestador

PRESTADOR / FORNECEDOR

COMPETÊNCIA DA NFS-e
08/08/2026

SÉRIE DA DPS
70000

SITUAÇÃO DA NFS-e
NFS-e MEI

CNPJ / CPF / NIF
22.267.787/0001-95

Nome / Nome Empresarial
MARCOS ANTONIO DA SILVA BORGES 01178289125

Endereço
RUA PARAGUACU, 135, JARDIM TIJUCA

Simples Nacional na Data de Competência
Optante - Microempreendedor Individua...

Regime de Apuração Tributária pelo SN
-

DATA E HORA DA EMISSÃO DA NFS-e
08/08/2026 18:01:50

DATA E HORA DA EMISSÃO DA DPS
08/08/2026 18:01:49

FINALIDADE
-

Indicador Municipal (Inscrição)
-

Município / Sigla UF
Campo Grande / MS

E-mail
marcosunders@gmail.com

A autenticidade desta NFS-e pode ser verificada
pela leitura deste código QR ou pela consulta da
chave de acesso no portal nacional da NFS-e

Telefone
(67) 98119-8424

Código IBGE / CEP
50.02704 / 79.092-360

INTERMEDIÁRIO DA OPERAÇÃO

CNPJ / CPF / NIF
04.386.913/0001-49

Indicador Municipal (Inscrição)
-

Telefone
-

Nome / Nome Empresarial
ELOS ESTUDIO E SERVICOS LTDA

Município / Sigla UF
Salvador / BA

Código IBGE / CEP
29.27408 / 40.280-900

TOMADOR/ADQUIRENTE DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e
DESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e

Endereço
ANTONIO CARLOS MAGALHAES, 2671, SALA 1202 EDIF BAHIA CENTER, BROTAS

E-mail
-

SERVIÇO PRESTADO

Código de Tributação Nacional/Municipal
13.02.01 / -

Código da NBS
1.2501.11.00

Local da Prestação / Sigla UF / País
Campo Grande / MS / -

Fonografia ou gravação de sons, inclusive trucagem, dublagem, mixagem e congêneres.

Descrição do Serviço
Referente à gravação dos jingles de Otaviano Pivetta JOB 5828, Desperta São Paulo JOB 5748 e Daniel Vilella JOB 5749.
Dados para pagamento: SANTANDER Banco: 033 AG 3465 C/C 01008912-3
Marcos Antonio da Silva Borges CPF: 011.782.891-25 (CPF PIX)

TRIBUTAÇÃO MUNICIPAL (ISSQN)

Tipo de Tributação do ISSQN
Operação Tributável

Município / Sigla UF / País de Incidência do ISSQN
Campo Grande / MS / -

BC ISSQN
-

TRIBUTAÇÃO FEDERAL (EXCETO CBS)

PIS - Débito Apuração Própria
-

TRIBUTAÇÃO IBS/CBS

Alíquota Aplicada
-

IRRF
-

COFINS - Débito Apuração Própria
-

CST / cClassTrib
- / -

Retenção do ISSQN
Não Retido

Contribuição Previdenciária - Retida
-

Descrição Contrib. Sociais - Retidas
-

ISSQN Apurado
-

Contribuições Sociais - Retidas
-

Indicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF
- / - / - / -

Exclusões e Reduções da Base de Cálculo
R$ 0,00

Base de Cálculo Após Exclusões e Reduções
-

Red. Alíquota IBS / Red. Alíquota CBS
- / - / -

Alíq. Efetiva Municipal - IBS
-

Valor Total Apurado - IBS
-

VALOR TOTAL DA NFS-e

Valor Apurado Municipal - IBS
-

Alíquota - CBS
-

VALOR DA OPERAÇÃO / SERVIÇO
R$ 1.200,00

Total das Retenções (ISSQN / Federais)
-

VALOR LÍQUIDO DA NFS-e
R$ 1.200,00

INFORMAÇÕES COMPLEMENTARES

Alíq. Efetiva Estadual - IBS
-

Alíquota Efetiva - CBS
-

Desconto Incondicionado
-

Total do IBS/CBS
R$ 0,00

Alíquota - IBS UF / IBS Mun
- / -

Valor Apurado Estadual - IBS
-

Valor Total Apurado - CBS
-

Desconto Condicionado
-

VALOR LÍQUIDO DA NFS-e + IBS/CBS
R$ 0,00

Totais aproximados dos Tributos cfe. Lei n° 12.741/2012: Federais: -; Estaduais: -; Municipais: -;

DATA CIENTIFICAÇÃO:

IDENTIFICAÇÃO E ASSINATURA

N° NFS-e / CHAVE NFS-e
59 / 50027042222267787000195000000000005926088195572837
"""

# Mesmo texto, mas sem a seção "INTERMEDIÁRIO DA OPERAÇÃO" - prova que o fix
# de recuperação do Endereço do tomador (rodada 1) continua valendo por si
# só, quando não há intermediário nenhum para promover.
MOCK_TEXT_SEM_INTERMEDIARIO = MOCK_TEXT_COM_INTERMEDIARIO.replace(
    """INTERMEDIÁRIO DA OPERAÇÃO

CNPJ / CPF / NIF
04.386.913/0001-49

Indicador Municipal (Inscrição)
-

Telefone
-

Nome / Nome Empresarial
ELOS ESTUDIO E SERVICOS LTDA

Município / Sigla UF
Salvador / BA

Código IBGE / CEP
29.27408 / 40.280-900

TOMADOR/ADQUIRENTE""",
    "TOMADOR/ADQUIRENTE",
)
assert "INTERMEDIÁRIO" not in MOCK_TEXT_SEM_INTERMEDIARIO


def _run(monkeypatch, texto):
    dummy_path = "tests/dummy_marcos_borges.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        return nfse_list
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_intermediario_e_promovido_a_tomador_quando_tomador_nao_identificado(monkeypatch):
    """Pedido explícito do usuário: tomador não identificado + intermediário
    identificado -> o intermediário assume o papel de tomador, e
    <Intermediario> fica vazio (a mesma entidade não fica nos dois papéis)."""
    nfse_list = _run(monkeypatch, MOCK_TEXT_COM_INTERMEDIARIO)
    assert len(nfse_list) == 1
    nfse = nfse_list[0]

    t = nfse.tomador
    assert t.cnpj_cpf == "04386913000149"
    assert t.razao_social == "ELOS ESTUDIO E SERVICOS LTDA"
    # Município/UF/CEP do intermediário (ele tem "Município/Sigla UF" e
    # "Código IBGE/CEP" próprios, sem "Endereço" - esta seção do layout
    # nunca imprime logradouro para o intermediário).
    assert t.endereco.municipio == "Salvador"
    assert t.endereco.uf == "BA"
    assert t.endereco.codigo_municipio == "2927408"
    assert t.endereco.cep == "40280900"
    assert t.endereco.logradouro == "Não informado"

    assert nfse.intermediario is None
    assert "Dados do tomador não identificados" not in nfse.avisos

    # Colateral: prestador não é afetado pela promoção.
    p = nfse.prestador
    assert p.cnpj_cpf == "22267787000195"
    assert p.endereco.municipio == "Campo Grande"
    assert p.endereco.uf == "MS"
    assert p.endereco.codigo_municipio == "5002704"


def test_tomador_nao_identificado_sem_intermediario_recupera_proprio_endereco(monkeypatch):
    """Sem intermediário nenhum para promover, a regra de negócio não
    dispara - mas o fix da rodada 1 (recuperar o Endereço real do PRÓPRIO
    tomador, mesmo não identificado) continua valendo: antes dele o bloco do
    tomador saía quase vazio (' DA OPERAÇÃO NÃO ') porque o marcador de fim
    resiliente 'IDENTIFICADO NA NFS' casava dentro do próprio preâmbulo do
    cabeçalho, perdendo o Endereço impresso logo abaixo."""
    nfse_list = _run(monkeypatch, MOCK_TEXT_SEM_INTERMEDIARIO)
    nfse = nfse_list[0]

    t = nfse.tomador
    assert t.cnpj_cpf == "00000000000000"
    assert t.razao_social == "Tomador Não Identificado"
    assert t.endereco.logradouro == "ANTONIO CARLOS MAGALHAES"
    assert t.endereco.numero == "2671"
    assert t.endereco.complemento == "SALA 1202 EDIF BAHIA CENTER"
    assert t.endereco.bairro == "BROTAS"
    # Sem intermediário no texto, não há nada pra contaminar o
    # Município/CEP - a nota genuinamente não imprime esses campos para um
    # tomador não identificado.
    assert t.endereco.municipio == "Não informado"
    assert t.endereco.uf == ""
    assert t.endereco.codigo_municipio == ""
    assert t.endereco.cep == "00000000"

    assert nfse.intermediario is None
    assert "Dados do tomador não identificados" in nfse.avisos
