# -*- coding: utf-8 -*-
"""Texto REAL do OCR (Tesseract) da DANFSe Nacional v2.0 (pós-reforma
tributária) nº 5, SBS SOLUÇÕES INTEGRADAS DE SEGURANÇA ELETRÔNICA LTDA ->
BONI TRANSPORTES, LOGÍSTICA E COMÉRCIO LTDA (Lauro de Freitas/BA), PDF
escaneado. Mesma nota de
`test_danfse_reforma_sbs_colunas_fundidas_prestador_nao_identificado.py`
(reportada em 2026-09-15 como "um prestador não identificado"); ESTE arquivo
cobre dois bugs ADICIONAIS descobertos ao verificar o XML já corrigido:
Endereço "Não informado" para as duas entidades e ValorServicos = 0,00
apesar de ValorLiquidoNfse = 660,51.

Causa raiz nº 1 — Endereço "Não informado" para prestador E tomador: o
rótulo "Endereço" imprime colado à coluna vizinha "E-mail"/"Email" na MESMA
linha do cabeçalho ("Enderaço Email" no prestador — o OCR também troca
"Endereço" por "Enderaço" aqui —, "Endereço E-mall" no tomador). O padrão
original exigia a quebra de linha logo após o rótulo isolado e nunca casava
com texto extra colado nela. Além disso, como "Endereço" e "E-mail" são
colunas vizinhas impressas lado a lado, o OCR de página inteira funde as
colunas de VALOR também numa única linha: no prestador, "<endereço real>
financoirogisbsgrupo.com.br" (e-mail colado sem separador). **Fix:** o rótulo
passa a tolerar texto/ruído após "Endereço"/"Enderaço" na mesma linha, e um
sufixo de domínio comum (.com/.com.br/.net/.org/.gov) colado sem espaço de
sobra no fim da linha de valor é removido antes do parse dos segmentos.

Causa raiz nº 2 — ruído solto de OCR no fim do bairro do tomador: o bairro
real "ITINGA" (confirmado por captura de tela da nota) sai "[TINGA «" — o
"I" inicial confundido com um colchete solto (mesma família da confusão
"D"/"O" já vista no CNPJ deste layout) e um caractere de aspas/guilhemet
colado no fim. **Fix:** limpeza de ruído solto no fim do último segmento +
substituição pontual "[" -> "I" só quando imediatamente seguido de "TINGA".

Causa raiz nº 3 — ValorServicos = 0,00: esta nota é "Serviços sem a
incidência de ISSQN e ICMS" (operação não sujeita ao ISSQN) — nessas notas
o rótulo "VALOR DA OPERAÇÃO / SERVIÇO" sai tão degradado pelo OCR ("NATO DA
GERAÇÃO FRITO", sem nenhum fragmento reconhecível) que nunca casa, e "BC
ISSQN" nem chega a ser impresso (não há base de cálculo de um imposto que
não incide) — `serv` ficava 0,00 apesar de o grid mostrar claramente "VALOR
DA OPERAÇÃO / SERVIÇO: R$ 660,51" (conferido por captura de tela da própria
nota). **Fix:** quando não há NENHUMA retenção detectada (ISS não retido,
sem IRRF/INSS/contribuições sociais), o VALOR LÍQUIDO DA NFS-e — que já sai
correto, extraído por um rótulo que sobrevive ao OCR — serve de fallback
para `valor_servicos` (matematicamente idêntico ao bruto quando não há
nada retido; um fallback assim NÃO seria seguro se houvesse retenção, pois
aí o líquido seria menor que o valor da operação).

O texto abaixo é cópia literal (via `_extract_via_ocr`) da nota real,
completa (inclui a grade de valores, ausente do mock do outro arquivo de
teste desta mesma nota, que focava só em prestador/tomador)."""
import os

from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_NACIONAL_REFORMA

MOCK_TEXT = (
    ': DANFSe v2.0\n'
    'NFSe Duo etnia Documento Auxiliar da NFS-e\n\n'
    'CHAVE DE ACESSO DA NFS-e\n'
    '29192072246875522000152000000000000526086097254953\n\n'
    'NÚMERO DA NFS-e COMPETÊNCIA DA NFS-e DATA E HORA DA EMISSÃO DA NFS-e\n'
    '5 06/08/2026 06/08/2026 16:02:10\n\n'
    'NÚMERO DA DPS SÉRIE DA DPS DATA E HORA DA EMISSÃO DA DPS\n\n'
    '5 70000 06/08/2026 16:02:10\n\n'
    'pela isitura deste código OR ou pels consulta da\n'
    'EMITENTE DA NFS-e SITUAÇÃO DA NFS-s FINALIDADE chave de acesso no portal nacional da NFS-e\n'
    'Prestador NFS-g Gerada .\n\n'
    'PRESTADOR / FORNECEDOR CNPJ/CPF NIE Indicador Municipal (Inscrição) Telefona\n'
    '46.876.522/0001-52 10041978 (71) 99632-1095\n\n'
    'Nome / Nome Empresarial Município / Sigla UF Código IBGE | CEP\n\n'
    'SBS SOLUCOES INTEGRADAS DE SEGURANCA ELETRONICA ll LTDA Lauro de Freitas / BA 29.19207 ! 42.707-650\n\n'
    'Enderaço Email\n\n'
    'AVN PRAIA DE ITAPOAN, 131, VILAS DO ATLANTICO financoirogisbsgrupo.com.br\n\n'
    'Simples Nacional na Data de Competência Regime de Apuração Tributária pelo SN\n\n'
    'Não optante -\n\n'
    'TOMADOR |! ADQUIRENTE CNPJ/CPF INF Indicador Municipal (Inscrição) Telefone\n'
    'D4.555.283/0003-50 - E\n\n'
    'Nome / Nome Empresarial Municipio | Sigla UF Código IBGE | CEP\n'
    'BONI TRANSPORTES, LOGISTICA E COMERCIO LTDA. Lauro de Freitas / BA 29.19207 | 42.738-205\n\n'
    'Endereço E-mall\n'
    'MARIA QUITERIA, 263, GALPÃO LOT DESMEMBRAMENTO DIAMANTE, [TINGA «\n\n'
    'DESTINATÁRIO DA O) ÃO NÃO IDENTIFICADO NA NFS-€\n'
    'INTERMEDIÁRIO DA OPER O IDENTIFICADO NA NFS-e\n'
    'RVIÇO Código de Tributação Nacional/Municipal Código da NES Local da Prestação | Sigla UF / Pais\n'
    '99.01,01/- - Lauro de Freitas / BA) -\n\n'
    'Serviços sem a incidência de ISSQN e ICMS\n\n'
    'Descrição do Serviço\n\n'
    'CONTRATO Nº [TS BTLC. 014/2024 SBS TEC II]\n\n'
    'COMPETÊNCIA: 09/2025\n\n'
    'LOCAÇÃO DE EQUIPAMENTOS E MONITORAMENTO - R$ 560,51\n\n'
    'VENCIMENTO: 05/09/2026\n\n'
    'FORMA DE PAGAMENTO: BOLETO BANCÁRIO - BANCO DO BRASIL\n\n'
    'TRIBUT; MUNICIPAL (15SQN) - OPERAÇÃO NÃO SUJEITA AO ISSQN\n'
    'TRIBUTAÇÃO FEDERAL (EXCETO IRRF Contribuição Previdenciária - Retida Contribuições Sociais - Retidas\n\n'
    'PIS - Débito Apuração Própria COFINS - Débito Apuração Própria Descrição Contrib. Sociais - Retidas\n\n'
    'TRIBUT, TEBSICES TST cClassTrib Indicador do Oporação | Código IBGE Incidência / Municipio Incidência / Sigla UF\n'
    'Sis efalafo\n\n'
    'Exclusões e Reduções da Base de Cálculo Base de Cálculo Após Exclusões e Reduções Red. Aliquota IBS / Red. Aliquota CBS Aliquota - [BS UF /HBS Mun\n\n'
    'R$ 0,00 - -f-d- fe\n\n'
    'Alig. Efetiva Municipal - IBS Valor Apurado Municipal - IBS Alig. Efetiva Estadual -IBS Valor Apurado Estadual -I85\n\n'
    'Valor Total Apurado -IBS Alíquota - CBS Aliquota Efetiva - CBS Valor Total Apurado - CBS\n\n'
    'VALOR TOTAL DA NFS-s NATO DA GERAÇÃO FRITO Desconto Incondicionado Desconto Condicionado\n\n'
    'Total das Retenções (ISSQN / Federais) VALOR LÍQUIDO DA NFS-e VALOR LIQUIDO DA NFS-o + ESTES\n'
    '- R$ 660,51 850,00\n\n'
    'INFORMAÇÕES COMPLEMENTARES\n\n'
    'Totais aproximados dos Tributos ce. Lei nº 12.741/2012: Federais: 0,00 %; Estaduais: 0,00 %; Municipais: 0,00 %;\n\n'
    'DATA CIENTIFI O E ASSINATURA NO NFS / CHAVE NFS-e\n'
    '5 / 29192072246876522000152000000000000526085097254953\n'
)


def _novo_extrator():
    dummy_path = "tests/dummy_sbs_solucoes_5_endereco_valor.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    extractor = SPPdfExtractor(dummy_path)
    extractor.raw_text = MOCK_TEXT
    extractor.layout = LAYOUT_NACIONAL_REFORMA
    return extractor, dummy_path


def test_endereco_prestador_sem_email_colado():
    extractor, dummy_path = _novo_extrator()
    try:
        prestador = extractor._extrair_entidade('Prestador')
        assert prestador.endereco.logradouro == "AVN PRAIA DE ITAPOAN"
        assert prestador.endereco.numero == "131"
        assert prestador.endereco.bairro == "VILAS DO ATLANTICO"
        assert '.com' not in prestador.endereco.bairro
        assert '.com' not in prestador.endereco.logradouro
    finally:
        os.remove(dummy_path)


def test_endereco_tomador_com_bairro_itinga_corrigido():
    extractor, dummy_path = _novo_extrator()
    try:
        tomador = extractor._extrair_entidade('Tomador')
        assert tomador.endereco.logradouro == "MARIA QUITERIA"
        assert tomador.endereco.numero == "263"
        assert tomador.endereco.complemento == "GALPÃO LOT DESMEMBRAMENTO DIAMANTE"
        # Bairro real "ITINGA" (Lauro de Freitas/BA) - o "I" inicial saía
        # como colchete solto no OCR ("[TINGA «").
        assert tomador.endereco.bairro == "ITINGA"
    finally:
        os.remove(dummy_path)


def test_valor_servicos_usa_liquido_quando_operacao_nao_sujeita_a_issqn_sem_retencao():
    extractor, dummy_path = _novo_extrator()
    try:
        valores = extractor._extrair_valores()
        # "VALOR DA OPERAÇÃO / SERVIÇO" sai ilegível pelo OCR nesta nota
        # (operação não sujeita ao ISSQN); sem nenhuma retenção, o valor
        # líquido da NFS-e (R$ 660,51, extraído corretamente por um rótulo
        # que sobrevive ao OCR) é usado como valor do serviço.
        assert valores.valor_servicos == 660.51
        assert valores.valor_liquido_nfse == 660.51
        assert valores.valor_iss == 0.0
        assert valores.valor_ir == 0.0
        assert valores.valor_inss == 0.0
    finally:
        os.remove(dummy_path)


def test_valor_servicos_nao_usa_liquido_quando_ha_retencao_issqn():
    # Guarda de regressão: o fallback só pode entrar em cena quando NÃO há
    # nenhuma retenção — caso contrário o líquido é menor que o valor da
    # operação, e usá-lo fabricaria um ValorServicos plausível-porém-errado.
    texto_com_retencao = MOCK_TEXT.replace(
        'TRIBUT; MUNICIPAL (15SQN) - OPERAÇÃO NÃO SUJEITA AO ISSQN\n',
        'TRIBUT; MUNICIPAL (15SQN) - OPERAÇÃO NÃO SUJEITA AO ISSQN\n'
        'IRRF\nR$ 10,00\n\n'
    )
    extractor, dummy_path = _novo_extrator()
    extractor.raw_text = texto_com_retencao
    try:
        valores = extractor._extrair_valores()
        assert valores.valor_servicos == 0.0
    finally:
        os.remove(dummy_path)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
