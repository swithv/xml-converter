# 📊 Sistema de Conversão e Dashboard de NF-e v2.0

## 🎯 Versão Final - 100% Conforme Leiaute Oficial

**Referência**: [Leiaute Oficial da NF-e](http://moc.sped.fazenda.pr.gov.br/Leiaute.html)  
**Nota Técnica**: NT 2025.001 v.1.02

---

## 📋 Características Principais

### ✅ Conformidade Total com o Leiaute
- **Namespace correto**: `http://www.portalfiscal.inf.br/nfe`
- **Mapeamento por IDs oficiais**: Todos os campos mapeados conforme IDs do manual (A01, B01, C01, etc.)
- **Granularidade por item**: Sistema gera **UMA LINHA POR ITEM** (tag `<det>` - ID H01)
- **Extração genérica de impostos**: Funciona com TODOS os CST de ICMS (00, 10, 20, 30, 40, 51, 60, 70, 90, etc.)

### 🔧 Grupos Implementados

| Grupo | Descrição | IDs | Status |
|-------|-----------|-----|--------|
| **A** | Informações da NF-e | A01-A04 | ✅ |
| **B** | Identificação | B01-B29 | ✅ |
| **C** | Emitente | C01-C19 | ✅ |
| **E** | Destinatário | E01-E19 | ✅ |
| **H** | Detalhamento (det) | H01-H02 | ✅ |
| **I** | Produtos e Serviços | I01-I80 | ✅ |
| **M** | Tributos | M01-M02 | ✅ |
| **N** | ICMS | N01-N37 | ✅ |
| **NA** | ICMSUFDest (DIFAL) | NA01-NA19 | ✅ |
| **O** | IPI | O01-O17 | ✅ |
| **Q** | PIS | Q01-Q10 | ✅ |
| **S** | COFINS | S01-S10 | ✅ |
| **W** | Total da NF-e | W01-W29 | ✅ |

---

## 🚀 Instalação e Uso

### 1. Requisitos
```bash
pip install -r requirements.txt
```

**Arquivo `requirements.txt`**:
```
streamlit==1.28.0
lxml==5.3.0
pandas>=2.2.0
openpyxl==3.1.2
plotly==5.17.0
```

### 2. Estrutura de Arquivos
```
projeto/
├── app.py                 # Interface Streamlit
├── nfe_parser.py          # Motor de extração
├── dashboard_logic.py     # Lógica dos gráficos
├── requirements.txt       # Dependências
├── logo.png              # Logo (opcional)
└── README.md             # Esta documentação
```

### 3. Executar
```bash
streamlit run app.py
```

---

## 📦 Campos Disponíveis

### Grupo B - Identificação da NF-e
- **ID A03**: Chave de Acesso (44 dígitos)
- **ID B08**: Número da NF
- **ID B07**: Série
- **ID B09**: Data e Hora de Emissão
- **ID B05**: Natureza da Operação
- **ID B06**: Modelo (55 ou 65)
- **ID A02**: Versão (4.00)

### Grupo C - Emitente
- **ID C02/C02a**: CNPJ ou CPF do Emitente
- **ID C03**: Razão Social
- **ID C04**: Nome Fantasia

### Grupo E - Destinatário
- **ID E02/E03**: CNPJ ou CPF do Destinatário
- **ID E04**: Razão Social
- **ID E17**: Inscrição Estadual

### Grupo I - Produtos (Nível do Item)
- **ID H02**: Número do Item (atributo nItem)
- **ID I02**: Código do Produto (cProd)
- **ID I03**: Código EAN/GTIN
- **ID I04**: Descrição do Produto (xProd)
- **ID I05**: NCM (8 dígitos)
- **ID I08**: CEST
- **ID I09**: CFOP
- **ID I10**: Unidade Comercial (uCom)
- **ID I11**: Quantidade Comercial (qCom)
- **ID I12**: Valor Unitário (vUnCom)
- **ID I13**: Valor Total do Item (vProd)

### Grupo N - ICMS (Todos os CST)
- **ID N11**: Origem da Mercadoria (0-8)
- **ID N12**: CST ICMS
- **ID N13**: Modalidade BC ICMS
- **ID N15**: Base de Cálculo ICMS (vBC)
- **ID N16**: Alíquota ICMS % (pICMS)
- **ID N17**: Valor ICMS (vICMS)

### Grupo NA - ICMSUFDest (DIFAL)
- **ID NA03**: BC ICMS UF Destino (vBCUFDest)
- **ID NA04**: BC FCP UF Destino (vBCFCPUFDest)
- **ID NA05**: Percentual FCP UF Destino % (pFCPUFDest)
- **ID NA07**: Alíquota Interna UF Destino % (pICMSUFDest)
- **ID NA09**: Alíquota Interestadual % (pICMSInter)
- **ID NA11**: Percentual Partilha ICMS % (pICMSInterPart) ⚠️ **CRÍTICO**
- **ID NA13**: Valor FCP UF Destino (vFCPUFDest)
- **ID NA15**: Valor ICMS UF Destino (vICMSUFDest)
- **ID NA17**: Valor ICMS UF Remetente (vICMSUFRemet)

### Outros Impostos
- **Grupo O**: Valor IPI (vIPI)
- **Grupo Q**: Valor PIS (vPIS)
- **Grupo S**: Valor COFINS (vCOFINS)

### Grupo W - Totais
- **ID W29**: Valor Total da NF-e (vNF)
- **ID W12**: Valor Total dos Produtos (vProd)
- **ID W14**: Valor Total do ICMS (vICMS)
- **ID W16**: Valor Total do IPI (vIPI)

---

## 🔍 Detalhes Técnicos

### Extração de ICMS (Grupo N)

O sistema utiliza **busca genérica** para capturar valores de ICMS independentemente do CST:

```python
# XPath genérico que funciona com TODOS os CST
xpath = './/nfe:imposto/nfe:ICMS//nfe:vICMS'
```

**Suporta todos os grupos**:
- ICMS00 (ID N02) - Tributada integralmente
- ICMS10 (ID N03) - Tributada com ST
- ICMS20 (ID N04) - Com redução de BC
- ICMS30 (ID N05) - Isenta com ST
- ICMS40/41/50 (ID N06) - Isenta/Não tributada/Suspensão
- ICMS51 (ID N07) - Diferimento
- ICMS60 (ID N08) - ICMS ST retido anteriormente
- ICMS70 (ID N09) - Com redução e ST
- ICMS90 (ID N10) - Outros
- ICMSSN101, 102, 201, 202, 500, 900 - Simples Nacional

### Extração de DIFAL (Grupo NA)

O grupo **ICMSUFDest** é extraído diretamente:

```python
xpath = './/nfe:imposto/nfe:ICMSUFDest/nfe:pICMSInterPart'
```

**Importante**: Este grupo só existe em:
- Operações interestaduais
- Destinadas a consumidor final não contribuinte
- A partir de 2016 (NF-e 4.00)

### Conversão de Tipos

Todos os campos numéricos são convertidos para `float`:

```python
numeric_fields = [
    'Quantidade Comercial',
    'Valor Unitário',
    'Valor Total Item',
    'Base Cálculo ICMS',
    'Alíquota ICMS',
    'Valor ICMS',
    # ... todos os valores monetários e percentuais
]

for field in numeric_fields:
    df[field] = pd.to_numeric(df[field], errors='coerce').fillna(0.0)
```

**Valores ausentes** = `0.0` (nunca `None` ou `NaN`)

---

## ⚠️ Avisos Importantes

### 1. Granularidade Alterada

**ANTES** (v1.0):
- 1 NF-e = 1 linha no resultado
- Dados consolidados por nota

**AGORA** (v2.0):
- 1 NF-e com 5 itens = 5 linhas no resultado
- Dados detalhados por produto

### 2. Impacto em Processos Existentes

Se você tinha rotinas que dependiam de "1 linha = 1 NF-e", será necessário:

**No Excel**:
```excel
=SUMIF(A:A, "ChaveAcesso", D:D)  # Agregar por NF-e
=UNIQUE(A:A)                      # Listar NF-e únicas
```

**No Python/Pandas**:
```python
# Agregar por NF-e
df_nfe = df.drop_duplicates(subset='Chave de Acesso')
total_por_nfe = df.groupby('Chave de Acesso')['Valor Total Item'].sum()
```

### 3. Campo Crítico: Percentual Partilha ICMS (ID NA11)

O campo **pICMSInterPart** é **OBRIGATÓRIO** quando há DIFAL.

**Valores válidos em 2025**:
- Operações em 2024-2025: `100.0` (100% para UF de destino)

**Rejeição 699**: Ocorre quando este campo está ausente ou incorreto em operações com DIFAL.

---

## 📊 Exemplos de Uso

### Caso 1: Controle de Estoque

**Objetivo**: Extrair produtos vendidos com quantidades.

**Campos necessários**:
- Chave de Acesso
- Data e Hora de Emissão
- Cód. Produto
- Descrição do Produto
- Quantidade Comercial
- Unidade Comercial

**Resultado**:
```
Chave          | Data       | Cód.  | Produto   | Qtd | Un
35240...       | 2024-01-15 | 001   | NOTEBOOK  | 2.0 | UN
35240...       | 2024-01-15 | 002   | MOUSE     | 5.0 | UN
```

### Caso 2: Análise Tributária

**Objetivo**: Calcular carga tributária por produto.

**Campos necessários**:
- Número da NF
- Cód. Produto
- Descrição do Produto
- Valor Total Item
- Base Cálculo ICMS
- Alíquota ICMS
- Valor ICMS
- Valor IPI
- Valor PIS
- Valor COFINS

**Análise**:
```python
# Carga tributária total
df['Impostos'] = df['Valor ICMS'] + df['Valor IPI'] + df['Valor PIS'] + df['Valor COFINS']
df['Carga %'] = (df['Impostos'] / df['Valor Total Item'] * 100).round(2)
```

### Caso 3: Auditoria DIFAL

**Objetivo**: Validar cálculo de DIFAL em operações interestaduais.

**Campos necessários**:
- Chave de Acesso
- Número da NF
- Cód. Produto
- Descrição do Produto
- Valor Total Item
- BC ICMS UF Destino
- Alíquota Interna UF Destino
- Alíquota Interestadual
- **Percentual Partilha ICMS** ⚠️
- Valor ICMS UF Destino
- Valor ICMS UF Remetente

**Validações**:
```python
# 1. Percentual Partilha deve ser 100% em 2024-2025
assert df['Percentual Partilha ICMS'].unique() == [100.0]

# 2. ICMS Dest + ICMS Rem = DIFAL total
df['DIFAL Total'] = df['Valor ICMS UF Destino'] + df['Valor ICMS UF Remetente']
```

---

## 🐛 Troubleshooting

### Problema 1: "Nenhum dado foi extraído"

**Causas**:
- Nenhum campo selecionado
- XML corrompido
- Namespace incorreto (muito raro)

**Solução**:
1. Marque ao menos os campos essenciais (marcados por padrão)
2. Valide XML em ferramenta externa
3. Verifique se o arquivo é NF-e (modelo 55) ou NFC-e (modelo 65)

### Problema 2: Valores aparecem como texto no Excel

**Causa**: Separador decimal incorreto no sistema.

**Solução**:
- Use download **XLSX** (não CSV)
- Configure Excel: Arquivo → Opções → Avançado → Separador decimal = "."

### Problema 3: DIFAL não aparece

**Causa**: A NF-e não possui operação interestadual para consumidor final.

**Verificação**:
```python
# Contar NF-e com DIFAL
nfe_com_difal = df[df['Valor ICMS UF Destino'] > 0]['Chave de Acesso'].nunique()
print(f"{nfe_com_difal} NF-e(s) com DIFAL")
```

### Problema 4: Dashboard não funciona

**Causa**: Campos necessários não foram selecionados.

**Solução**: Marque estes campos mínimos:
- Chave de Acesso ou Número da NF
- Data e Hora de Emissão
- Valor Total da NF
- Descrição do Produto
- Quantidade Comercial

---

## 📞 Suporte

**TRR Contabilidade**

- 🌐 Website: [trrcontabil.com](https://trrcontabil.com)
- 📷 Instagram: [@trr_contabilidade](https://www.instagram.com/trr_contabilidade/)
- 📞 WhatsApp: [(91) 99241-2788](https://wa.me/5591992412788)

---

## 📝 Changelog

### v2.0.0 (Versão Final) - 16/10/2025

**Novo**:
- ✅ Conformidade total com leiaute oficial NT 2025.001
- ✅ Mapeamento por IDs oficiais (A01, B01, C01, etc.)
- ✅ Granularidade alterada para nível de item (det - ID H01)
- ✅ Novos campos: Código EAN, Unidade Comercial, Nome Fantasia
- ✅ Grupo ICMSUFDest (DIFAL) completo - IDs NA01-NA19
- ✅ Extração genérica de ICMS (todos os CST)
- ✅ Extração de IPI, PIS, COFINS
- ✅ Conversão automática de tipos numéricos
- ✅ Valores padrão: 0.0 para campos numéricos ausentes
- ✅ Interface com IDs do leiaute nos labels
- ✅ Tratamento robusto de erros

**Corrigido**:
- ✅ Namespace garantido em todas as buscas
- ✅ XPath genérico para impostos
- ✅ Extração de FCP (Fundo de Combate à Pobreza)

### v1.0.0 - Versão Anterior
- Granularidade por NF-e
- Campos básicos de produto
- DIFAL parcialmente implementado

---

## 📚 Referências

1. **Manual Oficial**: [Leiaute da NF-e](http://moc.sped.fazenda.pr.gov.br/Leiaute.html)
2. **Portal Nacional NF-e**: [www.nfe.fazenda.gov.br](http://www.nfe.fazenda.gov.br)
3. **Nota Técnica**: NT 2025.001 v.1.02 (02/09/2025)
4. **Schema XSD**: Versão 4.00

---

## ⚖️ Licença

Sistema desenvolvido por **TRR Contabilidade** para uso interno e de clientes.

---

**Última atualização**: 16/10/2025  
**Versão**: 2.0.0 Final  
**Desenvolvido com**: Python 3.8+ | Streamlit | lxml | pandas