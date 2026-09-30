# -*- coding: utf-8 -*-
r"""Layout `danfse_nacional_reforma` (DANFSe v2.0) — variante "NFS-e MEI".

Achado real (2026-09-30): duas notas do MESMO prestador (PATRICIA ONORI
BORCHES SANCHEZ, Microempreendedor Individual, Santana de Parnaíba/SP) ->
NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA (São Paulo/SP), notas
nº 1 e nº 2, R$ 3.250,00 e R$ 6.500,00 de "Instrução, treinamento, orientação
pedagógica...". PDFs escaneados (via OCR), mesmo layout `LAYOUT_NACIONAL_
REFORMA` já suportado (nº 5/SBS, nº 11, nº 59/Campo Grande, nº 171-173/
Macedo) — mas com uma variação estrutural NOVA na coluna "Nome / Nome
Empresarial" que nenhuma das notas anteriores exibe.

Nas notas já suportadas, a 1ª linha não-vazia depois do rótulo "Nome / Nome
Empresarial" já é o nome (ou a coluna vem toda fundida numa linha só, outro
caminho já tratado). Nesta variante "NFS-e MEI" a coluna sai VAZIA logo
abaixo do próprio rótulo — o nome de verdade só aparece DEPOIS do bloco
"CNPJ/CPF / NIF" (rótulo + CNPJ formatado), numa linha que repete o CNPJ SEM
pontuação colado ao nome:

    Nome / Nome Empresarial

    CNPJ/CPF / NIF
    67.944.968/0001-47

    67.944.968 PATRICIA ONORI BORCHES SANCHEZ

Sem tratamento, a regex genérica aceitava cegamente a linha do rótulo "CNPJ/
CPF / NIF" (ou "CNPJ/CPF /NIF", grafia com 1 espaço a menos no bloco do
tomador desta mesma nota) como se fosse o nome — <RazaoSocial>CNPJ/CPF / NIF
</RazaoSocial> tanto no prestador quanto no tomador, apesar dos dois nomes
estarem perfeitamente legíveis 2 linhas abaixo.

Achados secundários cobertos aqui (mesma nota):
1. **CEP/Código IBGE do prestador**: a coluna "Código IBGE / CEP" perde o "0"
   inicial do CEP só nesta nota ("35.47304 / 6543001" - CEP real "06543-001",
   8 dígitos, sai com só 7). O parser rejeitava a linha INTEIRA (exigia
   8-12 caracteres no CEP), então nem o código IBGE - perfeitamente legível -
   era aproveitado: `CodigoMunicipio` caía no fallback por nome (que não
   conhece "Santana de Parnaíba" e devolvia a capital de SP, 3550308, por
   engano) e `Cep` saía "00000000" (sentinela).
2. **Indicador Municipal fantasma do prestador**: o campo vem legitimamente
   em branco ("- (11) 9462-0190", só o "-" marca a ausência, fundido com
   Telefone) - mas a busca genérica por "qualquer token puramente numérico"
   nas linhas seguintes do bloco encontrava, mais adiante, o CEP mal lido da
   própria linha "Código IBGE / CEP" e o aceitava como se fosse o Indicador
   Municipal do prestador (<InscricaoMunicipal>6543001</InscricaoMunicipal>).

Texto OCR REAL (Tesseract) das duas notas, preservado verbatim via repr()."""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA

MOCK_OCR_NOTA_1 = 'N FSe Nota Fiscal de\nServiço eletrônica\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nMunicípio: Santana de Parnaíba - SP\nAmbiente Gerador: 2\nTipo de Ambiente: 1\n\nCHAVE DE ACESSO DA NFS-e\n\n35473042267944968000147000000000000126084424151851\n\nNÚMERO DA NFS-e\n1\n\nNÚMERO DA DPS\n1\n\nEMITENTE DA NFS-e\nPrestador\n\nCOMPETÊNCIA DA NFS-e\n12/08/2026\n\nSÉRIE DA DPS\n70000\n\nSITUAÇÃO DA NFS-e\nNFS-e MEI\n\nDATA E HORA DA EMISSÃO DA NFS-e\n12/08/2026 22:48:37\n\nDATA E HORA DA EMISSÃO DA DPS\n12/08/2026 22:48:37\n\nFINALIDADE\n\nA autenticidade desta NFS-e pode ser verificada\n\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nPRESTADOR / FORNECEDOR\n\nNome / Nome Empresarial\n\nCNPJ/CPF / NIF\n67.944.968/0001-47\n\n67.944.968 PATRICIA ONORI BORCHES SANCHEZ\n\nEndereço\n\nAVENIDA MARCOS PENTEADO DE ULHOA RODRIGUES, 4446, TAMBORE\n\nSimples Nacional na Data de Competência\nOptante - Microempreendedor Individua...\n\nRegime de Apuração Tributária pelo SN\n\nindicador Municipal (Inscrição) Telefone\n\n- (11) 9462-0190\n\nCódigo IBGE / CEP\n35.47304 / 6543001\n\nMunicípio / Sigla UF\nSantana de Parnaíba / SP\n\nE-mail\nPATRICIAGBORCHESCONSULTORIA.COM\n\nTOMADOR / ADQUIRENTE\n\nNome / Nome Empresarial\n\nCNPJ/CPF /NIF\n16.699.869/0002-97\n\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\nEndereço\n\nGABRIEL MONTEIRO DA SILVA, 1480, CASA TERREA, JARDIM AMERICA\n\nIndicador Municipal (Inscrição) Telefone\n\nMunicípio / Sigla UF\nSão Paulo / SP\n\nE-mail\n\nCódigo IBGE / CEP\n35.50308 / 01.442-001\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\n\nCódigo de Tributação Nacional/Municipal\n08.02.01 /-\n\nLocal da Prestação / Sigla UF / País\nSantana de Parnaíba / SP / -\n\nCódigo da NBS\n1.2205.19.00\n\nInstrução, treinamento, orientação pedagógica e educacional, avaliação de conhecimentos de qualquer natureza.\n\nDescrição do Serviço\n\nTaxa administrativa inicial para estruturação, configuração e preparação das atividades do projeto, conforme condições comerciais apresentadas em contrato. Pagamento em 10 dias\napós emissão. Pagamento via PIX: 273.070.228-85\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\n\nBC ISSQN\n\nTipo de Tributação do ISSQN\nOperação Tributável\n\nAlíquota Aplicada\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\nSantana de Parnaíba / SP / -\n\nRetenção do ISSQN ISSQN Apurado\nNão Retido -\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n\nPIS - Débito Apuração Própria\n\nIRRF\n\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida Contribuições Sociais - Retidas\n\nDescrição Contrib. Sociais - Retidas\n\nTRIBUTAÇÃO IBS/CBS\n\nExclusões e Reduções da Base de Cálculo\nR$ 0,00\n\nAlíq. Efetiva Municipal - IBS\n\nValor Total Apurado - IBS\n\nCST / cClassTrib\n-1-\nBase de Cálculo Após Exclusões e Reduções\n\nValor Apurado Municipal - IBS\n\nAlíquota - CBS\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n=[=h=1-\n\nRed. Alíquota IBS / Red. Alíquota CBS Alíquota - IBS UF /IBS Mun\n=[-1- -[-\n\nAlíq. Efetiva Estadual - IBS Valor Apurado Estadual - IBS\n\nAlíquota Efetiva - CBS Valor Total Apurado - CBS\n\nVALOR TOTAL DA NFS-e\n\nTotal das Retenções (ISSQN / Federais)\n\nVALOR DA OPERAÇÃO | SERVIÇO\nR$ 3.250,00\n\nVALOR LÍQUIDO DA NFS-e\nR$ 3.250,00\n\nDesconto Incondicionado Desconto Condicionado\n\nVALOR LÍQUIDO DA NFS-e + IBS/CBS\nR$ 0,00\n\nTotal do IBS/CBS\nR$ 0,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nDATA CIENTIFICAÇÃO: IDENTIFICAÇÃO E ASSINATURA Nº NFS-e / CHAVE NFS-e\n1/35473042267944968000147000000000000126084424151851\n\n'

MOCK_OCR_NOTA_2 = 'N FSe Nota Fiscal de\nServiço eletrônica\n\nDANFSe v2.0\nDocumento Auxiliar da NFS-e\n\nMunicípio: Santana de Parnaíba - SP\nAmbiente Gerador: 2\nTipo de Ambiente: 1\n\nCHAVE DE ACESSO DA NFS-e\n\n35473042267944968000147000000000000226089997548496\n\nNÚMERO DA NFS-e\n2\n\nNÚMERO DA DPS\n2\n\nEMITENTE DA NFS-e\nPrestador\n\nCOMPETÊNCIA DA NFS-e\n12/08/2026\n\nSÉRIE DA DPS\n70000\n\nSITUAÇÃO DA NFS-e\nNFS-e MEI\n\nDATA E HORA DA EMISSÃO DA NFS-e\n12/08/2026 23:09:04\n\nDATA E HORA DA EMISSÃO DA DPS\n12/08/2026 23:09:04\n\nFINALIDADE\n\nA autenticidade desta NFS-e pode ser verificada\npela leitura deste código QR ou pela consulta da\nchave de acesso no portal nacional da NFS-e\n\nPRESTADOR / FORNECEDOR\n\nNome / Nome Empresarial\n\nCNPJ/CPF / NIF\n67.944.968/0001-47\n\n67.944.968 PATRICIA ONORI BORCHES SANCHEZ\n\nEndereço\n\nAVENIDA MARCOS PENTEADO DE ULHOA RODRIGUES, 4446, TAMBORE\n\nSimples Nacional na Data de Competência\nOptante - Microempreendedor Individua...\n\nRegime de Apuração Tributária pelo SN\n\nindicador Municipal (Inscrição) Telefone\n\n- (11) 9462-0190\n\nCódigo IBGE / CEP\n35.47304 / 6543001\n\nMunicípio / Sigla UF\n\nSantana de Parnaíba / SP\n\nE-mail\nPATRICIAGBORCHESCONSULTORIA.COM\n\nTOMADOR / ADQUIRENTE\n\nNome / Nome Empresarial\n\nCNPJ/CPF /NIF\n16.699.869/0002-97\n\nNAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA\n\nEndereço\n\nGABRIEL MONTEIRO DA SILVA, 1480, CASA TERREA, JARDIM AMERICA\n\nIndicador Municipal (Inscrição) Telefone\n\nMunicípio / Sigla UF\nSão Paulo / SP\n\nE-mail\n\nCódigo IBGE / CEP\n35.50308 / 01.442-001\n\nDESTINATÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nINTERMEDIÁRIO DA OPERAÇÃO NÃO IDENTIFICADO NA NFS-e\n\nSERVIÇO PRESTADO\n\nCódigo de Tributação Nacional/Municipal\n08.02.01 /-\n\nCódigo da NBS\n1.2205.19.00\n\nLocal da Prestação / Sigla UF / País\nSantana de Parnaíba / SP / -\n\nInstrução, treinamento, orientação pedagógica e educacional, avaliação de conhecimentos de qualquer natureza.\n\nDescrição do Serviço\n\nPrestação de serviços de preparação comercial, contemplando desenvolvimento de metodologia de vendas, orientação para atuação comercial dos lojistas, e implantação do Projeto\nCírculo mais Revista Aurora. - Pagamento 15 dias após emissão - Pagamento via PIX: 273.070.228-85\n\nTRIBUTAÇÃO MUNICIPAL (ISSQN)\n\nBC ISSQN\n\nTipo de Tributação do ISSQN\nOperação Tributável\n\nAlíquota Aplicada\n\nMunicípio / Sigla UF / País de Incidência do ISSQN\nSantana de Parnaíba / SP / -\n\nRetenção do ISSQN ISSQN Apurado\nNão Retido -\n\nTRIBUTAÇÃO FEDERAL (EXCETO CBS)\n\nPIS - Débito Apuração Própria\n\nIRRF\n\nCOFINS - Débito Apuração Própria\n\nContribuição Previdenciária - Retida Contribuições Sociais - Retidas\n\nDescrição Contrib. Sociais - Retidas\n\nTRIBUTAÇÃO IBS/CBS\n\nExclusões e Reduções da Base de Cálculo\nR$ 0,00\n\nAlíq. Efetiva Municipal - IBS\n\nValor Total Apurado - IBS\n\nCST / cClassTrib\n-1-\nBase de Cálculo Após Exclusões e Reduções\n\nValor Apurado Municipal - IBS\n\nAlíquota - CBS\n\nIndicador de Operação / Código IBGE Incidência / Município Incidência / Sigla UF\n=[=h=1-\n\nRed. Alíquota IBS / Red. Alíquota CBS Alíquota - IBS UF /IBS Mun\n=[-1- -[-\n\nAlíq. Efetiva Estadual - IBS Valor Apurado Estadual - IBS\n\nAlíquota Efetiva - CBS Valor Total Apurado - CBS\n\nVALOR TOTAL DA NFS-e\n\nTotal das Retenções (ISSQN / Federais)\n\nVALOR DA OPERAÇÃO | SERVIÇO\nR$ 6.500,00\n\nVALOR LÍQUIDO DA NFS-e\nR$ 6.500,00\n\nDesconto Incondicionado Desconto Condicionado\n\nVALOR LÍQUIDO DA NFS-e + IBS/CBS\nR$ 0,00\n\nTotal do IBS/CBS\nR$ 0,00\n\nINFORMAÇÕES COMPLEMENTARES\n\nTotais aproximados dos Tributos cfe. Lei nº 12.741/2012: Federais: -; Estaduais: -; Municipais: -;\n\nDATA CIENTIFICAÇÃO: IDENTIFICAÇÃO E ASSINATURA Nº NFS-e / CHAVE NFS-e\n21 35473042267944968000147000000000000226089997548496\n\n'


def _dummy(nome):
    caminho = f"tests/{nome}"
    os.makedirs("tests", exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(b"%PDF-1.4")
    return caminho


def _parse(monkeypatch, texto, nome):
    """Reproduz o caminho real destas notas: pdfminer não acha texto (PDF
    escaneado) e o extrator cai no OCR."""
    caminho = _dummy(nome)
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: "")
    monkeypatch.setattr(SPPdfExtractor, "_extract_via_ocr", lambda self: texto)
    try:
        return SPPdfExtractor(caminho).parse_multiple()
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_detect_layout(monkeypatch):
    caminho = _dummy("dummy_mei_patricia_detect.pdf")
    try:
        ex = SPPdfExtractor(caminho)
        ex.raw_text = MOCK_OCR_NOTA_1
        assert ex._detect_layout() == LAYOUT_NACIONAL_REFORMA
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


def test_nota_1_prestador_razao_social_nao_e_o_rotulo_cnpj(monkeypatch):
    """Bug central: RazaoSocial do prestador saía literalmente "CNPJ/CPF /
    NIF" (o próprio rótulo), nunca o nome real."""
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_1_prestador.pdf")
    p = notas[0].prestador
    assert p.razao_social == "PATRICIA ONORI BORCHES SANCHEZ"
    assert p.cnpj_cpf == "67944968000147"


def test_nota_1_tomador_razao_social_nao_e_o_rotulo_cnpj(monkeypatch):
    """Mesmo bug no tomador — grafia do rótulo sem espaço ("CNPJ/CPF /NIF"),
    tolerância de espaço já esperada pela heurística de detecção de rótulo."""
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_1_tomador.pdf")
    t = notas[0].tomador
    assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA"
    assert t.cnpj_cpf == "16699869000297"


def test_nota_1_prestador_ibge_e_cep_com_zero_inicial_perdido(monkeypatch):
    """"Código IBGE / CEP: 35.47304 / 6543001" -> IBGE 3547304 (Santana de
    Parnaíba/SP) e CEP 06543-001 (o "0" inicial não sobrevive ao OCR nesta
    coluna). Antes do fix a linha inteira era rejeitada: CEP saía
    "00000000" (sentinela) e o código do município caía no fallback por
    nome, que não conhece "Santana de Parnaíba" e devolvia a capital do
    estado (São Paulo, 3550308) por engano."""
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_1_ibge_cep.pdf")
    p = notas[0].prestador
    assert p.endereco.municipio == "Santana de Parnaíba"
    assert p.endereco.uf == "SP"
    assert p.endereco.codigo_municipio == "3547304"
    assert p.endereco.cep == "06543001"


def test_nota_1_prestador_indicador_municipal_nao_herda_o_cep(monkeypatch):
    """O Indicador Municipal do prestador vem legitimamente em branco ("-
    (11) 9462-0190", fundido com Telefone). Antes do fix a busca genérica
    por "qualquer token puramente numérico" nas linhas seguintes do bloco
    encontrava o CEP mal lido da própria linha "Código IBGE / CEP"
    ("6543001") e o aceitava como Indicador Municipal do prestador."""
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_1_im.pdf")
    p = notas[0].prestador
    assert not p.inscricao_municipal
    assert p.telefone == "(11) 9462-0190"


def test_nota_1_tomador_endereco_e_localizacao(monkeypatch):
    """Regressão: os demais campos do tomador (já corretos hoje) continuam
    corretos após o fix da razão social."""
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_1_tomador_end.pdf")
    t = notas[0].tomador
    assert t.endereco.logradouro == "GABRIEL MONTEIRO DA SILVA"
    assert t.endereco.numero == "1480"
    assert t.endereco.complemento == "CASA TERREA"
    assert t.endereco.bairro == "JARDIM AMERICA"
    assert t.endereco.municipio == "São Paulo"
    assert t.endereco.uf == "SP"
    assert t.endereco.codigo_municipio == "3550308"
    assert t.endereco.cep == "01442001"


def test_nota_1_prestador_endereco(monkeypatch):
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_1_prestador_end.pdf")
    p = notas[0].prestador
    assert p.endereco.logradouro == "AVENIDA MARCOS PENTEADO DE ULHOA RODRIGUES"
    assert p.endereco.numero == "4446"
    assert p.endereco.bairro == "TAMBORE"


def test_nota_1_identificacao(monkeypatch):
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_1_ident.pdf")
    nota = notas[0]
    assert len(notas) == 1
    assert nota.numero == "1"
    assert nota.codigo_verificacao == "35473042267944968000147000000000000126084424151851"
    assert nota.valores.valor_servicos == pytest.approx(3250.00)


def test_nota_2_prestador_e_tomador_razao_social(monkeypatch):
    """Segunda nota do MESMO prestador: mesma variação estrutural, mesmo
    fix precisa valer — só muda número/data/descrição do serviço."""
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_2, "dummy_mei_patricia_2_entidades.pdf")
    nota = notas[0]
    assert nota.numero == "2"
    assert nota.valores.valor_servicos == pytest.approx(6500.00)
    p, t = nota.prestador, nota.tomador
    assert p.razao_social == "PATRICIA ONORI BORCHES SANCHEZ"
    assert p.endereco.codigo_municipio == "3547304"
    assert p.endereco.cep == "06543001"
    assert not p.inscricao_municipal
    assert t.razao_social == "NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA"


def test_xml_abrasf_das_duas_notas(monkeypatch):
    """Saída final: os campos que o importador do usuário consome, nas DUAS
    notas."""
    from src.transformers.abrasf_transformer import Abrasf201Transformer

    notas_1 = _parse(monkeypatch, MOCK_OCR_NOTA_1, "dummy_mei_patricia_xml_1.pdf")
    xml_1 = Abrasf201Transformer().transform(notas_1[0])
    assert "<RazaoSocial>PATRICIA ONORI BORCHES SANCHEZ</RazaoSocial>" in xml_1
    assert "<RazaoSocial>NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA</RazaoSocial>" in xml_1
    assert "CNPJ/CPF" not in xml_1
    assert "<Cep>06543001</Cep>" in xml_1

    notas_2 = _parse(monkeypatch, MOCK_OCR_NOTA_2, "dummy_mei_patricia_xml_2.pdf")
    xml_2 = Abrasf201Transformer().transform(notas_2[0])
    assert "<RazaoSocial>PATRICIA ONORI BORCHES SANCHEZ</RazaoSocial>" in xml_2
    assert "<RazaoSocial>NAUTICA INDUSTRIA E COMERCIO DE MOVEIS E SERVICOS LTDA</RazaoSocial>" in xml_2
    assert "CNPJ/CPF" not in xml_2


def test_regressao_nota_11_sbs_continua_intacta(monkeypatch):
    """A nota nº 11 (SBS -> Condomínio TK Tower), já validada, tem o nome
    do prestador na 1ª linha não-vazia após o rótulo — o caminho ORIGINAL
    (sem a variante MEI) precisa continuar funcionando sem alterações."""
    from tests.test_danfse_nacional_reforma_layout import MOCK_OCR as MOCK_OCR_NOTA_11
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_11, "dummy_mei_patricia_regressao_11.pdf")
    p = notas[0].prestador
    t = notas[0].tomador
    assert p.razao_social == "UNICA SEGURANCA PATRIMONIAL LTDA"
    assert t.razao_social == "CONDOMINIO EDIFICIO TK TOWER"


def test_regressao_nota_171_macedo_continua_intacta(monkeypatch):
    """A nota nº 171/173 (Macedo), com colunas fundidas na mesma linha
    ("Nome / Nome Empresarial Município / Sigla UF"), usa um caminho
    totalmente diferente (fallback de linha fundida) — precisa continuar
    intocado."""
    from tests.test_danfse_nacional_reforma_texto_digital_sem_espacos import MOCK_OCR as MOCK_OCR_NOTA_171
    notas = _parse(monkeypatch, MOCK_OCR_NOTA_171, "dummy_mei_patricia_regressao_171.pdf")
    p = notas[0].prestador
    assert p.razao_social == "SUL&SEG COMERCIO E SERVICOS DE MANUTENCAO ELETRICOS LTDA"
    assert p.inscricao_municipal == "10030574"
