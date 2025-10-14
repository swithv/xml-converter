"""
Módulo de parsing e extração de dados de NF-e (XML)
Arquivo: nfe_parser.py
"""
import zipfile
import io
from lxml import etree
import pandas as pd
from typing import List, Dict, Any

# Namespace padrão de NF-e
NAMESPACE = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

# Mapeamento completo de XPaths
XPATH_MAP = {
    # Identificação
    'Chave de Acesso': './/nfe:infNFe',
    'Número da NF': './/nfe:ide/nfe:nNF',
    'Série': './/nfe:ide/nfe:serie',
    'Data e Hora de Emissão': './/nfe:ide/nfe:dhEmi',
    'Natureza da Operação': './/nfe:ide/nfe:natOp',
    'Status do Protocolo': './/nfe:protNFe/nfe:infProt/nfe:xMotivo',
    
    # Emitente/Destinatário
    'CNPJ do Emitente': './/nfe:emit/nfe:CNPJ',
    'Razão Social Emitente': './/nfe:emit/nfe:xNome',
    'CNPJ do Destinatário': './/nfe:dest/nfe:CNPJ',
    'Razão Social Destinatário': './/nfe:dest/nfe:xNome',
    'Inscrição Estadual Destinatário': './/nfe:dest/nfe:IE',
    
    # Detalhes dos Itens (tratados separadamente)
    'Número do Item': 'nItem',
    'Descrição do Produto': './/nfe:prod/nfe:xProd',
    'CFOP do Item': './/nfe:prod/nfe:CFOP',
    'Quantidade Comercial': './/nfe:prod/nfe:qCom',
    'Valor Unitário': './/nfe:prod/nfe:vUnCom',
    
    # Totais e Impostos
    'Valor Total da NF': './/nfe:total/nfe:ICMSTot/nfe:vNF',
    'Valor Total dos Produtos': './/nfe:total/nfe:ICMSTot/nfe:vProd',
    'Valor Total do ICMS': './/nfe:total/nfe:ICMSTot/nfe:vICMS',
    'Valor Total do IPI': './/nfe:total/nfe:ICMSTot/nfe:vIPI',
}

# Campos que pertencem ao grupo "Detalhes dos Itens"
ITEM_FIELDS = [
    'Número do Item',
    'Descrição do Produto',
    'CFOP do Item',
    'Quantidade Comercial',
    'Valor Unitário'
]


def extract_xml_from_files(uploaded_files: List) -> List[bytes]:
    """
    Extrai conteúdo XML de arquivos individuais ou ZIPs
    """
    xml_contents = []
    
    for file in uploaded_files:
        file_content = file.read()
        file.seek(0)  # Reset para possível reutilização
        
        if file.name.endswith('.zip'):
            # Descompactar ZIP
            with zipfile.ZipFile(io.BytesIO(file_content)) as zip_ref:
                for zip_info in zip_ref.filelist:
                    if zip_info.filename.endswith('.xml'):
                        xml_contents.append(zip_ref.read(zip_info.filename))
        elif file.name.endswith('.xml'):
            xml_contents.append(file_content)
    
    return xml_contents


def parse_nfe_xml(xml_content: bytes, selected_fields: Dict[str, bool]) -> List[Dict[str, Any]]:
    """
    Faz o parsing de um XML de NF-e e retorna lista de registros
    """
    try:
        root = etree.fromstring(xml_content)
    except Exception as e:
        return []
    
    # Verifica se há campos de itens selecionados
    has_item_fields = any(field in selected_fields and selected_fields[field] 
                          for field in ITEM_FIELDS)
    
    # Extrai dados de cabeçalho (dados gerais da NF-e)
    header_data = {}
    
    for field_name, is_selected in selected_fields.items():
        if not is_selected or field_name in ITEM_FIELDS:
            continue
        
        xpath = XPATH_MAP.get(field_name)
        if not xpath:
            continue
        
        try:
            if field_name == 'Chave de Acesso':
                # Extrai ID e remove prefixo 'NFe'
                elem = root.find(xpath, namespaces=NAMESPACE)
                if elem is not None:
                    chave = elem.get('Id', '')
                    header_data[field_name] = chave.replace('NFe', '')
            else:
                elem = root.find(xpath, namespaces=NAMESPACE)
                if elem is not None:
                    header_data[field_name] = elem.text
        except Exception:
            header_data[field_name] = None
    
    # Se não há campos de itens, retorna apenas uma linha de resumo
    if not has_item_fields:
        return [header_data] if header_data else []
    
    # Caso contrário, processa cada item
    results = []
    items = root.findall('.//nfe:det', namespaces=NAMESPACE)
    
    for item in items:
        row_data = header_data.copy()
        
        for field_name in ITEM_FIELDS:
            if field_name not in selected_fields or not selected_fields[field_name]:
                continue
            
            try:
                if field_name == 'Número do Item':
                    row_data[field_name] = item.get('nItem', '')
                else:
                    xpath = XPATH_MAP[field_name]
                    elem = item.find(xpath, namespaces=NAMESPACE)
                    if elem is not None:
                        row_data[field_name] = elem.text
            except Exception:
                row_data[field_name] = None
        
        results.append(row_data)
    
    return results if results else [header_data]


def process_nfe_files(uploaded_files: List, selected_fields: Dict[str, bool]) -> pd.DataFrame:
    """
    Função principal: processa todos os arquivos e retorna DataFrame consolidado
    """
    if not uploaded_files:
        return pd.DataFrame()
    
    xml_contents = extract_xml_from_files(uploaded_files)
    
    all_records = []
    for xml_content in xml_contents:
        records = parse_nfe_xml(xml_content, selected_fields)
        all_records.extend(records)
    
    if not all_records:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_records)
    
    # Ordenar colunas conforme ordem dos filtros
    ordered_cols = [col for col in selected_fields.keys() 
                    if col in df.columns and selected_fields[col]]
    df = df[ordered_cols]
    
    return df