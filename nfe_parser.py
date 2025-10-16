"""
Módulo de parsing e extração de dados de NF-e (XML)
Versão FINAL - 100% conforme leiaute oficial da NF-e 4.00
Referência: http://moc.sped.fazenda.pr.gov.br/Leiaute.html
Arquivo: nfe_parser.py
"""
import zipfile
import io
from lxml import etree
import pandas as pd
from typing import List, Dict, Any, Optional

# Namespace padrão obrigatório da NF-e
NAMESPACE = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

# Mapeamento XPath conforme IDs do leiaute oficial
XPATH_MAP = {
    # Grupo B - Identificação da NF-e (ID B01)
    'Chave de Acesso': './/nfe:infNFe',  # ID A03 - atributo Id
    'Número da NF': './/nfe:ide/nfe:nNF',  # ID B08
    'Série': './/nfe:ide/nfe:serie',  # ID B07
    'Data e Hora de Emissão': './/nfe:ide/nfe:dhEmi',  # ID B09
    'Natureza da Operação': './/nfe:ide/nfe:natOp',  # ID B05
    'Modelo': './/nfe:ide/nfe:mod',  # ID B06
    'Versão': './/nfe:infNFe',  # ID A02 - atributo versao
    
    # Protocolo de Autorização
    'Status do Protocolo': './/nfe:protNFe/nfe:infProt/nfe:xMotivo',
    
    # Grupo C - Identificação do Emitente (ID C01)
    'CNPJ do Emitente': './/nfe:emit/nfe:CNPJ',  # ID C02
    'CPF do Emitente': './/nfe:emit/nfe:CPF',  # ID C02a
    'Razão Social Emitente': './/nfe:emit/nfe:xNome',  # ID C03
    'Nome Fantasia Emitente': './/nfe:emit/nfe:xFant',  # ID C04
    
    # Grupo E - Identificação do Destinatário (ID E01)
    'CNPJ do Destinatário': './/nfe:dest/nfe:CNPJ',  # ID E02
    'CPF do Destinatário': './/nfe:dest/nfe:CPF',  # ID E03
    'Razão Social Destinatário': './/nfe:dest/nfe:xNome',  # ID E04
    'Inscrição Estadual Destinatário': './/nfe:dest/nfe:IE',  # ID E17
    
    # Grupo I - Produtos e Serviços (ID I01) - Nível do Item
    'Número do Item': 'nItem',  # ID H02 - atributo
    'Cód. Produto': './/nfe:prod/nfe:cProd',  # ID I02
    'Código EAN': './/nfe:prod/nfe:cEAN',  # ID I03
    'Descrição do Produto': './/nfe:prod/nfe:xProd',  # ID I04
    'NCM': './/nfe:prod/nfe:NCM',  # ID I05
    'CEST': './/nfe:prod/nfe:CEST',  # ID I08
    'CFOP do Item': './/nfe:prod/nfe:CFOP',  # ID I09
    'Unidade Comercial': './/nfe:prod/nfe:uCom',  # ID I10
    'Quantidade Comercial': './/nfe:prod/nfe:qCom',  # ID I11
    'Valor Unitário': './/nfe:prod/nfe:vUnCom',  # ID I12
    'Valor Total Item': './/nfe:prod/nfe:vProd',  # ID I13
    
    # Grupo M/N - Impostos (genérico para todos os CST)
    'Origem da Mercadoria': './/nfe:imposto/nfe:ICMS',  # ID N11 (orig)
    'CST ICMS': './/nfe:imposto/nfe:ICMS',  # ID N12
    'Modalidade BC ICMS': './/nfe:imposto/nfe:ICMS',  # ID N13 (modBC)
    'Base Cálculo ICMS': './/nfe:imposto/nfe:ICMS',  # ID N15 (vBC)
    'Alíquota ICMS': './/nfe:imposto/nfe:ICMS',  # ID N16 (pICMS)
    'Valor ICMS': './/nfe:imposto/nfe:ICMS',  # ID N17 (vICMS)
    
    # IPI (ID O01)
    'Valor IPI': './/nfe:imposto/nfe:IPI',  # ID O17 (vIPI)
    
    # PIS (ID Q01)
    'Valor PIS': './/nfe:imposto/nfe:PIS',  # vPIS (vários CST)
    
    # COFINS (ID S01)
    'Valor COFINS': './/nfe:imposto/nfe:COFINS',  # vCOFINS (vários CST)
    
    # Grupo NA - ICMS para UF de destino (DIFAL) - ID NA01
    'BC ICMS UF Destino': './/nfe:imposto/nfe:ICMSUFDest/nfe:vBCUFDest',  # ID NA03
    'BC FCP UF Destino': './/nfe:imposto/nfe:ICMSUFDest/nfe:vBCFCPUFDest',  # ID NA04
    'Percentual FCP UF Destino': './/nfe:imposto/nfe:ICMSUFDest/nfe:pFCPUFDest',  # ID NA05
    'Alíquota Interna UF Destino': './/nfe:imposto/nfe:ICMSUFDest/nfe:pICMSUFDest',  # ID NA07
    'Alíquota Interestadual': './/nfe:imposto/nfe:ICMSUFDest/nfe:pICMSInter',  # ID NA09
    'Percentual Partilha ICMS': './/nfe:imposto/nfe:ICMSUFDest/nfe:pICMSInterPart',  # ID NA11
    'Valor FCP UF Destino': './/nfe:imposto/nfe:ICMSUFDest/nfe:vFCPUFDest',  # ID NA13
    'Valor ICMS UF Destino': './/nfe:imposto/nfe:ICMSUFDest/nfe:vICMSUFDest',  # ID NA15
    'Valor ICMS UF Remetente': './/nfe:imposto/nfe:ICMSUFDest/nfe:vICMSUFRemet',  # ID NA17
    
    # Grupo W - Total da NF-e (ID W01)
    'Valor Total da NF': './/nfe:total/nfe:ICMSTot/nfe:vNF',  # ID W29
    'Valor Total dos Produtos': './/nfe:total/nfe:ICMSTot/nfe:vProd',  # ID W12
    'Valor Total do ICMS': './/nfe:total/nfe:ICMSTot/nfe:vICMS',  # ID W14
    'Valor Total do IPI': './/nfe:total/nfe:ICMSTot/nfe:vIPI',  # ID W16
}

# Campos que pertencem ao nível do item (det)
ITEM_FIELDS = [
    'Número do Item',
    'Cód. Produto',
    'Código EAN',
    'Descrição do Produto',
    'NCM',
    'CEST',
    'CFOP do Item',
    'Unidade Comercial',
    'Quantidade Comercial',
    'Valor Unitário',
    'Valor Total Item',
    # Impostos do item
    'Origem da Mercadoria',
    'CST ICMS',
    'Modalidade BC ICMS',
    'Base Cálculo ICMS',
    'Alíquota ICMS',
    'Valor ICMS',
    'Valor IPI',
    'Valor PIS',
    'Valor COFINS',
    # DIFAL por item
    'BC ICMS UF Destino',
    'BC FCP UF Destino',
    'Percentual FCP UF Destino',
    'Alíquota Interna UF Destino',
    'Alíquota Interestadual',
    'Percentual Partilha ICMS',
    'Valor FCP UF Destino',
    'Valor ICMS UF Destino',
    'Valor ICMS UF Remetente',
]


def safe_find_text(element: etree._Element, xpath: str, namespaces: Dict[str, str], 
                   default: Optional[str] = None) -> Optional[str]:
    """Busca texto de elemento de forma segura."""
    try:
        found = element.find(xpath, namespaces=namespaces)
        if found is not None and found.text:
            return found.text.strip()
        return default
    except Exception:
        return default


def safe_find_attribute(element: etree._Element, xpath: str, attr_name: str,
                       namespaces: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
    """Busca atributo de forma segura."""
    try:
        found = element.find(xpath, namespaces=namespaces)
        if found is not None:
            attr_value = found.get(attr_name)
            if attr_value:
                return attr_value.strip()
        return default
    except Exception:
        return default


def extract_icms_field(item: etree._Element, field_tag: str, namespaces: Dict[str, str]) -> Any:
    """
    Extrai campo de ICMS de forma genérica, independente do CST.
    Busca em TODOS os grupos: ICMS00, ICMS10, ICMS20, ICMS30, ICMS40, ICMS51, ICMS60, ICMS70, ICMS90, etc.
    """
    try:
        # Busca genérica: .//nfe:ICMS//nfe:campo captura de qualquer subgrupo
        xpath = f'.//nfe:imposto/nfe:ICMS//nfe:{field_tag}'
        found = item.find(xpath, namespaces=namespaces)
        
        if found is not None and found.text:
            text_value = found.text.strip()
            # Tenta converter para float se possível
            try:
                return float(text_value)
            except ValueError:
                return text_value
        return None
    except Exception:
        return None


def extract_tax_value(item: etree._Element, tax_group: str, value_tag: str, namespaces: Dict[str, str]) -> float:
    """
    Extrai valor de imposto (IPI, PIS, COFINS) de forma genérica.
    """
    try:
        xpath = f'.//nfe:imposto/nfe:{tax_group}//nfe:{value_tag}'
        found = item.find(xpath, namespaces=namespaces)
        
        if found is not None and found.text:
            return float(found.text.strip())
        return 0.0
    except (ValueError, AttributeError):
        return 0.0


def extract_icmsufdest_field(item: etree._Element, field_tag: str, namespaces: Dict[str, str]) -> Optional[float]:
    """
    Extrai campo do grupo ICMSUFDest (DIFAL) conforme leiaute oficial (Grupo NA).
    """
    try:
        xpath = f'.//nfe:imposto/nfe:ICMSUFDest/nfe:{field_tag}'
        found = item.find(xpath, namespaces=namespaces)
        
        if found is not None and found.text:
            return float(found.text.strip())
        return None
    except (ValueError, AttributeError):
        return None


def detect_nfe_version(root: etree._Element) -> str:
    """Detecta versão da NF-e (ID A02)."""
    version = safe_find_attribute(root, './/nfe:infNFe', 'versao', NAMESPACE, default="desconhecida")
    return version


def extract_xml_from_files(uploaded_files: List) -> List[bytes]:
    """Extrai conteúdo XML de arquivos individuais ou ZIPs."""
    xml_contents = []
    
    for file in uploaded_files:
        try:
            file_content = file.read()
            file.seek(0)
            
            if file.name.endswith('.zip'):
                with zipfile.ZipFile(io.BytesIO(file_content)) as zip_ref:
                    for zip_info in zip_ref.filelist:
                        if zip_info.filename.lower().endswith('.xml'):
                            try:
                                xml_contents.append(zip_ref.read(zip_info.filename))
                            except Exception:
                                continue
            elif file.name.lower().endswith('.xml'):
                xml_contents.append(file_content)
        except Exception:
            continue
    
    return xml_contents


def parse_nfe_xml(xml_content: bytes, selected_fields: Dict[str, bool]) -> List[Dict[str, Any]]:
    """
    Parsing conforme leiaute oficial da NF-e.
    RETORNA: UMA LINHA POR ITEM (det - ID H01).
    """
    try:
        root = etree.fromstring(xml_content)
    except Exception:
        return []
    
    nfe_version = detect_nfe_version(root)
    
    # Extrai dados do cabeçalho (infNFe, ide, emit, dest, total)
    header_data = {}
    
    for field_name, is_selected in selected_fields.items():
        if not is_selected or field_name in ITEM_FIELDS:
            continue
        
        xpath = XPATH_MAP.get(field_name)
        if not xpath:
            continue
        
        try:
            if field_name == 'Chave de Acesso':
                # ID A03 - atributo Id
                chave = safe_find_attribute(root, xpath, 'Id', NAMESPACE)
                if chave:
                    header_data[field_name] = chave.replace('NFe', '')
                else:
                    header_data[field_name] = None
                    
            elif field_name == 'Versão':
                # ID A02 - atributo versao
                header_data[field_name] = nfe_version
                
            elif field_name == 'CNPJ do Emitente':
                # ID C02 ou C02a (fallback para CPF)
                cnpj = safe_find_text(root, xpath, NAMESPACE)
                if not cnpj:
                    cnpj = safe_find_text(root, XPATH_MAP.get('CPF do Emitente', ''), NAMESPACE)
                header_data[field_name] = cnpj
                
            elif field_name == 'CNPJ do Destinatário':
                # ID E02 ou E03 (fallback para CPF)
                cnpj = safe_find_text(root, xpath, NAMESPACE)
                if not cnpj:
                    cnpj = safe_find_text(root, XPATH_MAP.get('CPF do Destinatário', ''), NAMESPACE)
                header_data[field_name] = cnpj
                
            else:
                text_value = safe_find_text(root, xpath, NAMESPACE)
                header_data[field_name] = text_value
                
        except Exception:
            header_data[field_name] = None
    
    # OBRIGATÓRIO: Itera sobre TODOS os items (det - ID H01)
    results = []
    items = root.findall('.//nfe:det', namespaces=NAMESPACE)
    
    if not items:
        return [header_data] if header_data else []
    
    for item in items:
        row_data = header_data.copy()
        
        # ID H02 - nItem (atributo)
        nitem = item.get('nItem', '')
        if 'Número do Item' in selected_fields and selected_fields['Número do Item']:
            row_data['Número do Item'] = nitem if nitem else None
        
        # Processa campos do item
        for field_name in ITEM_FIELDS:
            if field_name not in selected_fields or not selected_fields[field_name]:
                continue
            
            if field_name == 'Número do Item':
                continue  # Já processado
            
            try:
                # Campos de ICMS (Grupo N)
                if field_name == 'Origem da Mercadoria':
                    row_data[field_name] = extract_icms_field(item, 'orig', NAMESPACE)
                
                elif field_name == 'CST ICMS':
                    row_data[field_name] = extract_icms_field(item, 'CST', NAMESPACE)
                
                elif field_name == 'Modalidade BC ICMS':
                    row_data[field_name] = extract_icms_field(item, 'modBC', NAMESPACE)
                
                elif field_name == 'Base Cálculo ICMS':
                    value = extract_icms_field(item, 'vBC', NAMESPACE)
                    row_data[field_name] = value if value is not None else 0.0
                
                elif field_name == 'Alíquota ICMS':
                    value = extract_icms_field(item, 'pICMS', NAMESPACE)
                    row_data[field_name] = value if value is not None else 0.0
                
                elif field_name == 'Valor ICMS':
                    value = extract_icms_field(item, 'vICMS', NAMESPACE)
                    row_data[field_name] = value if value is not None else 0.0
                
                # IPI (Grupo O)
                elif field_name == 'Valor IPI':
                    row_data[field_name] = extract_tax_value(item, 'IPI', 'vIPI', NAMESPACE)
                
                # PIS (Grupo Q)
                elif field_name == 'Valor PIS':
                    row_data[field_name] = extract_tax_value(item, 'PIS', 'vPIS', NAMESPACE)
                
                # COFINS (Grupo S)
                elif field_name == 'Valor COFINS':
                    row_data[field_name] = extract_tax_value(item, 'COFINS', 'vCOFINS', NAMESPACE)
                
                # Grupo ICMSUFDest (DIFAL - Grupo NA)
                elif field_name in ['BC ICMS UF Destino', 'BC FCP UF Destino', 'Percentual FCP UF Destino',
                                   'Alíquota Interna UF Destino', 'Alíquota Interestadual', 'Percentual Partilha ICMS',
                                   'Valor FCP UF Destino', 'Valor ICMS UF Destino', 'Valor ICMS UF Remetente']:
                    # Mapeia nome do campo para tag XML
                    tag_map = {
                        'BC ICMS UF Destino': 'vBCUFDest',
                        'BC FCP UF Destino': 'vBCFCPUFDest',
                        'Percentual FCP UF Destino': 'pFCPUFDest',
                        'Alíquota Interna UF Destino': 'pICMSUFDest',
                        'Alíquota Interestadual': 'pICMSInter',
                        'Percentual Partilha ICMS': 'pICMSInterPart',
                        'Valor FCP UF Destino': 'vFCPUFDest',
                        'Valor ICMS UF Destino': 'vICMSUFDest',
                        'Valor ICMS UF Remetente': 'vICMSUFRemet',
                    }
                    tag = tag_map.get(field_name)
                    if tag:
                        value = extract_icmsufdest_field(item, tag, NAMESPACE)
                        row_data[field_name] = value if value is not None else 0.0
                
                # Campos de produto (Grupo I)
                elif field_name in ['Quantidade Comercial', 'Valor Unitário', 'Valor Total Item']:
                    xpath = XPATH_MAP.get(field_name, '')
                    text_value = safe_find_text(item, xpath, NAMESPACE)
                    if text_value:
                        try:
                            row_data[field_name] = float(text_value)
                        except ValueError:
                            row_data[field_name] = 0.0
                    else:
                        row_data[field_name] = 0.0
                
                # Campos de texto
                else:
                    xpath = XPATH_MAP.get(field_name, '')
                    text_value = safe_find_text(item, xpath, NAMESPACE)
                    row_data[field_name] = text_value
                    
            except Exception:
                # Define valor padrão em caso de erro
                if field_name in ['Quantidade Comercial', 'Valor Unitário', 'Valor Total Item',
                                 'Base Cálculo ICMS', 'Alíquota ICMS', 'Valor ICMS',
                                 'Valor IPI', 'Valor PIS', 'Valor COFINS',
                                 'BC ICMS UF Destino', 'BC FCP UF Destino', 'Percentual FCP UF Destino',
                                 'Alíquota Interna UF Destino', 'Alíquota Interestadual', 'Percentual Partilha ICMS',
                                 'Valor FCP UF Destino', 'Valor ICMS UF Destino', 'Valor ICMS UF Remetente']:
                    row_data[field_name] = 0.0
                else:
                    row_data[field_name] = None
        
        results.append(row_data)
    
    return results if results else [header_data]


def process_nfe_files(uploaded_files: List, selected_fields: Dict[str, bool]) -> pd.DataFrame:
    """
    Função principal: processa arquivos e retorna DataFrame.
    IMPORTANTE: UMA LINHA POR ITEM de produto.
    """
    if not uploaded_files:
        return pd.DataFrame()
    
    xml_contents = extract_xml_from_files(uploaded_files)
    
    if not xml_contents:
        return pd.DataFrame()
    
    all_records = []
    
    for xml_content in xml_contents:
        try:
            records = parse_nfe_xml(xml_content, selected_fields)
            all_records.extend(records)
        except Exception:
            continue
    
    if not all_records:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_records)
    
    # Ordena colunas
    ordered_cols = [col for col in selected_fields.keys() 
                    if col in df.columns and selected_fields[col]]
    
    for col in ordered_cols:
        if col not in df.columns:
            if any(keyword in col for keyword in ['Valor', 'Quantidade', 'Alíquota', 'Base', 'Percentual', 'BC']):
                df[col] = 0.0
            else:
                df[col] = None
    
    df = df[ordered_cols]
    
    # Converte campos numéricos para float
    numeric_fields = [
        'Quantidade Comercial', 'Valor Unitário', 'Valor Total Item',
        'Base Cálculo ICMS', 'Alíquota ICMS', 'Valor ICMS',
        'Valor IPI', 'Valor PIS', 'Valor COFINS',
        'Valor Total da NF', 'Valor Total dos Produtos', 'Valor Total do ICMS', 'Valor Total do IPI',
        'BC ICMS UF Destino', 'BC FCP UF Destino', 'Percentual FCP UF Destino',
        'Alíquota Interna UF Destino', 'Alíquota Interestadual', 'Percentual Partilha ICMS',
        'Valor FCP UF Destino', 'Valor ICMS UF Destino', 'Valor ICMS UF Remetente'
    ]
    
    for field in numeric_fields:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0.0)
    
    return df