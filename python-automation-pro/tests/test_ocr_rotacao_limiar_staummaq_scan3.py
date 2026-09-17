# -*- coding: utf-8 -*-
r"""Portão da busca de rotação do OCR (`_ocr_page`).

Achado real 2026-09-14, lote "STAUMMAQ - SCAN 3.pdf" (5 páginas). Pedido do
usuário: "verificar o motivo de não ter extraído as 5 notas do arquivo. Só
extraiu a primeira, ferimport".

CAUSA-RAIZ: as CINCO páginas do lote foram digitalizadas de cabeça para baixo.
`_ocr_page` já sabe corrigir isso — testa 180°/90°/270° e fica com a leitura de
melhor placar em `_score_ocr_text` —, mas a busca só rodava quando a leitura em
0° pontuava **exatamente zero**. Medido nas páginas reais deste lote:

    página   score 0°   score 180°   resultado
      1          0          51       busca rodou  -> nota extraída
      2          1          82       busca BLOQUEADA -> nota perdida
      3          0          17       busca rodou  (boletim de medição)
      4          1          84       busca BLOQUEADA -> nota perdida
      5          0          18       busca rodou  (boletim de medição)

Ou seja: UM acerto acidental de palavra-chave no texto invertido (score 1)
bastava para travar a correção de orientação. As duas NFS-e presas na
orientação errada caíam em `LAYOUT_GENERICO`, e `parse_multiple` descarta essas
páginas ("Layout não reconhecido") — o lote inteiro saía com 1 nota em vez de 3.

CORREÇÃO: o portão virou um LIMIAR (`_OCR_ROTACAO_LIMIAR`), e a aceitação de
uma rotação ganhou uma MARGEM de 3x. A margem existe para o caso simétrico, já
documentado no fallback de PSM 6: uma rotação ERRADA também pode pontuar > 0
por coincidência (nota 160/GUARAJUBA SHOPPING), e sem margem ela substituiria
uma leitura 0° mediana porém correta.

Os testes abaixo controlam o Tesseract: `image_to_string` é substituído por uma
função que devolve um texto por chamada, na ordem em que `_ocr_page` testa as
orientações (0°, 180°, 90°, 270°). Assim o portão é exercitado sem depender de
OCR real, que seria lento e não determinístico na suíte.
"""
import pytest

from src.extractors.pdf_extractor import SPPdfExtractor

# Pontua 1: uma única palavra-chave ("CEP"), nenhum valor em formato de moeda.
# É a assinatura do texto invertido das páginas 2 e 4 do lote real.
TEXTO_INVERTIDO_SCORE_1 = "oBsseJduu] pjeq CEP 9Z0Z/L0/VZ aa no SaIdOdvAITI"

# Pontua alto: várias palavras-chave + valor em moeda (2 pontos).
TEXTO_CERTO_SCORE_ALTO = (
    "PREFEITURA MUNICIPAL DE CAMACARI\n"
    "NOTA FISCAL DE SERVICOS ELETRONICA\n"
    "PRESTADOR DE SERVICOS  CNPJ  CEP  MUNICIPIO\n"
    "TOMADOR DE SERVICOS  VALOR  DISCRIMINACAO  EMISSAO\n"
    "1.466,98\n"
)


def _ocr_page_controlado(monkeypatch, tmp_path, textos):
    """Roda `_ocr_page(0)` devolvendo `textos[i]` na i-ésima chamada ao
    Tesseract feita pela BUSCA DE ROTAÇÃO — as orientações são testadas na
    ordem 0°, 180°, 90°, 270°.

    `_ocr_page` faz outras chamadas ao Tesseract no mesmo fluxo (o fallback de
    `--psm 6` e o recorte dedicado do cabeçalho de Salvador), e todas elas
    passam `config=`, enquanto a busca de rotação usa só `lang='por'`. É por
    isso que o filtro abaixo é por `config`: sem ele essas chamadas consumiriam
    a sequência e a contagem não teria relação com o que o teste afirma.
    Devolvem "" (placar 0), então nunca substituem a leitura escolhida."""
    import pymupdf
    import pytesseract

    caminho = tmp_path / "pagina.pdf"
    doc = pymupdf.open()
    doc.new_page()
    doc.save(str(caminho))
    doc.close()

    chamadas = {"n": 0}

    def _falso(img, *args, **kwargs):
        if kwargs.get("config"):
            return ""
        i = chamadas["n"]
        chamadas["n"] += 1
        return textos[i] if i < len(textos) else ""

    monkeypatch.setattr(pytesseract, "image_to_string", _falso)
    texto = SPPdfExtractor(str(caminho))._ocr_page(0)
    return texto, chamadas["n"]


def test_score_do_texto_invertido_e_do_texto_certo():
    """Ancora os placares que sustentam o resto do arquivo — se
    `_score_ocr_text` mudar, estes números avisam."""
    assert SPPdfExtractor._score_ocr_text(TEXTO_INVERTIDO_SCORE_1) == 1
    assert SPPdfExtractor._score_ocr_text(TEXTO_CERTO_SCORE_ALTO) >= 10


def test_um_acerto_acidental_nao_bloqueia_mais_a_busca_de_rotacao(monkeypatch, tmp_path):
    """O defeito exato das páginas 2 e 4: 0° pontuava 1, e a busca nem rodava."""
    texto, _ = _ocr_page_controlado(
        monkeypatch, tmp_path, [TEXTO_INVERTIDO_SCORE_1, TEXTO_CERTO_SCORE_ALTO])
    assert texto == TEXTO_CERTO_SCORE_ALTO


def test_leitura_boa_em_0_nao_dispara_rotacao(monkeypatch, tmp_path):
    """Acima do limiar não se gasta passada extra de OCR: a leitura de 0° é
    aceita e o Tesseract é chamado UMA vez só."""
    texto, n_chamadas = _ocr_page_controlado(
        monkeypatch, tmp_path, [TEXTO_CERTO_SCORE_ALTO, "lixo", "lixo", "lixo"])
    assert texto == TEXTO_CERTO_SCORE_ALTO
    assert n_chamadas == 1


def test_rotacao_coincidente_nao_rouba_leitura_mediana(monkeypatch, tmp_path):
    """A margem de 3x: uma orientação errada que pontua um pouco acima NÃO pode
    substituir a leitura de 0°. Aqui 0° pontua 4 e a rotação pontua 6 — passa
    do 'maior', mas não da margem."""
    zero = "CNPJ CEP VALOR MUNICIPIO"          # 4 palavras-chave -> score 4
    rot = "CNPJ CEP VALOR MUNICIPIO NOTA CPF"  # score 6
    assert SPPdfExtractor._score_ocr_text(zero) == 4
    assert SPPdfExtractor._score_ocr_text(rot) == 6
    texto, _ = _ocr_page_controlado(monkeypatch, tmp_path, [zero, rot, rot, rot])
    assert texto == zero


def test_rotacao_com_margem_folgada_vence(monkeypatch, tmp_path):
    """O caso real: 1 contra 82 passa com folga na margem de 3x."""
    zero = TEXTO_INVERTIDO_SCORE_1
    rot = TEXTO_CERTO_SCORE_ALTO
    assert SPPdfExtractor._score_ocr_text(rot) > SPPdfExtractor._score_ocr_text(zero) * 3
    texto, _ = _ocr_page_controlado(monkeypatch, tmp_path, [zero, rot])
    assert texto == rot


def test_comportamento_com_score_zero_permanece_identico(monkeypatch, tmp_path):
    """Regressão das notas 160/201: quando 0° pontua ZERO, a margem é inócua
    (`0 * 3 == 0`) e qualquer rotação que pontue > 0 é aceita, como antes."""
    zero = "qwrty zxcvb plmnk hjgfd"  # nenhum termo fiscal: placar 0
    rot = "NOTA FISCAL PRESTADOR"  # score baixo (3), mas > 0
    assert SPPdfExtractor._score_ocr_text(zero) == 0
    assert 0 < SPPdfExtractor._score_ocr_text(rot) < 10
    texto, _ = _ocr_page_controlado(monkeypatch, tmp_path, [zero, rot])
    assert texto == rot


def test_busca_para_assim_que_encontra_leitura_boa(monkeypatch, tmp_path):
    """Achando uma orientação acima do limiar, não se testa 90° nem 270°."""
    _, n_chamadas = _ocr_page_controlado(
        monkeypatch, tmp_path, [TEXTO_INVERTIDO_SCORE_1, TEXTO_CERTO_SCORE_ALTO, "lixo", "lixo"])
    assert n_chamadas == 2


def test_limiar_documentado_no_codigo():
    """O limiar mora no vão entre o placar de uma leitura invertida (0 ou 1) e
    o de uma nota lida na orientação certa (17 a 84 no lote real)."""
    assert SPPdfExtractor._OCR_ROTACAO_LIMIAR > 1
    assert SPPdfExtractor._OCR_ROTACAO_LIMIAR <= 17
