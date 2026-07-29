# -*- coding: utf-8 -*-
"""Cobre a seleção de páginas alternadas (ex.: 1, 3 e 6) de um PDF de várias
páginas: o parser de especificação da CLI (`parse_page_spec`) e o filtro por
página do `run_conversion` (`selected_pages`)."""
import os
import re
import glob
import pytest

import src.main as main
from src.main import parse_page_spec, run_conversion
from src.models.nfse_models import Nfse, Entidade, Endereco, Valores
from datetime import datetime


# ----------------------------- parse_page_spec -----------------------------

@pytest.mark.parametrize("spec, esperado", [
    ("1,3,6", [1, 3, 6]),
    ("1-3,6", [1, 2, 3, 6]),
    ("6-1", [1, 2, 3, 4, 5, 6]),      # intervalo invertido é normalizado
    (" 1 , 3 ,6 ", [1, 3, 6]),         # espaços tolerados
    ("2", [2]),
    ("1,1,2", [1, 2]),                 # duplicatas colapsadas e ordenadas
    ("", []),
    ("   ", []),
])
def test_parse_page_spec_validos(spec, esperado):
    assert parse_page_spec(spec) == esperado


@pytest.mark.parametrize("spec", ["0", "1,abc", "-2", "3-0", "0-2"])
def test_parse_page_spec_invalidos(spec):
    with pytest.raises(ValueError):
        parse_page_spec(spec)


# --------------------------- filtro selected_pages ---------------------------

def _mk_nfse(numero: str, pagina: int) -> Nfse:
    """Nfse mínima válida, marcada com a página de origem."""
    ent = Entidade(
        cnpj_cpf="00000000000191",
        razao_social=f"EMPRESA {numero}",
        endereco=Endereco(
            logradouro="RUA X", numero="1", bairro="CENTRO",
            codigo_municipio="2927408", uf="BA", cep="40000000",
        ),
    )
    n = Nfse(
        numero=numero,
        codigo_verificacao="XXXX-XXXX",
        data_emissao=datetime(2026, 4, 14),
        competencia=datetime(2026, 4, 1),
        prestador=ent, tomador=ent,
        discriminacao="Serviço",
        servico_codigo="0101",
        valores=Valores(valor_servicos=100.0, base_calculo=100.0, aliquota=0.0, valor_liquido_nfse=100.0),
    )
    n.pagina_origem = pagina
    return n


def _paginas_geradas(out_dir: str) -> list:
    """Lê os XMLs gerados e devolve as páginas de origem, pelo sufixo _Pagina_N_."""
    pags = []
    for f in glob.glob(os.path.join(out_dir, "*.xml")):
        m = re.search(r"_Pagina_(\d+)_", os.path.basename(f))
        if m:
            pags.append(int(m.group(1)))
    return sorted(pags)


@pytest.fixture
def _fake_pipeline(monkeypatch):
    """PDF de 4 páginas (1, 2, 3, 6) sem tocar em disco de entrada nem OCR."""
    notas = [_mk_nfse("0001", 1), _mk_nfse("0002", 2), _mk_nfse("0003", 3), _mk_nfse("0006", 6)]
    monkeypatch.setattr(main.SPPdfExtractor, "parse_multiple", lambda self: notas)
    # Isola o teste da lógica do transformer — só precisamos saber quais notas viram arquivo.
    monkeypatch.setattr(main.Abrasf201Transformer, "transform", lambda self, nfse: f"<nfse numero='{nfse.numero}'/>")
    return notas


def test_run_conversion_paginas_alternadas(tmp_path, _fake_pipeline):
    out = os.path.join(str(tmp_path), "saida.xml")
    run_conversion("dummy.pdf", out, selected_pages=[1, 3, 6])
    # Só as páginas 1, 3 e 6 devem gerar XML — a 2 fica de fora.
    assert _paginas_geradas(str(tmp_path)) == [1, 3, 6]


def test_run_conversion_sem_selecao_gera_todas(tmp_path, _fake_pipeline):
    out = os.path.join(str(tmp_path), "saida.xml")
    run_conversion("dummy.pdf", out, selected_pages=None)
    assert _paginas_geradas(str(tmp_path)) == [1, 2, 3, 6]


def test_run_conversion_selecao_sem_correspondencia(tmp_path, _fake_pipeline):
    out = os.path.join(str(tmp_path), "saida.xml")
    with pytest.raises(ValueError):
        run_conversion("dummy.pdf", out, selected_pages=[99])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
