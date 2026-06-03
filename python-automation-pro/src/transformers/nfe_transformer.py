import xml.etree.ElementTree as ET
from datetime import datetime
from ..models.nfse_models import Nfse
import random

NS_NFE = 'http://www.portalfiscal.inf.br/nfe'

class NfeTransformer:
    """
    Transformador para gerar XML no padrão NF-e (Modelo 55 - DANFE Estadual).
    Utilizado como workaround para importação em sistemas contábeis que 
    possuem suporte limitado a layouts de NFS-e mas aceitam NF-e padrão.
    """
    
    @staticmethod
    def _digits(value: str) -> str:
        return ''.join(ch for ch in (value or '') if ch.isdigit())

    def _generate_fake_key(self, nfse: Nfse, cuf: str) -> str:
        """Gera uma chave de acesso NF-e fake de 44 dígitos."""
        cnpj = self._digits(nfse.prestador.cnpj_cpf).zfill(14)
        aamm = nfse.data_emissao.strftime('%y%m')
        mod = '55'
        serie = '001'
        nnf = nfse.numero.zfill(9)
        tp_emis = '1'
        cnf = str(random.randint(10000000, 99999999))
        
        parcial = f"{cuf}{aamm}{cnpj}{mod}{serie}{nnf}{tp_emis}{cnf}"
        
        # Cálculo do dígito verificador (Módulo 11)
        soma = 0
        peso = 2
        for char in reversed(parcial):
            soma += int(char) * peso
            peso = 2 if peso == 9 else peso + 1
        dv = 11 - (soma % 11)
        if dv >= 10: dv = 0
        
        return f"{parcial}{dv}"

    def transform(self, nfse: Nfse) -> str:
        # Registra namespace
        ET.register_namespace('', NS_NFE)
        
        cuf = nfse.prestador.endereco.codigo_municipio[:2] if nfse.prestador.endereco.codigo_municipio else "35"
        chave = self._generate_fake_key(nfse, cuf)
        
        # Root: nfeProc
        nfe_proc = ET.Element('nfeProc', xmlns=NS_NFE, versao="4.00")
        
        # NFe
        nfe = ET.SubElement(nfe_proc, 'NFe', xmlns=NS_NFE)
        
        # infNFe
        inf_nfe = ET.SubElement(nfe, 'infNFe', Id=f"NFe{chave}", versao="4.00")
        
        # ide
        ide = ET.SubElement(inf_nfe, 'ide')
        ET.SubElement(ide, 'cUF').text = cuf
        ET.SubElement(ide, 'cNF').text = chave[35:43]
        ET.SubElement(ide, 'natOp').text = "PRESTACAO DE SERVICO"
        ET.SubElement(ide, 'mod').text = "55"
        ET.SubElement(ide, 'serie').text = "1"
        ET.SubElement(ide, 'nNF').text = nfse.numero[-9:].lstrip('0') or '1'
        ET.SubElement(ide, 'dhEmi').text = nfse.data_emissao.strftime('%Y-%m-%dT%H:%M:%S-03:00')
        ET.SubElement(ide, 'tpNF').text = "1"
        ET.SubElement(ide, 'idDest').text = "1"
        ET.SubElement(ide, 'cMunFG').text = nfse.prestador.endereco.codigo_municipio or "3550308"
        ET.SubElement(ide, 'tpImp').text = "1"
        ET.SubElement(ide, 'tpEmis').text = "1"
        ET.SubElement(ide, 'cDV').text = chave[43]
        ET.SubElement(ide, 'tpAmb').text = "1"
        ET.SubElement(ide, 'finNFe').text = "1"
        ET.SubElement(ide, 'indFinal').text = "1"
        ET.SubElement(ide, 'indPres').text = "1"
        ET.SubElement(ide, 'procEmi').text = "0"
        ET.SubElement(ide, 'verProc').text = "Antigravity_v1"
        
        # emit
        emit = ET.SubElement(inf_nfe, 'emit')
        ET.SubElement(emit, 'CNPJ').text = self._digits(nfse.prestador.cnpj_cpf)
        ET.SubElement(emit, 'xNome').text = (nfse.prestador.razao_social[:60] or "PRESTADOR NAO IDENTIFICADO")
        
        ender_emit = ET.SubElement(emit, 'enderEmit')
        ET.SubElement(ender_emit, 'xLgr').text = nfse.prestador.endereco.logradouro[:60] or "RUA NAO INFORMADA"
        ET.SubElement(ender_emit, 'nro').text = nfse.prestador.endereco.numero or "S/N"
        ET.SubElement(ender_emit, 'xBairro').text = nfse.prestador.endereco.bairro[:60] or "BAIRRO"
        ET.SubElement(ender_emit, 'cMun').text = nfse.prestador.endereco.codigo_municipio or "3550308"
        ET.SubElement(ender_emit, 'xMun').text = "MUNICIPIO"
        ET.SubElement(ender_emit, 'UF').text = nfse.prestador.endereco.uf or "SP"
        ET.SubElement(ender_emit, 'CEP').text = self._digits(nfse.prestador.endereco.cep) or "00000000"
        if nfse.prestador.telefone:
            ET.SubElement(ender_emit, 'fone').text = self._digits(nfse.prestador.telefone)[:14]
        
        ET.SubElement(emit, 'IE').text = "ISENTO"
        ET.SubElement(emit, 'CRT').text = "1"
        
        # dest
        dest = ET.SubElement(inf_nfe, 'dest')
        doc_dest = self._digits(nfse.tomador.cnpj_cpf)
        if len(doc_dest) == 14:
            ET.SubElement(dest, 'CNPJ').text = doc_dest
        else:
            ET.SubElement(dest, 'CPF').text = doc_dest.zfill(11)
            
        ET.SubElement(dest, 'xNome').text = (nfse.tomador.razao_social[:60] or "TOMADOR NAO IDENTIFICADO")
        
        ender_dest = ET.SubElement(dest, 'enderDest')
        ET.SubElement(ender_dest, 'xLgr').text = nfse.tomador.endereco.logradouro[:60] or "RUA NAO INFORMADA"
        ET.SubElement(ender_dest, 'nro').text = nfse.tomador.endereco.numero or "S/N"
        ET.SubElement(ender_dest, 'xBairro').text = nfse.tomador.endereco.bairro[:60] or "BAIRRO"
        ET.SubElement(ender_dest, 'cMun').text = nfse.tomador.endereco.codigo_municipio or "3550308"
        ET.SubElement(ender_dest, 'xMun').text = "MUNICIPIO"
        ET.SubElement(ender_dest, 'UF').text = nfse.tomador.endereco.uf or "SP"
        ET.SubElement(ender_dest, 'CEP').text = self._digits(nfse.tomador.endereco.cep) or "00000000"
        if nfse.tomador.telefone:
            ET.SubElement(ender_dest, 'fone').text = self._digits(nfse.tomador.telefone)[:14]
        
        if nfse.tomador.email:
            ET.SubElement(dest, 'email').text = nfse.tomador.email[:60]
        
        ET.SubElement(dest, 'indIEDest').text = "9"
        
        # det
        det = ET.SubElement(inf_nfe, 'det', nItem="1")
        prod = ET.SubElement(det, 'prod')
        ET.SubElement(prod, 'cProd').text = nfse.servico_codigo.replace('.', '')[:60] or "001"
        ET.SubElement(prod, 'cEAN').text = "SEM GTIN"
        ET.SubElement(prod, 'xProd').text = (nfse.discriminacao[:120] or "PRESTACAO DE SERVICO")
        ET.SubElement(prod, 'NCM').text = "00"
        # CFOP: 5933 (dentro do estado) ou 6933 (fora)
        cfop = "5933" if nfse.prestador.endereco.uf == nfse.tomador.endereco.uf else "6933"
        ET.SubElement(prod, 'CFOP').text = cfop
        ET.SubElement(prod, 'uCom').text = "UN"
        ET.SubElement(prod, 'qCom').text = "1.0000"
        ET.SubElement(prod, 'vUnCom').text = f"{nfse.valores.valor_servicos:.4f}"
        ET.SubElement(prod, 'vProd').text = f"{nfse.valores.valor_servicos:.2f}"
        ET.SubElement(prod, 'cEANTrib').text = "SEM GTIN"
        ET.SubElement(prod, 'uTrib').text = "UN"
        ET.SubElement(prod, 'qTrib').text = "1.0000"
        ET.SubElement(prod, 'vUnTrib').text = f"{nfse.valores.valor_servicos:.4f}"
        ET.SubElement(prod, 'indTot').text = "1"
        
        imposto = ET.SubElement(det, 'imposto')
        icms = ET.SubElement(imposto, 'ICMS')
        icms00 = ET.SubElement(icms, 'ICMS00')
        ET.SubElement(icms00, 'orig').text = "0"
        ET.SubElement(icms00, 'CST').text = "00"
        ET.SubElement(icms00, 'modBC').text = "3"
        ET.SubElement(icms00, 'vBC').text = "0.00"
        ET.SubElement(icms00, 'pICMS').text = "0.00"
        ET.SubElement(icms00, 'vICMS').text = "0.00"
        
        pis = ET.SubElement(imposto, 'PIS')
        pis_outr = ET.SubElement(pis, 'PISOutr')
        ET.SubElement(pis_outr, 'CST').text = "99"
        ET.SubElement(pis_outr, 'vBC').text = "0.00"
        ET.SubElement(pis_outr, 'pPIS').text = "0.00"
        ET.SubElement(pis_outr, 'vPIS').text = "0.00"
        
        cofins = ET.SubElement(imposto, 'COFINS')
        cofins_outr = ET.SubElement(cofins, 'COFINSOutr')
        ET.SubElement(cofins_outr, 'CST').text = "99"
        ET.SubElement(cofins_outr, 'vBC').text = "0.00"
        ET.SubElement(cofins_outr, 'pCOFINS').text = "0.00"
        ET.SubElement(cofins_outr, 'vCOFINS').text = "0.00"
        
        # total
        total = ET.SubElement(inf_nfe, 'total')
        icms_tot = ET.SubElement(total, 'ICMSTot')
        fields = [
            ('vBC', "0.00"), ('vICMS', "0.00"), ('vICMSDeson', "0.00"), ('vFCP', "0.00"),
            ('vBCST', "0.00"), ('vST', "0.00"), ('vFCPST', "0.00"), ('vFCPSTRet', "0.00"),
            ('vProd', f"{nfse.valores.valor_servicos:.2f}"), ('vFrete', "0.00"), ('vSeg', "0.00"),
            ('vDesc', "0.00"), ('vII', "0.00"), ('vIPI', "0.00"), ('vIPIDevol', "0.00"),
            ('vPIS', "0.00"), ('vCOFINS', "0.00"), ('vOutro', "0.00"),
            ('vNF', f"{nfse.valores.valor_servicos:.2f}")
        ]
        for tag, val in fields:
            ET.SubElement(icms_tot, tag).text = val
            
        # transp
        transp = ET.SubElement(inf_nfe, 'transp')
        ET.SubElement(transp, 'modFrete').text = "9"
        
        # pag
        pag = ET.SubElement(inf_nfe, 'pag')
        det_pag = ET.SubElement(pag, 'detPag')
        ET.SubElement(det_pag, 'tPag').text = "99"
        ET.SubElement(det_pag, 'vPag').text = f"{nfse.valores.valor_servicos:.2f}"
        
        # infAdic
        inf_adic = ET.SubElement(inf_nfe, 'infAdic')
        ET.SubElement(inf_adic, 'infCpl').text = f"NFS-e Numero: {nfse.numero} - Cod. Verificacao: {nfse.codigo_verificacao}. {nfse.discriminacao}"[:5000]

        ET.indent(nfe_proc, space='  ')
        return ET.tostring(nfe_proc, encoding='utf-8', xml_declaration=True).decode('utf-8')
