"""
Módulo de parsing e extração de dados de NF-e (XML)
Versão resiliente compatível com NF-e 3.10 e 4.00
Arquivo: nfe_parser.py
"""
import zipfile
import io
from lxml import etree
import pandas as pd
from typing import List, Dict, Any, Optional

# Namespace padrão de NF-e
NAMESPACE = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}

# Mapeamento completo de XPaths com fallbacks para versões diferentes
XPATH_MAP = {
    # Identificação
    'Chave de Acesso': './/nfe:infNFe',
    'Número da NF': './/nfe:ide/nfe:nNF',
    'Série': './/nfe:ide/nfe:serie',
    'Data e Hora de Emissão': './/nfe:ide/nfe:dhEmi',
    'Natureza da Operação': './/nfe:ide/nfe:natOp',
    'Status do Protocolo': './/nfe:protNFe/nfe:infProt/nfe:xMotivo',
    'Modelo': './/nfe:ide/nfe:mod',
    'Versão': './/nfe:infNFe',  # Extrai do atributo versao
    
    # Emitente/Destinatário
    'CNPJ do Emitente': './/nfe:emit/nfe:CNPJ',
    'CPF do Emitente': './/nfe:emit/nfe:CPF',  # Fallback para pessoa física
    'Razão Social Emitente': './/nfe:emit/nfe:xNome',
    'CNPJ do Destinatário': './/nfe:dest/nfe:CNPJ',
    'CPF do Destinatário': './/nfe:dest/nfe:CPF',  # Fallback para pessoa física
    'Razão Social Destinatário': './/nfe:dest/nfe:xNome',
    'Inscrição Estadual Destinatário': './/nfe:dest/nfe:IE',
    
    # Detalhes dos Itens (tratados separadamente)
    'Número do Item': 'nItem',
    'Descrição do Produto': './/nfe:prod/nfe:xProd',
    'CFOP do Item': './/nfe:prod/nfe:CFOP',
    'Quantidade Comercial': './/nfe:prod/nfe:qCom',
    'Valor Unitário': './/nfe:prod/nfe:vUnCom',
    'NCM': './/nfe:prod/nfe:NCM',
    'CEST': './/nfe:prod/nfe:CEST',
    
    # Partilha do ICMS Interestadual (DIFAL) - Nível do Item
    'BC ICMS UF Destino': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:vBCUFDest',
    'Alíquota Interna UF Destino': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:pICMSUFDest',
    'Alíquota Interestadual': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:pICMSInter',
    'Percentual Partilha ICMS': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:pICMSInterPart',
    'Valor ICMS UF Destino': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:vICMSUFDest',
    'Valor ICMS UF Remetente': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:vICMSUFRemet',
    
    # Fundo de Combate à Pobreza (FCP) - Nível do Item
    'BC FCP UF Destino': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:vBCFCPUFDest',
    'Percentual FCP UF Destino': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:pFCPUFDest',
    'Valor FCP UF Destino': './/nfe:imposto/nfe:ICMS/nfe:ICMSUFDest/nfe:vFCPUFDest',
    
    # Totais e Impostos (campos essenciais)
    'Valor Total da NF': './/nfe:total/nfe:ICMSTot/nfe:vNF',
    'Valor Total dos Produtos': './/nfe:total/nfe:ICMSTot/nfe:vProd',
    'Valor Total do ICMS': './/nfe:total/nfe:ICMSTot/nfe:vICMS',
    'Valor Total do IPI': './/nfe:total/nfe:ICMSTot/nfe:vIPI',
    
    # DIFAL e FCP (Totalizadores - presentes apenas em NF-e 4.00 ou operações específicas)
    'Valor ICMS UF Destino (Total)': './/nfe:total/nfe:ICMSTot/nfe:vICMSUFDest',
    'Valor ICMS UF Remetente (Total)': './/nfe:total/nfe:ICMSTot/nfe:vICMSUFRemet',
    'Valor FCP UF Destino (Total)': './/nfe:total/nfe:ICMSTot/nfe:vFCPUFDest',
}

# Campos que pertencem ao grupo "Detalhes dos Itens"
ITEM_FIELDS = [
    'Número do Item',
    'Descrição do Produto',
    'CFOP do Item',
    'Quantidade Comercial',
    'Valor Unitário',
    'NCM',
    'CEST',
    # DIFAL - Partilha do ICMS
    'BC ICMS UF Destino',
    'Alíquota Interna UF Destino',
    'Alíquota Interestadual',
    'Percentual Partilha ICMS',
    'Valor ICMS UF Destino',
    'Valor ICMS UF Remetente',
    # FCP - Fundo de Combate à Pobreza
    'BC FCP UF Destino',
    'Percentual FCP UF Destino',
    'Valor FCP UF Destino',
]


def safe_find_text(element: etree._Element, xpath: str, namespaces: Dict[str, str], 
                   default: Optional[str] = None) -> Optional[str]:
    """
    Busca um elemento de forma segura e retorna seu texto.
    Retorna default (None) se o elemento não existir.
    
    Args:
        element: Elemento XML raiz ou contexto
        xpath: Expressão XPath para busca
        namespaces: Dicionário de namespaces
        default: Valor padrão a retornar se elemento não for encontrado
        
    Returns:
        Texto do elemento ou valor default
    """
    try:
        found = element.find(xpath, namespaces=namespaces)
        if found is not None and found.text:
            return found.text.strip()
        return default
    except Exception:
        return default


def safe_find_attribute(element: etree._Element, xpath: str, attr_name: str,
                       namespaces: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
    """
    Busca um atributo de elemento de forma segura.
    
    Args:
        element: Elemento XML raiz ou contexto
        xpath: Expressão XPath para busca
        attr_name: Nome do atributo a extrair
        namespaces: Dicionário de namespaces
        default: Valor padrão a retornar se não encontrado
        
    Returns:
        Valor do atributo ou valor default
    """
    try:
        found = element.find(xpath, namespaces=namespaces)
        if found is not None:
            attr_value = found.get(attr_name)
            if attr_value:
                return attr_value.strip()
        return default
    except Exception:
        return default


def detect_nfe_version(root: etree._Element) -> str:
    """
    Detecta a versão da NF-e a partir do XML.
    
    Args:
        root: Elemento raiz do XML
        
    Returns:
        Versão da NF-e (ex: "4.00", "3.10") ou "desconhecida"
    """
    version = safe_find_attribute(root, './/nfe:infNFe', 'versao', NAMESPACE, default="desconhecida")
    return version


def extract_xml_from_files(uploaded_files: List) -> List[bytes]:
    """
    Extrai conteúdo XML de arquivos individuais ou ZIPs.
    
    Args:
        uploaded_files: Lista de arquivos enviados
        
    Returns:
        Lista de conteúdos XML em bytes
    """
    xml_contents = []
    
    for file in uploaded_files:
        try:
            file_content = file.read()
            file.seek(0)  # Reset para possível reutilização
            
            if file.name.endswith('.zip'):
                # Descompactar ZIP
                with zipfile.ZipFile(io.BytesIO(file_content)) as zip_ref:
                    for zip_info in zip_ref.filelist:
                        if zip_info.filename.lower().endswith('.xml'):
                            try:
                                xml_contents.append(zip_ref.read(zip_info.filename))
                            except Exception:
                                continue  # Ignora arquivos corrompidos dentro do ZIP
            elif file.name.lower().endswith('.xml'):
                xml_contents.append(file_content)
        except Exception:
            continue  # Ignora arquivos com problemas
    
    return xml_contents


def parse_nfe_xml(xml_content: bytes, selected_fields: Dict[str, bool]) -> List[Dict[str, Any]]:
    """
    Faz o parsing de um XML de NF-e e retorna lista de registros.
    Compatível com versões 3.10 e 4.00.
    
    Args:
        xml_content: Conteúdo do XML em bytes
        selected_fields: Dicionário com campos selecionados pelo usuário
        
    Returns:
        Lista de dicionários com dados extraídos
    """
    try:
        root = etree.fromstring(xml_content)
    except Exception as e:
        # XML malformado ou corrompido
        return []
    
    # Detecta versão da NF-e
    nfe_version = detect_nfe_version(root)
    
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
                chave = safe_find_attribute(root, xpath, 'Id', NAMESPACE)
                if chave:
                    header_data[field_name] = chave.replace('NFe', '')
                else:
                    header_data[field_name] = None
                    
            elif field_name == 'Versão':
                # Extrai versão do atributo
                header_data[field_name] = nfe_version
                
            elif field_name == 'CNPJ do Emitente':
                # Tenta CNPJ, se não houver tenta CPF
                cnpj = safe_find_text(root, xpath, NAMESPACE)
                if not cnpj:
                    cnpj = safe_find_text(root, XPATH_MAP.get('CPF do Emitente', ''), NAMESPACE)
                header_data[field_name] = cnpj
                
            elif field_name == 'CNPJ do Destinatário':
                # Tenta CNPJ, se não houver tenta CPF
                cnpj = safe_find_text(root, xpath, NAMESPACE)
                if not cnpj:
                    cnpj = safe_find_text(root, XPATH_MAP.get('CPF do Destinatário', ''), NAMESPACE)
                header_data[field_name] = cnpj
                
            else:
                # Extração padrão com safe_find_text
                text_value = safe_find_text(root, xpath, NAMESPACE)
                header_data[field_name] = text_value
                
        except Exception:
            # Em caso de erro, define como None
            header_data[field_name] = None
    
    # Se não há campos de itens, retorna apenas uma linha de resumo
    if not has_item_fields:
        return [header_data] if header_data else []
    
    # Caso contrário, processa cada item
    results = []
    items = root.findall('.//nfe:det', namespaces=NAMESPACE)
    
    if not items:
        # Se não há itens, retorna apenas cabeçalho
        return [header_data] if header_data else []
    
    for item in items:
        row_data = header_data.copy()
        
        for field_name in ITEM_FIELDS:
            if field_name not in selected_fields or not selected_fields[field_name]:
                continue
            
            try:
                if field_name == 'Número do Item':
                    # Extrai número do item do atributo
                    nitem = item.get('nItem', '')
                    row_data[field_name] = nitem if nitem else None
                else:
                    # Extração padrão com safe_find_text
                    xpath = XPATH_MAP.get(field_name, '')
                    text_value = safe_find_text(item, xpath, NAMESPACE)
                    row_data[field_name] = text_value
            except Exception:
                row_data[field_name] = None
        
        results.append(row_data)
    
    return results if results else [header_data]


def process_nfe_files(uploaded_files: List, selected_fields: Dict[str, bool]) -> pd.DataFrame:
    """
    Função principal: processa todos os arquivos e retorna DataFrame consolidado.
    
    Args:
        uploaded_files: Lista de arquivos enviados
        selected_fields: Dicionário com campos selecionados
        
    Returns:
        DataFrame com dados consolidados
    """
    if not uploaded_files:
        return pd.DataFrame()
    
    xml_contents = extract_xml_from_files(uploaded_files)
    
    if not xml_contents:
        return pd.DataFrame()
    
    all_records = []
    errors_count = 0
    
    for xml_content in xml_contents:
        try:
            records = parse_nfe_xml(xml_content, selected_fields)
            all_records.extend(records)
        except Exception:
            errors_count += 1
            continue  # Continua processando outros arquivos
    
    if not all_records:
        return pd.DataFrame()
    
    df = pd.DataFrame(all_records)
    
    # Ordenar colunas conforme ordem dos filtros
    ordered_cols = [col for col in selected_fields.keys() 
                    if col in df.columns and selected_fields[col]]
    
    # Garante que todas as colunas selecionadas existam
    for col in ordered_cols:
        if col not in df.columns:
            df[col] = None
    
    df = df[ordered_cols]
    
    return df