import os

import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

# NFS-e da PREFEITURA DO MUNICÍPIO DE SÃO PAULO (modelo padrão), impressa do
# navegador (cabeçalho "19/10/2026, 17:34 Email – Luiz Argolo – Outlook",
# rodapé com a URL do outlook.live.com) e ESCANEADA — nota real nº 00000228,
# APROAR PLANEJAMENTO PATRIMONIAL LTDA -> PATRICORP PATRIMONIAL LTDA.,
# R$ 41.326,00 (Notas/102026/APROAR NF 228 AGO OUT004.pdf, 2026-11-04).
#
# CAMADA: texto REAL que o pdfminer extrai do PDF — camada de OCR gravada
# pelo scanner, reconhecida como japonês. Tem "CNPJ" e 1239 caracteres, então
# passava no portão global de OCR; nenhum layout casava e o PDF saía com zero
# notas ("parece ser baseado em imagem/scan ou vazio").
#
# OCR: texto REAL devolvido pelo `_ocr_page` desta página (Tesseract), já com
# os recortes dedicados do SP escaneado prependados (código do serviço,
# retenções do modelo "Contribuição Previdenciária", cabeçalho com a leitura
# alternativa B/8 do código de verificação) e a discriminação relida.

CAMADA = '19I「O鰹026, 17二鞠\n\nEmail - Luiz AngoIo - Out10Ok\n\nPR断割TURÅ Do MUN-CipiO DE SÅo pAUしO\n\nSたCRどIA膿IA MUNICI寄AしDA FAZENDA\n\nNOTA馴ScAし且的ONICA鵬S囲IVl$OS - NFS・e\n\nN心m屯ro dむNo章a\n\nOOOOO2ま8\n\nひa章aさ魅o棺de E請issきo\n\n1 9I書伽を026 1 4:45脚5\n\n髄拙go de Ⅵ如簡閲辞o\nV喜8寄・珊\n\nC陣CNP」: 11.437.働けIOOl-章5\n\n書nsc噂o議unicゆa農`.㈱.榔事2\n\n飾訊眼\n\nNomel京a務o敏鵜ial: ▲農韓o餓pし側と」A調印町0寄調書議o軸l▲し皿\n\np則:S¶軸)o照りたS田恥部悔\n\nNome佃敬重o SociaI: P鼻面りCO則書PAT書棚譲oNIAしし丁DA.\n\nC即すCNPJ: 00.625.書91脚1-87\n\nEnder基準O: AVI: TAN脚o関崎「側15 ]偶5 - c劇議事剛鵬問晩S ▲照Vo駆お葛cEP: \'1鮫lト0弧\nMuれic重め納柵\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000U「:田A E・ma旺・・機\n\n動恥部脚0京劇; S駆れ偶coS\n\nCPFICNPJ: -・-\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000\u3000Nome/Razao S[貼aI: ・・--\n\ntN丁圏的霊園"A則O\n\nDE S囲IVleOS\n\n馴SC則棚NA$ao眼S駅VICOS\n\nⅥ鵬舶関りo S圃Ⅳl印墓場4章.雷的脚\n\n墳町筋岬P同軸膿軸-韓髄ぬく購)\n\nc〇㌔巾的軒鯵軸ais ・同地S (時)\n\n親臨00∞鴫的。き血。血岬調調は。.血糊馳帥復職陥。他種1ぬ\nV8厨丁億8ミ(鐙S晩鴫S (京$\n\n寄ase僻c細則ぬ(噂)\n\n叫00\n\n4書.32ふ1抑\n\nValα do置ミ遅く的\n\nC他説〇時請種da軸陣(韓靭\n\n2.劃i車軸I\n\n0.00\n\nM脚輯pめdeかきs略ゆdo鎚Ⅳi印\n\n軸t m輯〇億S調印く鴎e直隠\n\nV81e富句調達部劃わdos丁蹄競OS l鼠)競艇\n\nOU隔晩S i討Fo剛閲的鯵\n\n場ま葛購置,55\n\n(1 ) Esta NFSでfoi em舶a com leSpa調o na Lei no 14.097/2脚5; @) D純a de venc加ento do ISS desta NFSせ10/書1 I2026; @) Infoma串es pr鎚調騨das\n\nnes campas de PiS e COFINS sao鳩fe唆ntes cos vaIo記S toぬis sく心re a opl的確〇、;\n\nhttps:伽u軸ooIuive.債珊面uailhnboxnd仏AkAしgARAAAAHYQD EapmEc2b]小CqAC%2F馴喝OA[I4IMY5LGNkGVh3¶.xl oしugAJatIT53QAA/§X§AuA…\u30001 /1\n\n\x0c'

OCR = 'Código do Serviço\n03115 - (releitura dedicada)\nSP2RET_FEDERAIS: 0,00 619,89 1.239,78 268,62\nSP2RET_CSLL: 413,26\n\nNúmero da Nota\n00000228\nData e Hora de Emissão\n19/10/2026 14:45:05\nCódigo de Verificação\nVIBQ-C4WQ\nSP_COD_VERIF_ALTERNATIVO: VI8Q-C4WQ\n\n19/10/2026, 17:34 Email — Luiz Argolo — Outlook\n\nNúmero da Nota\n00000228\nData e Hora de Emissão\n19/10/2026 14:45:05\nCódigo de Verificação\nVIBQ-C4WQ\n\nPREFEITURA DO MUNICÍPIO DE SÃO PAULO\nSECRETARIA MUNICIPAL DA FAZENDA\n\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\n\n|\n20261019u11437087000185\n\nPRESTADOR DE SERVIÇOS\nCPF/CNPJ: 11.437.087/0001-85 Inscrição Municipal: 4.003.857-2\nA Nome/Razão Social: APROAR PLANEJAMENTO PATRIMONIAL LTDA\nAPROAR Endereço: AV REBOUCAS 3970, ANDAR 17 - PINHEIROS - CEP: 05402-918 |\nMunicípio: São Paulo UF: SP\n\n| TOMADOR DE SERVIÇOS\n\n| Nome/Razão Social: PATRICORP PATRIMONIAL LTDA. |\nCPF/CNPJ: 00.625.191/0001-87 Inscrição Municipal: ----\nEndereço: AVE TANCREDO NEVES, 1485 1485 - CAMINHO DAS ARVORES - CEP: 41820-020\n\nMunicípio: Salvador UF: BA E-mail: ----\n\n= |]|]]][]]]D]D[DD>>>>>—>—————————1——\n| INTERMEDIÁRIO DE SERVIÇOS\n\nCPF/CNPJ: ---- Nome/Razão Social: ----\n| DISCRIMINAÇÃO DE SERVIÇOS |\nServiços prestados.\n(=) Valor liquido: R$ 38.784,45\nPIS: R$ 268,62\nCofins: R$ 1.239,78\nCSLL: R$ 413,26\nIRRF: R$ 619,89\nVALOR TOTAL DO SERVIÇO = R$ 41.326,00\n\n| Contribuição Previdenciária - Retida (R$) PIS/PASEP (R$) | IPI(RS)\n\n| 0,00 268,62 -\nContribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n\n| 413,26 -\n\nRo\n\n| Código do Serviço |\n\n715 - Assessoria ou consultoria de qualquer natureza, não contida em outros itens desta lista.\n\n| Valor Total das Deduções (R$) Base de Cálculo (R$) Aliquota (3) Valor do ISS (R$) Crédito Programa da NFP (R$)\n| 0,00 41.326,00 5,00% 2.066,30 0,00\nValor Aproximado dos Tributos / Fonte 1\n\n| Município de Prestação do Serviço Número Inscrição da Obra\n| = R$ 2.541,55\n\n| &\n| OUTRAS INFORMAÇÕES\n| (1) Esta NFS-e foi emitida com respaldo na Lei nº 14.097/2005; (2) Data de vencimento do ISS desta NFS-e: 10/11/2026; (3) Informações preenchidas\n| nos campos de PIS e COFINS são referentes aos valores totais sobre a operação.;\n\n|\n\n|\n|\n|\n\nhttps://outiook.live.com/mailfinbox/id/AAkALgAAAAAAHY QDEapmEc2byACqAC %ZFEWg0AgaIMYSLGNKGVh3fLx1oLUgAJaATS3QAA/sxs/AAKA...\n'


def _parse(monkeypatch, camada, ocr_pag1, nome):
    dummy_path = f"tests/{nome}.pdf"
    os.makedirs("tests", exist_ok=True)
    with open(dummy_path, "wb") as f:
        f.write(b"%PDF-1.4")
    monkeypatch.setattr("src.extractors.pdf_extractor.extract_text", lambda path: camada)
    # Só a página 1 tem conteúdo (o "\x0c" final da camada gera uma 2ª
    # página vazia, que também passa pelo OCR por página).
    monkeypatch.setattr(SPPdfExtractor, "_ocr_page", lambda self, i: ocr_pag1 if i == 0 else "")
    try:
        ext = SPPdfExtractor(dummy_path)
        return ext, ext.parse_multiple()
    finally:
        if os.path.exists(dummy_path):
            os.remove(dummy_path)


# --- Portão de qualidade da camada de texto ---------------------------------

def test_camada_lixo_de_ocr_de_terceiros_e_ilegivel():
    # 1196+ caracteres, tem "CNPJ" (passa no portão global antigo), mas ~34%
    # dos caracteres não brancos são CJK.
    assert SPPdfExtractor._camada_texto_ilegivel(CAMADA)


def test_texto_latino_bom_nao_e_ilegivel():
    # O próprio texto do OCR (português com acentos, travessões e "R$") e um
    # texto digital típico não podem disparar o portão.
    assert not SPPdfExtractor._camada_texto_ilegivel(OCR)
    digital = ("PREFEITURA DO MUNICÍPIO DE SÃO PAULO\nNOTA FISCAL ELETRÔNICA DE SERVIÇOS - NFS-e\n"
               "Prestador: AÇÚCAR & CAFÉ LTDA – “Matriz” — Endereço: Av. Brigadeiro Faria Lima, nº 1.234, 2ª via\n"
               "Lei nº 12.741/2012 – tributos aproximados € 0,00 · R$ 1.234,56 (5,00%) ‘ok’ …\n") * 5
    assert not SPPdfExtractor._camada_texto_ilegivel(digital)


def test_texto_curto_nao_e_avaliado():
    assert not SPPdfExtractor._camada_texto_ilegivel("鰹" * 200)


# --- Nota completa ------------------------------------------------------------

def test_aproar_228_camada_lixo_vai_para_ocr_e_extrai_todos_os_campos(monkeypatch):
    ext, notas = _parse(monkeypatch, CAMADA, OCR, "dummy_sp2_aproar_228")
    assert len(notas) == 1
    assert ext.from_ocr is True
    n = notas[0]

    assert n.numero == "00000228"
    # Leitura 'por' do Tesseract (impresso "VI8Q-C4WQ"): a divergência B/8
    # com a leitura 'eng' vira aviso, sem trocar o valor (ver docstring).
    assert n.codigo_verificacao == "VIBQ-C4WQ"
    assert any("VIBQ-C4WQ" in a and "VI8Q-C4WQ" in a and "B/8" in a for a in n.avisos)
    assert n.data_emissao.strftime("%d/%m/%Y %H:%M:%S") == "19/10/2026 14:45:05"
    # Sem competência impressa: mês da emissão (convenção do SP escaneado),
    # nunca a data/hora do cabeçalho do navegador.
    assert n.competencia.strftime("%m/%Y") == "10/2026"
    assert n.servico_codigo == "03115"

    p = n.prestador
    assert p.cnpj_cpf == "11437087000185"
    assert p.inscricao_municipal == "40038572"
    assert p.razao_social == "APROAR PLANEJAMENTO PATRIMONIAL LTDA"
    assert p.endereco.logradouro == "AV REBOUCAS"
    assert p.endereco.numero == "3970"
    assert p.endereco.complemento == "ANDAR 17"
    assert p.endereco.bairro == "PINHEIROS"
    assert p.endereco.cep == "05402918"
    assert p.endereco.codigo_municipio == "3550308"
    assert p.endereco.uf == "SP"

    t = n.tomador
    assert t.cnpj_cpf == "00625191000187"
    assert t.razao_social.startswith("PATRICORP PATRIMONIAL LTDA")
    assert t.endereco.logradouro == "AVE TANCREDO NEVES"
    assert t.endereco.numero == "1485"
    assert t.endereco.complemento == "1485"
    assert t.endereco.bairro == "CAMINHO DAS ARVORES"
    assert t.endereco.cep == "41820020"
    assert t.endereco.codigo_municipio == "2927408"
    assert t.endereco.uf == "BA"
    assert n.intermediario is None

    v = n.valores
    assert v.valor_servicos == pytest.approx(41326.00)
    assert v.valor_deducoes == pytest.approx(0.0)
    assert v.base_calculo == pytest.approx(41326.00)
    assert v.aliquota == pytest.approx(0.05)
    assert v.valor_iss == pytest.approx(2066.30)
    assert v.iss_retido is False
    assert v.valor_inss == pytest.approx(0.0)
    assert v.valor_ir == pytest.approx(619.89)
    assert v.valor_cofins == pytest.approx(1239.78)
    assert v.valor_pis == pytest.approx(268.62)
    assert v.valor_csll == pytest.approx(413.26)
    # 41.326,00 - 619,89 - 1.239,78 - 268,62 - 413,26 = 38.784,45 (= o
    # "(=) Valor liquido" impresso na discriminação).
    assert v.valor_liquido_nfse == pytest.approx(38784.45)

    assert n.discriminacao.startswith("Serviços prestados.")
    assert "Valor liquido: R$ 38.784,45" in n.discriminacao
    assert "IRRF: R$ 619,89" in n.discriminacao
    # Cabeçalho/rodapé do navegador não vazam para campo nenhum.
    assert "Outlook" not in n.discriminacao and "outlook" not in n.discriminacao
    # Único aviso: a ambiguidade B/8 do código de verificação.
    assert len(n.avisos) == 1


def test_linha_de_retencoes_incompleta_nunca_e_distribuida_por_posicao(monkeypatch):
    # Sem os marcadores votados do recorte, só sobra a linha da página
    # inteira "| 0,00 268,62 -" (perdeu as colunas IRRF/COFINS): não pode
    # virar INSS=0,00/IRRF=268,62. Fica sentinela 0,00 + aviso, e a CSLL
    # (linha própria, legível) continua lida.
    sem_recorte = "\n".join(
        ln for ln in OCR.split("\n")
        if not ln.startswith(("SP2RET_", "SP_COD_VERIF_ALTERNATIVO")))
    _ext, notas = _parse(monkeypatch, CAMADA, sem_recorte, "dummy_sp2_aproar_228_sem_recorte")
    v = notas[0].valores
    assert v.valor_ir == 0.0 and v.valor_pis == 0.0 and v.valor_cofins == 0.0 and v.valor_inss == 0.0
    assert v.valor_csll == pytest.approx(413.26)
    avisos = notas[0].avisos
    assert any("Retenções federais ilegíveis" in a and "INSS/IRRF/COFINS/PIS" in a for a in avisos)
    # O líquido da discriminação denuncia a divergência.
    assert any("Valor líquido calculado" in a and "38.784,45" in a for a in avisos)


def test_retencoes_modelo_previdenciaria_com_borda_lida_como_barra():
    ext = SPPdfExtractor.__new__(SPPdfExtractor)
    ext.__init__("tests/inexistente.pdf")
    ext._sp_avisos = []
    ret = ext._sp2_retencoes_modelo_previdenciaria(
        "Contribuição Previdenciária - Retida (R$) IRRF (R$) COFINS (R$) PIS/PASEP (R$) IPI(R$)\n"
        "| 0,00 619,89 1.239,78 268,62 -\n"
        "Contribuições Sociais - Retidas (R$) Descrição Contribuições Sociais - Retidas\n"
        "| 413,26 -\n")
    assert ret == (0.0, 619.89, 1239.78, 268.62, 413.26)
    assert ext._sp_avisos == []
    # Modelo antigo (sem "Contribuição Previdenciária"): não se aplica.
    assert ext._sp2_retencoes_modelo_previdenciaria("IRRF (R$) CSLL (R$) COFINS (R$) PIS/PASEP (R$)\n1,00 2,00 3,00 4,00") is None


def test_discriminacao_so_e_trocada_quando_o_recorte_traz_mais_conteudo():
    base = ("DISCRIMINAÇÃO DE SERVIÇOS\n|serviços prestados. |\n|\n|\n"
            "VALOR TOTAL DO SERVIÇO = R$ 41.326,00\n")
    recut = "Serviços prestados.\n(=) Valor liquido: R$ 38.784,45\nPIS: R$ 268,62\né\n"
    novo = SPPdfExtractor._sp_substituir_discriminacao_pobre(base, recut)
    assert "Valor liquido: R$ 38.784,45" in novo
    assert "\né\n" not in novo
    assert novo.endswith("VALOR TOTAL DO SERVIÇO = R$ 41.326,00\n")

    rica = ("DISCRIMINAÇÃO DE SERVIÇOS\nIMC - PLANO ZAP+ (ZAP+VIVA+OLX) Valor Bruto 1803,45 referente a junho\n"
            "VALOR TOTAL DO SERVIÇO = R$ 1.803,45\n")
    assert SPPdfExtractor._sp_substituir_discriminacao_pobre(rica, "IMC - PLANO ZAP+") == rica
