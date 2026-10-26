import re
import unicodedata
import xml.etree.ElementTree as ET
from typing import Optional

from ..models.cte_os_model import CteOS, EntidadeCte

NS_CTE = 'http://www.portalfiscal.inf.br/cte'
VERSAO_LEIAUTE = '4.00'
VERSAO_MODAL = '4.00'

# Valores que o DACTE OS NÃO imprime mas o leiaute 4.00 exige - sentinelas
# DOCUMENTADAS (ver DOCUMENTACAO_CONVERSAO.md, seção do DACTE OS), nunca um
# dado fiscal inventado:
# - `ide/verProc` (versão do aplicativo EMISSOR do contribuinte) e
#   `protCTe/infProt/verAplic` (versão do aplicativo da SEFAZ que autorizou):
#   nenhum dos dois aparece no documento impresso.
SENTINELA_VERSAO = 'NAO INFORMADO'
# - Chave de acesso ilegível: o `Id` do `infCte` e o `chCTe` do protocolo
#   são obrigatórios e casam com um padrão fixo de 44 dígitos - zeros
#   (o extrator já registra o aviso "Chave de acesso não encontrada").
SENTINELA_CHAVE = '0' * 44
# - `emit/IE` obrigatória (TIe = 2 a 14 dígitos) quando a IE não foi lida.
SENTINELA_IE = '00'
# - `xBairro`/`xLgr` obrigatórios (TString, mínimo 1 caractere).
SENTINELA_TEXTO = 'NAO INFORMADO'

_TRADUCAO_TSTRING = str.maketrans({
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '–': '-', '—': '-', '•': '-', ' ': ' ',
})


def _txt(valor: Optional[str], max_len: int) -> str:
    """Normaliza um texto para o tipo `TString` do leiaute (só caracteres de
    `!` a `ÿ`, sem espaço no início/fim, sem espaços duplicados) e corta no
    tamanho máximo do campo. Aspas/travessões tipográficos que o OCR produz
    viram os equivalentes ASCII; qualquer outro caractere fora do Latin-1 é
    decomposto (NFKD) e descartado se não tiver equivalente."""
    s = (valor or '').translate(_TRADUCAO_TSTRING)
    saida = []
    for ch in s:
        if ' ' <= ch <= 'ÿ':
            saida.append(ch)
        elif ch in '\t\r\n':
            saida.append(' ')
        else:
            base = unicodedata.normalize('NFKD', ch)
            saida.append(''.join(c for c in base if ' ' <= c <= 'ÿ'))
    s = re.sub(r'\s+', ' ', ''.join(saida)).strip()
    return s[:max_len].strip()


def _digits(valor) -> str:
    return ''.join(ch for ch in (valor or '') if ch.isdigit())


def _dec(valor: float, casas: int = 2) -> str:
    """Formato dos tipos `TDec_1302`/`TDec_0302`/`TDec_1104` (ponto decimal,
    sem separador de milhar, casas fixas)."""
    return f"{max(valor or 0.0, 0.0):.{casas}f}"


def _dh(dt) -> str:
    """`TDateTimeUTC` (AAAA-MM-DDThh:mm:ssTZD). Todos os DACTE OS vistos são
    da BA, sem horário de verão desde 2019 - fuso -03:00."""
    return dt.strftime('%Y-%m-%dT%H:%M:%S') + '-03:00'


def grupo_icms(cst: Optional[str]) -> str:
    """Grupo oficial de `imp/ICMS` para um CST (leiaute 4.00, `TImpOS`)."""
    if cst == '00':
        return 'ICMS00'
    if cst == '20':
        return 'ICMS20'
    if cst in ('40', '41', '51'):
        return 'ICMS45'
    if cst == 'SN':
        return 'ICMSSN'
    return 'ICMS90'


class CteTransformer:
    """
    Transformador para CT-e OS (Conhecimento de Transporte Eletrônico para
    Outros Serviços) - Modelo 67, DACTE OS - REAL, extraído de um documento
    genuíno (`CteOS`, ver LAYOUT_DACTE_OS). Emite o XML no LEIAUTE OFICIAL
    4.00 do Modelo 67 (pacote de schemas `PL_CTe_400`, arquivos
    `procCTeOS_v4.00.xsd`/`cteOS_v4.00.xsd`/`cteTiposBasico_v4.00.xsd`/
    `cteModalRodoviarioOS_v4.00.xsd`, Portal Nacional do CT-e
    https://www.cte.fazenda.gov.br/portal/ - "Esquemas XML"):

    - raiz `cteOSProc` (`CTeOS` + `protCTe`) quando o documento impresso traz
      o protocolo de autorização; só `CTeOS` quando não traz (o `cteOSProc`
      oficial exige o `protCTe`);
    - `infCte` na ordem do `TCTeOS`: `ide`, `compl`, `emit`, `toma`,
      `vPrest`, `imp`, `infCTeNorm` (`infServico`/`infQ`, `infModal`/`rodoOS`);
    - ICMS no grupo do CST (`ICMS00`/`ICMS20`/`ICMS45`/`ICMS90`/`ICMSSN`),
      tributos federais retidos em `imp/infTribFed`;
    - campos derivados da chave de acesso (cUF, cCT, tpEmis, cDV) - a chave é
      conferida por DV mod-11 no extrator.

    Antes (até a v. com `cteProc`/`CTe`) a saída era um XML "inspirado" no
    Modelo 57: raiz errada, `tpServico` textual, grupo inventado
    `<retencoes>`, ICMS sempre `ICMS00`, `nProt` dentro de `ide`, municípios
    vazios - o Domínio (rotina "CT-e e CT-eOS > Arquivo XML") não reconhecia
    nenhuma linha.

    Limitação conhecida: sem `ds:Signature` (o documento original foi
    assinado pelo emitente; não temos o certificado dele) - é o único
    elemento obrigatório do XSD que fica de fora.
    """

    def _q(self, nome: str) -> str:
        return f'{{{NS_CTE}}}{nome}'

    def _sub(self, pai, nome: str, texto: Optional[str] = None, **attrs):
        el = ET.SubElement(pai, self._q(nome), **attrs)
        if texto is not None:
            el.text = texto
        return el

    @staticmethod
    def _ind_ie_toma(ie: Optional[str]) -> str:
        if ie and ie.strip().upper() == 'ISENTO':
            return '2'
        if _digits(ie):
            return '1'
        return '9'

    @staticmethod
    def _tp_cte(tipo: str) -> str:
        t = (tipo or '').strip().lower()
        if t.startswith('compl'):
            return '1'
        if t.startswith('substitu'):
            return '3'
        return '0'

    def _endereco(self, pai, tag: str, ent: EntidadeCte, max_lgr: int, com_fone: bool):
        end = ent.endereco
        el = self._sub(pai, tag)
        self._sub(el, 'xLgr', _txt(end.logradouro, max_lgr) or SENTINELA_TEXTO)
        self._sub(el, 'nro', _txt(end.numero, 60) or 'S/N')
        if _txt(end.complemento, 60):
            self._sub(el, 'xCpl', _txt(end.complemento, 60))
        self._sub(el, 'xBairro', _txt(end.bairro, 60) or SENTINELA_TEXTO)
        cmun = _digits(end.codigo_municipio)
        self._sub(el, 'cMun', cmun if len(cmun) == 7 else '0000000')
        self._sub(el, 'xMun', _txt(end.municipio, 60) or SENTINELA_TEXTO)
        cep = _digits(end.cep)
        if len(cep) == 8 and cep != '00000000':
            self._sub(el, 'CEP', cep)
        self._sub(el, 'UF', (end.uf or '').strip().upper())
        fone = _digits(ent.telefone)
        if com_fone and 6 <= len(fone) <= 14:
            self._sub(el, 'fone', fone)
        return el

    def _icms(self, imp_el, cte: CteOS):
        imp = cte.imposto
        cst = imp.cst_icms or imp.cst_derivado()
        grupo = grupo_icms(cst)
        icms = self._sub(imp_el, 'ICMS')
        g = self._sub(icms, grupo)
        if grupo == 'ICMSSN':
            self._sub(g, 'CST', '90')
            self._sub(g, 'indSN', '1')
            return
        self._sub(g, 'CST', cst if grupo != 'ICMS90' else '90')
        if grupo == 'ICMS45':
            return
        if grupo == 'ICMS20' or (grupo == 'ICMS90' and imp.percentual_reducao_bc > 0):
            self._sub(g, 'pRedBC', _dec(imp.percentual_reducao_bc))
        self._sub(g, 'vBC', _dec(imp.base_calculo_icms))
        self._sub(g, 'pICMS', _dec(imp.aliquota_icms))
        self._sub(g, 'vICMS', _dec(imp.valor_icms))

    def _modal_rodoviario(self, norm, cte: CteOS):
        m = cte.modal_rodoviario
        if m is None:
            return
        taf = _digits(m.termo_autorizacao_fretamento)
        reg = _digits(m.registro_estadual)
        if len(taf) != 12 and len(reg) != 25:
            # `rodoOS` exige TAF (12) OU NroRegEstadual (25) - sem nenhum dos
            # dois legível, o grupo não é emitido (o extrator já avisou).
            return
        inf_modal = self._sub(norm, 'infModal', versaoModal=VERSAO_MODAL)
        rodo = self._sub(inf_modal, 'rodoOS')
        if len(taf) == 12:
            self._sub(rodo, 'TAF', taf)
        else:
            self._sub(rodo, 'NroRegEstadual', reg)
        placa = (m.placa_veiculo or '').strip().upper()
        if re.fullmatch(r'[A-Z]{2,3}[0-9]{4}|[A-Z]{3,4}[0-9]{3}|[A-Z0-9]{7}', placa):
            veic = self._sub(rodo, 'veic')
            self._sub(veic, 'placa', placa)
            renavam = (m.renavam or '').strip()
            if 9 <= len(renavam) <= 11:
                self._sub(veic, 'RENAVAM', renavam)
            if m.uf_licenciamento:
                self._sub(veic, 'UF', m.uf_licenciamento.strip().upper())

    def transform(self, cte: CteOS) -> str:
        ET.register_namespace('', NS_CTE)

        chave = cte.chave_acesso if re.fullmatch(r'\d{44}', cte.chave_acesso or '') else SENTINELA_CHAVE
        emit_end = cte.emitente.endereco

        cte_os = ET.Element(self._q('CTeOS'), versao=VERSAO_LEIAUTE)
        inf = self._sub(cte_os, 'infCte', versao=VERSAO_LEIAUTE, Id=f"CTe{chave}")

        # ---------------------------------------------------------------- ide
        ide = self._sub(inf, 'ide')
        self._sub(ide, 'cUF', chave[0:2] if chave != SENTINELA_CHAVE else (_digits(emit_end.codigo_municipio)[:2] or '29'))
        self._sub(ide, 'cCT', chave[35:43])
        self._sub(ide, 'CFOP', _digits(cte.cfop)[:4])
        self._sub(ide, 'natOp', _txt(cte.natureza_operacao, 60) or SENTINELA_TEXTO)
        self._sub(ide, 'mod', '67')
        self._sub(ide, 'serie', str(int(_digits(cte.serie) or '0')))
        self._sub(ide, 'nCT', str(int(_digits(cte.numero) or '0')))
        self._sub(ide, 'dhEmi', _dh(cte.data_emissao))
        # 1 = Retrato: todos os DACTE OS vistos são impressos em retrato.
        self._sub(ide, 'tpImp', '1')
        self._sub(ide, 'tpEmis', chave[34] if chave != SENTINELA_CHAVE else '1')
        self._sub(ide, 'cDV', chave[43])
        # 1 = Produção: o documento traz protocolo de autorização de uso
        # (DACTE de homologação sai com "SEM VALOR FISCAL").
        self._sub(ide, 'tpAmb', '1')
        self._sub(ide, 'tpCTe', self._tp_cte(cte.tipo_cte))
        self._sub(ide, 'procEmi', '0')
        self._sub(ide, 'verProc', SENTINELA_VERSAO)
        # Município de envio = município do emitente (de onde o CT-e é
        # transmitido) - não impresso no DACTE OS.
        cmun_emit = _digits(emit_end.codigo_municipio)
        self._sub(ide, 'cMunEnv', cmun_emit if len(cmun_emit) == 7 else '0000000')
        self._sub(ide, 'xMunEnv', _txt(emit_end.municipio, 60) or SENTINELA_TEXTO)
        self._sub(ide, 'UFEnv', (emit_end.uf or '').strip().upper())
        self._sub(ide, 'modal', cte.modal or '01')
        self._sub(ide, 'tpServ', cte.tipo_servico_codigo or '6')
        self._sub(ide, 'indIEToma', self._ind_ie_toma(cte.tomador.inscricao_estadual))
        for cod, nome, uf, sufixo in (
                (cte.codigo_municipio_inicio, cte.municipio_inicio_prestacao, cte.uf_inicio_prestacao, 'Ini'),
                (cte.codigo_municipio_fim, cte.municipio_fim_prestacao, cte.uf_fim_prestacao, 'Fim')):
            if re.fullmatch(r'\d{7}', cod or ''):
                self._sub(ide, f'cMun{sufixo}', cod)
            if _txt(nome, 60):
                self._sub(ide, f'xMun{sufixo}', _txt(nome, 60))
            if uf:
                self._sub(ide, f'UF{sufixo}', uf.strip().upper())

        # -------------------------------------------------------------- compl
        # `cte.observacoes` já inclui a linha "NUMERO DO PEDIDO: ..." (faz
        # parte do mesmo bloco impresso) - `numero_pedido` não é reconcatenado.
        if _txt(cte.observacoes, 2000):
            compl = self._sub(inf, 'compl')
            self._sub(compl, 'xObs', _txt(cte.observacoes, 2000))

        # --------------------------------------------------------------- emit
        emit = self._sub(inf, 'emit')
        self._sub(emit, 'CNPJ', _digits(cte.emitente.cnpj_cpf).zfill(14)[:14])
        ie_emit = _digits(cte.emitente.inscricao_estadual)
        self._sub(emit, 'IE', ie_emit[:14] if len(ie_emit) >= 2 else SENTINELA_IE)
        self._sub(emit, 'xNome', _txt(cte.emitente.razao_social, 60) or SENTINELA_TEXTO)
        self._endereco(emit, 'enderEmit', cte.emitente, max_lgr=60, com_fone=True)
        self._sub(emit, 'CRT', cte.crt or '3')

        # --------------------------------------------------------------- toma
        toma = self._sub(inf, 'toma')
        doc_toma = _digits(cte.tomador.cnpj_cpf)
        if len(doc_toma) == 11:
            self._sub(toma, 'CPF', doc_toma)
        else:
            self._sub(toma, 'CNPJ', doc_toma.zfill(14)[:14])
        ie_toma = (cte.tomador.inscricao_estadual or '').strip()
        if ie_toma.upper() == 'ISENTO':
            self._sub(toma, 'IE', 'ISENTO')
        elif _digits(ie_toma):
            self._sub(toma, 'IE', _digits(ie_toma)[:14])
        self._sub(toma, 'xNome', _txt(cte.tomador.razao_social, 60) or SENTINELA_TEXTO)
        fone_toma = _digits(cte.tomador.telefone)
        if 6 <= len(fone_toma) <= 14:
            self._sub(toma, 'fone', fone_toma)
        self._endereco(toma, 'enderToma', cte.tomador, max_lgr=255, com_fone=False)
        email = (cte.tomador.email or '').strip()
        if re.fullmatch(r'[^@\s]+@[^.@\s]+\..+', email) and len(email) <= 60:
            self._sub(toma, 'email', email)

        # ------------------------------------------------------------- vPrest
        vprest = self._sub(inf, 'vPrest')
        self._sub(vprest, 'vTPrest', _dec(cte.valor_total_prestacao))
        self._sub(vprest, 'vRec', _dec(cte.valor_a_receber))

        # ---------------------------------------------------------------- imp
        imp_el = self._sub(inf, 'imp')
        self._icms(imp_el, cte)
        # Tributos federais retidos (impressos na grade "INFORMAÇÕES
        # RELATIVAS AO IMPOSTO") - grupo oficial `infTribFed`. Os 5 são
        # impressos (inclusive os 0,00), então os 5 são emitidos.
        trib = self._sub(imp_el, 'infTribFed')
        self._sub(trib, 'vPIS', _dec(cte.imposto.valor_pis))
        self._sub(trib, 'vCOFINS', _dec(cte.imposto.valor_cofins))
        self._sub(trib, 'vIR', _dec(cte.imposto.valor_ir))
        self._sub(trib, 'vINSS', _dec(cte.imposto.valor_inss))
        self._sub(trib, 'vCSLL', _dec(cte.imposto.valor_csll))

        # --------------------------------------------------------- infCTeNorm
        norm = self._sub(inf, 'infCTeNorm')
        serv = self._sub(norm, 'infServico')
        self._sub(serv, 'xDescServ', _txt(cte.descricao_servico, 30) or SENTINELA_TEXTO)
        if cte.quantidade_servico and cte.quantidade_servico > 0:
            inf_q = self._sub(serv, 'infQ')
            self._sub(inf_q, 'qCarga', _dec(cte.quantidade_servico, 4))
        self._modal_rodoviario(norm, cte)

        if not cte.protocolo_autorizacao:
            raiz = cte_os
        else:
            raiz = ET.Element(self._q('cteOSProc'), versao=VERSAO_LEIAUTE)
            raiz.append(cte_os)
            prot = self._sub(raiz, 'protCTe', versao=VERSAO_LEIAUTE)
            inf_prot = self._sub(prot, 'infProt')
            self._sub(inf_prot, 'tpAmb', '1')
            self._sub(inf_prot, 'verAplic', SENTINELA_VERSAO)
            self._sub(inf_prot, 'chCTe', chave)
            self._sub(inf_prot, 'dhRecbto', _dh(cte.protocolo_data_hora or cte.data_emissao))
            self._sub(inf_prot, 'nProt', _digits(cte.protocolo_autorizacao))
            self._sub(inf_prot, 'cStat', '100')
            self._sub(inf_prot, 'xMotivo', 'Autorizado o uso do CT-e')

        ET.indent(raiz, space='  ')
        return ET.tostring(raiz, encoding='utf-8', xml_declaration=True).decode('utf-8')
