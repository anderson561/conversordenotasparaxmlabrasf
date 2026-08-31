# -*- coding: utf-8 -*-
import os
from src.extractors.pdf_extractor import SPPdfExtractor, LAYOUT_LOCALIZA_PETROLINA

# Texto REAL extraído por pdfminer (`extract_text`) da fatura Localiza nº
# 53044, agência MC LOCADORA PETROLINA LTDA (Petrolina/PE, mesmo CNPJ
# corporativo `06.890.020/0001-61` da Localiza) -> TEMIS PROJETOS DE MEIO
# AMBIENTE E SUSTENTABILIDADE LTDA, R$768,57. PDF digital sem OCR, 6 páginas
# (fatura/pág.1, boleto/pág.2, contrato+demonstrativo de valores/pág.3,
# recibo/pág.4 e 6 vazias, resumo de substituições/pág.5). Preservado
# verbatim - os campos do box "CLIENTE" da página 1 saem em ordem INVERTIDA
# (valor antes do rótulo, ex. "...PETROLINA - PECNPJ...", "18/12/2025...DATA
# DE EMISSÃOCÓDIGO..."), diferente das 4 variantes já cobertas por
# `LAYOUT_LOCALIZA` (rótulo sempre antes do valor) - por isso o tomador, a
# data de emissão e o município do prestador (Salvador/BA por default, em
# vez do real Petrolina/PE) caíam nos fallbacks. O valor real da fatura só
# existe na página 3 ("TOTAL GERAL 768,57"), que não repete "MC LOCADORA
# PETROLINA LTDA" nem o CNPJ - só o título/cláusulas genéricas "Contrato de
# Aluguel de Carros/Proposta de Seguro" (comum a QUALQUER nota Localiza) -,
# então essa página caía inteira em `LAYOUT_GENERICO` e era descartada.
MOCK_TEXT = 'VALOR DO SEGURO *ACPNZ0412290001ALUGUEL CONFORME CONTRATO R$ 768,57R$ 53,85R$ 714,72assistenciaaclientes@localiza.comTEL 0800 979 2020ASSISTÊNCIA A CLIENTES56308000 - PETROLINA - PECNPJ - 06.890.020/0001-61AGÊNCIA CENTRO - PETROLINA                                  MC LOCADORA PETROLINA LTDAAVENIDA HONORATO VIANA, 309 - GERCINO COELHODESCRIÇÃOVALORVALOR TOTAL02/01/2026À PRAZOVENCIMENTOCONDIÇÕES DE PAGAMENTOFATURA / DUPLICATANº:ACPNZ - 53044CLIENTEINSC. ESTADUAL         06972548318/12/202502640209DATA DE EMISSÃOCÓDIGO07.345.543/0001-90TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA41830540 - SALVADOR - BARUA TERRITORIO DO AMAPA, 146 CS 2 - PITUBACNPJCEP/CID/UFENDEREÇOSacador:Aceite:*Valor repassado para a SANCOR SEGUROS DO BRASIL S.A , CNPJ/MF nº 17.643.407/0001-30  Processo SUSEP n° 15414.900333/2014-50.\x0c   341-7   34191.09610 51809.718292 01095.970008 3 13170000076857Beneficiário   MC LOCADORA PETROLINA LTDAAgência/Código do Beneficiário   8290 / 10959-7Espécie   R$Quantidade   001Nosso número               109/61518097-1Endereço do Beneficiário   AVENIDA HONORATO VIANA, 309 - GERCINO COELHO   Petrolina - PE - CEP: 56308000Número do documento   53044CPF/CNPJ   06890020000161Vencimento   05/01/2026Valor documento768,57(-) Desconto / Abatimentos (-) Outras deduções (+) Mora / Multa (+) Outros acréscimos (=) Valor cobrado Pagador    TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA 07345543000190Demonstrativo    MC LOCADORA PETROLINA LTDA      Autenticação mecânica          Corte na linha pontilhada   341-7   34191.09610 51809.718292 01095.970008 3 13170000076857Local de pagamento   ATÉ O VENCIMENTO, PAGUE EM QUALQUER BANCO OU CORRESPONDENTE NÃO BANCÁRIOAPÓS O VENCIMENTO, ACESSE ITAU.COM.BR/BOLETOS E PAGUE EM QUALQUER BANCO OUCORRESPONDENTE NÃO BANCÁRIO.Vencimento05/01/2026Beneficiário    MC LOCADORA PETROLINA LTDA - CNPJ/CPF: 06890020000161Agência/Código do Beneficiário8290 / 10959-7Data do documento      18/12/2025Nº documento      53044Espécie doc.      DMAceite      NData processamento   18/12/2025Nosso número109/61518097-1Uso do Banco     Carteira      109Espécie      R$Quantidade      001Valor Documento      768,57(=) Valor documento768,57Instruções de responsabilidade do BENEFICIÁRIO. Qualquer dúvida sobre este boleto, contacte o BENEFICIÁRIO. APÓS O VENCIMENTO COBRAR: JUROS DE 1,00% AO MÊS e MULTA DE 2,00% AO MÊS   NEGATIVAR APÓS 5 DIAS DO VENCIMENTO.   BOLETO SUJEITO A PROTESTO.   53044(-) Desconto / Abatimentos     (-) Outras deduções     (+) Mora / Multa     (+) Outros acréscimos     (=) Valor cobrado     Pagador:  TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA 07345543000190CPF/CNPJ:  07345543000190Endereço: RUA TERRITORIO DO AMAPA - 146 - PITUBA - Salvador - BA - CEP: 41830540 CASA 02Sacador/Avalista:Código de baixa:Endereço do Sacador/Avalista      Autenticação Mecânica - Ficha de CompensaçãoCorte na linha pontilhada\x0cContrato de Aluguel de Carros/Proposta de SeguroN° ACPNZ0412290001FaturadoACPNZ-53044Empresa:02640209TEMIS PROJETOS DE MEIOAMBIENTE E SUSTENTABILIDADELTDAUsuário:14330634DAFNE PAULINA DE SOUZA ALVESVeículo:SOF0I54      Argo Drive 1.0 Custo Pré-fixado de Limite de Danos: Grupo Reservado: CE - Econômico Especial Grupo Cobrado: CE - Econômico Especial   Danos ao Carro: 4.000,00 Danos a Terceiros: 1.000,00 Danos PT/Furto/Roubo: 4.000,00 Saída / Vigência Seguro: 15/12/2025 08:11 Centro - Petrolina Km:27.831 Tanque:8/8  Retorno / Vigência Seguro: 18/12/2025 09:48 Centro - Petrolina Km:28.168 Tanque:8/8 Utilização: 3 Diárias 1 Hora 37 Minutos  KM Utilizado:337 Tarifa:016802 - Tarifa Diária Fr Pj - Oferta Especial Plus Km:Livre Reserva: PCYU53OLZ9DF Forma de Pagamento:  À Faturar Demonstrativo de Valores:Valor UnitárioDesconto (%)Desconto (R$)Valor LíquidoQuantidadeValor FinalDiária 799,95 78,02 624,11 175,84 3,00  527,52  Proteção do Carro 34,95 34,95 3,00  104,85  Seguros de terceiros RCFA 17,95 17,95 3,00  53,85  Taxa de Aluguel 12% 82,35  TOTAL GERAL 768,57  FATURADO PARA EMPRESA 768,57  SALDO DEVIDO 0,00  Observações:* Contrato dispensa autorização ou voucher. * Tarifa válida para devolução a partir do dia 18/12/2025 às 08:11 até o dia 13/01/2026 às 08:11.Por este instrumento particular, as partes acima qualificadas celebram contrato de locação de veículo nas condições abaixo ajustadas:Cláusula 1ª.: O CLIENTE declara que devolveu o carro alugado na data acima e que conferiu e aprovou os valores da locação, sob pena de sua omissão implicar em anuência,na forma do art. 111 do Código Civil.Cláusula 2ª.: O CLIENTE declara que tomou conhecimento prévio e anuiu às Condições Gerais do Contrato de Aluguel de Carros e Seguro, disponível em:https://www.localiza.com/Contratos/brasil/pt/Contrato_Geral_Aluguel_de_Carros.pdf, bem como às Condições Gerais que regem o contrato de seguro do carro.Acesse e responda nossa pesquisa de satisfação e consulte os pontos acumulados nesta locação\x0c\x0c14330634 - DAFNE PAULINA DE SOUZA ALVESUsuárioResumo de Substituições do ContratoNo. ACPNZ0412290001Avenida. Honorato Viana, 309 - Gercino Coelho56308000 - Petrolina - PECNPJ: 06890020000161Telefone +55 87 3862 2788Assistência a Clientes: 0800 979 2020MC LOCADORA PETROLINA LTDAAGÊNCIA CENTRO - PETROLINALocatárioCNPJ: 0734554300019002640209 - TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDAR: Territorio do Amapa n.146 - Pituba41830540 Salvador - BA - BrasilÀ FaturarPCYU53OLZ9DFReservaSOF0I54Argo 1.0 4P C/Ar15/12/2025 11:2418/12/2025 09:482223799,952.399,853370,00SNX9C97C3 Attraction15/12/2025 08:1115/12/2025 11:240300,000,00240,00PlacaData SaídaModeloCobradaUtilizadaData RetornoValorUnitárioCombustívelValorTotalKmHoraDiaDiaTOTAIS:OBS:xAo assinar este documento você estará aderindo e se vinculando às Condições Gerais do Contrato de Aluguel de Carros, disponível em: https://www.localiza.com/Contratos/brasil/pt/Contrato_Geral_Aluguel_de_Carros.pdf, documento que encontra-se exposto e lhe foi apresentado na agência de contratação.2.399,853610,00\x0c'


def test_detect_layout_localiza_petrolina():
    dummy_path = "tests/dummy_localiza_petrolina.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    try:
        ex = SPPdfExtractor(dummy_path)
        ex.raw_text = MOCK_TEXT
        assert ex._detect_layout() == LAYOUT_LOCALIZA_PETROLINA
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


def test_extract_localiza_petrolina_nfse_53044(monkeypatch):
    """Achado real: tomador saía "Não Identificado"/CNPJ zerado, valor saía
    0,00 e o município do prestador saía Salvador/BA (default) em vez de
    Petrolina/PE - tudo por causa da ordem invertida (valor antes do rótulo)
    do box "CLIENTE" da página 1 e da página 3 (onde fica o valor real,
    "TOTAL GERAL") caindo em `LAYOUT_GENERICO` e sendo descartada."""
    dummy_path = "tests/dummy_localiza_petrolina_full.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")

    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: MOCK_TEXT)

    try:
        extractor = SPPdfExtractor(dummy_path)
        nfse_list = extractor.parse_multiple()
        assert len(nfse_list) == 1
        nfse = nfse_list[0]

        assert nfse.numero == "53044"
        assert nfse.codigo_verificacao == "FATURA"
        assert nfse.data_emissao.strftime("%d/%m/%Y") == "18/12/2025"
        assert nfse.competencia.year == 2025
        assert nfse.competencia.month == 12

        p = nfse.prestador
        assert p.cnpj_cpf == "06890020000161"
        assert p.razao_social == "MC LOCADORA PETROLINA LTDA"
        assert p.endereco.logradouro == "AVENIDA HONORATO VIANA"
        assert p.endereco.numero == "309"
        assert p.endereco.bairro == "GERCINO COELHO"
        assert p.endereco.municipio == "PETROLINA"
        assert p.endereco.uf == "PE"
        assert p.endereco.cep == "56308000"
        assert p.endereco.codigo_municipio == "2611606"

        t = nfse.tomador
        assert t.cnpj_cpf == "07345543000190"
        assert t.razao_social == "TEMIS PROJETOS DE MEIO AMBIENTE E SUSTENTABILIDADE LTDA"
        assert t.endereco.logradouro == "RUA TERRITORIO DO AMAPA"
        assert t.endereco.numero == "146"
        assert t.endereco.bairro == "PITUBA"
        assert t.endereco.municipio == "Salvador"
        assert t.endereco.uf == "BA"
        assert t.endereco.cep == "41830540"

        v = nfse.valores
        assert v.valor_servicos == 768.57
        assert v.valor_liquido_nfse == 768.57
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)
