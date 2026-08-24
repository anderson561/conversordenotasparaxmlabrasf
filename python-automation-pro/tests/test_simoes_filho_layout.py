# -*- coding: utf-8 -*-
"""Novo layout Simões Filho/BA (`simoes_filho_ba`) — nota real nº 122
(VITORIOS EMPILHADEIRAS COMERCIO E SERVIÇOS LTDA -> BONI TRANSPORTES,
LOGISTICA E COMERCIO LTDA, R$ 440,00), pág. 1 de um PDF de 2 páginas cuja
pág. 2 é a nota irmã Lauro de Freitas/NFTS (já coberta por
`test_lauro_de_freitas_*`).

A constante já existia (`LAYOUT_SIMOES_FILHO`) mas nunca tinha extração
dedicada nem prioridade de detecção correta: a marca genérica de Barreiras/BA
("Data Fato Gerador", mesma plataforma/template) casava PRIMEIRO e a nota
inteira caía no layout errado — `Numero` saía "246" (vazado de "orçamento nº
246" na discriminação, não o "Nº da Nota Fiscal" real), `CodigoVerificacao`
ficava travado no sentinela, o CNPJ do prestador saía IGUAL ao do tomador
(cross-contaminação de entidade) e o Município de ambas as entidades caía no
fallback de Salvador (2927408) por a linha solta "<Município> - <UF> - CEP:
<cep>" não ser reconhecida pelo parser genérico.
"""
import os
import pytest
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_SIMOES_FILHO

MOCK_TEXT = (
    'Razão Social: VITORIOS EMPILHADEIRAS COMERCIO E SERVIÇOS LTDA\n\n'
    'Nome Fantasia: VITORIOS EMPILHADEIRAS\n'
    'Endereço: Avenida da Republica, 128, QUADRAO? - CIA |\n\n'
    'Simões Filho - BA - CEP: 43716-435\n\n'
    'E-mail: MANUTENCAO GVITORIOSEMPILHADEIRAS.COM.BR - Fone: (7 1]3396-2555 - Celular: 71 97000736 - Site: ........\n'
    'Inscrição Estadual: ........ - Inscrição Municipal: 26201 - CPF/CNPJ; 50.945 432/0001-11\n\n'
    'NOTA FISCAL DE SERVIÇOS ELETRÔNICA - NFSe\n'
    'PREFEITURA MUNICIPAL DE SIMÕES FILHO\n'
    'e Codigo de Verificação para Autanticação: 31752883 7 ag\n'
    'sis HR cnes: ape postato bic BAGOvER Es:\n\n'
    'pu = Emitido am 2270712026 24 14:46\n\n'
    'Data Fato Gerador Exigibilidade de 155 Regime Tributário Numero RPS Serie RPS | Nº da Note Fiscal\n'
    'aeorianas Exguei Tetusisção Normal - - |\n'
    'Tpode Recolhimento | Simples Tocal de Frostação Tocal de Recolhimento 202600000000122\n'
    'PRESTADOR\n\n'
    'Razão Social: VITORIOS EMPILHADEIRAS COMERCIO E SERVIÇOS LTDA\n'
    'Nome Fantasia: VITORIOS EMPILHADEIRAS\n'
    'Encereço: Avenida da Republica, 128, QUADRADZ - CIA |\n'
    'Simões Filho - BA - CEP: 49716-435\n'
    'E-mail: MANUTENCAO QVITORIOSEMPILHADEIRAS.COM.BR - Fone: (71)3396-2555 - Celular: 71 87000736 - Site: ........\n'
    'Inscrição Estadual: .......- « Inscrição Municipal: 28201 - CPF/CNPJ; 50.945 432/0001-11\n'
    'TOMADOR\n\n'
    'Razão Social: BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA.\n\n'
    'Endereço: Rua Doutor Gerino de Souzs Filho, 1025, ACESSO PELA RUA JOELMA S, MENDES LOTES U4 A US QUADRA - Itinga\n'
    'Leuro de Freitas - BA - CEP. 42738200\n\n'
    'E-mail: financeirof Bbonialimentos.com.br - Fone: 7132835325 - Celular. 7132835323\n'
    'Inscrição Estadual: 55694713 - Inscrição Municipal: 166791 - CPF/CNPJ: 04.555.283/0001-99\n\n'
    'SERVIÇO NACIONAL\n\n'
    '140101 - Lubrificação, limpeza, ilustração, revisão, carga e recarga, conserto, restauração, blindagem, manutenção e conservação de máquinas, veiculos,\n'
    'aparelhos, equipamentos, motores, elevadores ou de qualquer objeto (exceto peças e partes empregadas, que ficam sujeitas ao ICMS).\n\n'
    'DISCRIMINAÇÃO DOS SERVIÇOS\n'
    'Serviço técnico realizado em empilhadeira EGV sório: 340261V03809, problema encontrado conexão do dllingro central folgada, Toi feito o aperio da conexão\n'
    'Maquina liberada para o operação, orçamento nº 246, relatório nº 76971645, atendimento realizado no dis 15/07/2026.\n'
    'Condições de pagamento 14 dias via Pix CNPJ: 50.949.432/0001-11\n'
    'Vencimento: 05/08/2026.\n\n'
    'OBSERVAÇÃO\n\n'
    'VALOR SERVIÇO (R$)] DEDUÇÕES (R$) DESCONTO INCONDICIONAL (R$) BASE CÁLCULO (R$) ALÍQUOTA (%) ss (R$)\n'
    '440,00 0,00 0,00 440,00 285 12,54\n\n'
    'DEMONSTRATIVO DOS TRIBUTOS FEDERAIS DESCONTO (R$) OUTRAS (R$) VALOR LÍQUIDO (85)\n'
    'o E a o |\n'
    '00 | f\n'
    '000 0,00 0,00 0.00 000 440,00\n\n'
    'OUTRAS INFORMAÇÕES\n\n'
    'de acesso Ambiente de Dados Nacional; 25307091250348452000711 012228070003046849\n'
    '(Valor Liquido = Valor Serviço - INSS - IR - CSLL - Outras Retanções - COFINS - PIS - Descontos Diversos - 155 Retido - Desconto Incondicional)\n\n'
    'ESTE DOCUMENTO FO! EMITIDO POR EMPRESA OPTANTE DO SIMPLES NACIONAL(Art. 23 da LC 123/2006), DEVENDO NESTA CONDIÇÃO O PRESTADOR.\n'
    'INFORMAR A ALÍQUOTA ENTRE 2 A 5%, CONFORME TABELA DE ENQUADRAMENTO DE ACORDO COM O SEU FATURAMENTO.O RECOLHIMENTO DO I53QN E\n'
    'REALIZADO VIA DAS EMITIDO PELA RECEITA FEDERAL DO BRASIL.\n\n'
    'Consulte a autenticidade deste dacumento acessando q sãe www.sefaz.simoesfilha.ba.gov.br\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_simoes_filho_122.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    return extractor, dummy_path


def test_deteccao_prioriza_simoes_filho_sobre_barreiras():
    extractor, dummy_path = _novo_extrator()
    try:
        assert extractor._detect_layout() == LAYOUT_SIMOES_FILHO
    finally:
        os.remove(dummy_path)


def test_numero_recupera_da_nota_fiscal_nao_do_orcamento():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        # BUG CORRIGIDO: a extração genérica pegava "246" (orçamento do
        # prestador, dentro da discriminação), não o "Nº da Nota Fiscal" real.
        assert extractor._extrair_numero() == "202600000000122"
    finally:
        os.remove(dummy_path)


def test_codigo_verificacao_e_sentinela_nao_numero_garantidamente_errado():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        # O valor real é alfanumérico ("bd17528e3") e o Tesseract nunca lê
        # certo nesta plataforma (testado exaustivamente) — sentinela
        # honesto é preferível a uma leitura numérica garantidamente errada.
        assert extractor._extrair_codigo_verificacao() == "XXXX-XXXX"
    finally:
        os.remove(dummy_path)


def test_prestador_e_tomador_nao_compartilham_cnpj():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        prestador = extractor._extrair_entidade('Prestador')
        tomador = extractor._extrair_entidade('Tomador')
        # BUG CORRIGIDO: prestador saía com o MESMO CNPJ do tomador.
        assert prestador.cnpj_cpf != tomador.cnpj_cpf
        assert prestador.cnpj_cpf == "50945432000111"
        assert "VITORIOS EMPILHADEIRAS" in prestador.razao_social
        assert tomador.cnpj_cpf == "04555283000199"
        assert "BONI TRANSPORTES" in tomador.razao_social
    finally:
        os.remove(dummy_path)


def test_municipio_prestador_recuperado_da_linha_solta_apos_endereco():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        prestador = extractor._extrair_entidade('Prestador')
        # BUG CORRIGIDO: caía em "Não informado"/fallback de Salvador
        # (2927408) — a linha "<Município> - <UF> - CEP:" não tem rótulo
        # próprio e o parser genérico não a reconhecia.
        assert prestador.endereco.municipio == 'Simões Filho'
        assert prestador.endereco.codigo_municipio == "2930709"
        assert prestador.endereco.uf == "BA"

        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.endereco.municipio == 'Lauro de Freitas'
        assert tomador.endereco.codigo_municipio == "2919207"
        assert tomador.endereco.bairro == 'Itinga'
    finally:
        os.remove(dummy_path)


def test_recorte_dedicado_do_prestador_tem_prioridade_sobre_corpo_degradado():
    """Quando `_ocr_recut_prestador_simoes_filho` roda (via `_ocr_page` real),
    o resultado é guardado em `_simoes_filho_prestador_recut` e deve prevalecer
    sobre a leitura de página inteira para CEP/Inscrição Municipal — aqui
    simulado diretamente, sem depender do Tesseract instalado na máquina de
    CI."""
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        extractor._simoes_filho_prestador_recut = (
            'Razão Social: VITORIOS EMPILHADEIRAS COMERCIO E SERVIÇOS LTDA\n'
            'Nome Fantasia: VITORIOS EMPILHADEIRAS\n'
            'Endereço: Avenida da Republica, 128, QUADRA02 - CIA I\n'
            'Simões Filho - BA - CEP: 43716-435\n'
            'E-mail: MANUTENCAO@VITORIOSEMPILHADEIRAS.COM.BR\n'
            'Inscrição Estadual: ........ - Inscrição Municipal: 26201 - CPF/CNPJ; 50.945 432/0001-11\n'
        )
        prestador = extractor._extrair_entidade('Prestador')
        # CEP e Inscrição Municipal do recorte (corretos) prevalecem sobre os
        # do corpo (49716-435 / 28201, ambos errados nesta nota real).
        assert prestador.endereco.cep == "43716435"
        assert prestador.inscricao_municipal == "26201"
    finally:
        os.remove(dummy_path)


def test_valores_grade_com_aliquota_sem_separador_decimal():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 440.0
        assert valores.base_calculo == 440.0
        # "285" (sem vírgula, achado real de OCR) -> 2,85% -> fração 0.0285.
        assert valores.aliquota == pytest.approx(0.0285)
        assert valores.valor_iss == pytest.approx(12.54)
    finally:
        os.remove(dummy_path)


def test_data_emissao_usa_data_de_atendimento_em_vez_de_hoje():
    """A linha "Emitido em 22/07/2026 21:14:46" nunca sai legível do OCR
    nesta plataforma (testado exaustivamente — zooms, PSMs, binarização,
    recorte isolado). Sem um fallback dedicado, a extração genérica cairia no
    sentinela "agora" (mês errado na Competência). A data de atendimento
    citada na própria discriminação ("...no dia 15/07/2026") é o único sinal
    de data limpo e confiável nesta nota — usada como proxy, confirmada de
    forma independente pela Competência "07/2026" da nota irmã (Lauro de
    Freitas/NFTS, mesma transação)."""
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        data = extractor._extrair_data_emissao()
        assert data.year == 2026
        assert data.month == 7
        assert data.day == 15
        # Não deve mais cair no sentinela "agora" (mês/ano de hoje).
        assert not extractor._data_emissao_fallback
    finally:
        os.remove(dummy_path)


def test_discriminacao_nao_engole_a_grade_de_valores_e_rodape():
    extractor, dummy_path = _novo_extrator()
    try:
        extractor.layout = LAYOUT_SIMOES_FILHO
        disc = extractor._extrair_discriminacao()
        # BUG CORRIGIDO: sem limite dedicado, a discriminação vazava até o
        # fim do documento inteiro (grade de valores + rodapé legal).
        assert "orçamento nº 246" in disc
        assert "VALOR SERVIÇO" not in disc
        assert "SIMPLES NACIONAL" not in disc
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
