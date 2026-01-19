import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ananda Kino | Cotizador PRO", page_icon="🏠", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #F9FCFF 0%, #FFFFFF 100%); }
    h1, h2, h3, .metric-label { color: #004e92 !important; font-family: 'Helvetica Neue', sans-serif; }
    .metric-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center; border: 1px solid #e1e5e8; }
    .big-number { font-size: 28px; font-weight: 800; color: #004e92; }
    .future-number { font-size: 28px; font-weight: 800; color: #ffc107; }
    .stButton>button { background-color: #004e92; color: white; border-radius: 8px; width: 100%; height: 50px; font-weight: bold;}
    </style>
    """, unsafe_allow_html=True)

# --- 1. CARGA DE DATOS INTELIGENTE ---
@st.cache_data
def load_data():
    file_name = "precios.csv"
    
    # 1. Intentar cargar el archivo (Detectando separador , o ;)
    try:
        # Prueba con motor python para autodetectar separador
        df = pd.read_csv(file_name, sep=None, engine='python')
    except:
        # Si falla, devuelve Dummy y aviso
        return None, False

    # 2. Limpieza de nombres de columnas
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '').str.replace('°', '')
    
    # 3. BUSCADOR INTELIGENTE DE COLUMNAS (Mapeo)
    # Buscamos cuál columna es la del 'Lote'
    col_lote = None
    posibles_lote = ['lote', 'lotes', 'no_lote', 'num_lote', 'unidad', 'numero', 'id']
    for posible in posibles_lote:
        if posible in df.columns:
            col_lote = posible
            break
            
    # Si encontramos una variante, la renombramos a 'lote' para estandarizar
    if col_lote and col_lote != 'lote':
        df.rename(columns={col_lote: 'lote'}, inplace=True)
    
    # Si de plano no encontró nada parecido a lote, avisar
    if 'lote' not in df.columns:
        st.error(f"⚠️ ERROR DE FORMATO: No encuentro una columna que diga 'Lote'. Las columnas que veo son: {list(df.columns)}")
        return None, False

    return df, True

df_raw, archivo_cargado = load_data()

# --- SI FALLA LA CARGA, USAR DATOS DE RESPALDO PARA QUE NO TRUENE ---
if not archivo_cargado or df_raw is None:
    df_raw = pd.DataFrame({
        'lote': range(1, 45),
        'm2': [200 + (i*2) for i in range(44)],
        'm2_construccion': [160] * 44,
        'precio_lista_1': [900000 + (i*10000) for i in range(44)]
    })
    # Solo mostramos el error si el usuario NO es un visitante (opcional)
    # st.sidebar.warning("Usando datos simulados por error en CSV.")

# --- 2. SIDEBAR ---
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.header("🏠 Ananda Residencial")

st.sidebar.header("1. Configuración")

# Selectores
lista_seleccionada = st.sidebar.selectbox("Lista de Precio Vigente:", range(1, 11), index=0)
lote_label = st.sidebar.selectbox("Lote a Cotizar:", df_raw['lote'])
row_lote = df_raw[df_raw['lote'] == lote_label].iloc[0]

# --- LÓGICA DE PRECIOS ---
m2_terreno = float(row_lote.get('m2', 200))
m2_construccion_default = float(row_lote.get('m2_construccion', 180)) 

# Precio Base (Busca columna inteligente)
cols_precio = [c for c in df_raw.columns if 'precio' in c or 'valor' in c or 'lista_1' in c or 'total' in c]
if cols_precio:
    col_base = cols_precio[0]
    precio_base_lista1 = float(row_lote[col_base])
else:
    precio_base_lista1 = 900000.0

# Cálculo Incremento Lista (3% por lista)
incremento_pct = 0.03
precio_terreno_actual = precio_base_lista1 * (1 + (incremento_pct * (lista_seleccionada - 1)))
precio_terreno_futuro = precio_base_lista1 * (1 + (incremento_pct * 9)) # Lista 10

st.sidebar.markdown("---")
st.sidebar.header("2. Casa Terminada")
st.sidebar.caption("Se entrega residencia construida (Obra Civil + Acabados).")

costo_m2_const = st.sidebar.number_input("Valor Construcción por m²:", value=14500, step=500)
m2_const_final = st.sidebar.number_input("M² de Construcción:", value=int(m2_construccion_default))
valor_construccion = m2_const_final * costo_m2_const

# TOTALES
precio_preventa_total = precio_terreno_actual + valor_construccion
precio_final_mercado = precio_terreno_futuro + valor_construccion
plusvalia = precio_final_mercado - precio_preventa_total

# --- 3. PANEL PRINCIPAL ---
st.title(f"Residencia Ananda | Lote {lote_label}")
st.markdown(f"**Estado:** Preventa (Lista {lista_seleccionada}) | **Entrega:** Casa Terminada")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Precio Preventa (HOY)</div>
        <div class="big-number">${precio_preventa_total:,.0f}</div>
        <small>Terreno + Casa</small>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card" style="border: 2px solid #ffc107; background:#fffdf5">
        <div class="metric-label">Valor Final (Lista 10)</div>
        <div class="future-number">${precio_final_mercado:,.0f}</div>
        <small>Feb 2027</small>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card" style="background:#f0fff4; border: 2px solid #28a745;">
        <div class="metric-label" style="color:#28a745!important">Plusvalía Proyectada</div>
        <div class="big-number" style="color:#28a745">+${plusvalia:,.0f}</div>
        <small>Ganancia inmediata</small>
    </div>""", unsafe_allow_html=True)

# DETALLES
st.markdown("---")
col_det1, col_det2 = st.columns(2)
with col_det1:
    st.subheader("🏡 Ficha Técnica")
    st.markdown(f"""
    - **Terreno:** {m2_terreno} m²
    - **Construcción:** {m2_const_final} m²
    - **Modelo:** Residencial 3 Recámaras
    - **Incluye:** Cocina, Closets, Minisplits, Pisos.
    """)
with col_det2:
    st.subheader("🆚 Comparativa de Mercado")
    precio_m2_ananda = precio_preventa_total / m2_const_final
    precio_m2_competencia = 4500000 / 110
    st.markdown(f"""
    - **Competencia (Depto):** ${precio_m2_competencia:,.0f} / m²
    - **Ananda (Casa):** ${precio_m2_ananda:,.0f} / m²
    - **Ventaja:** Estás comprando **tierra y ladrillo** a mejor precio.
    """)

# --- 4. SECCIÓN RENTAS ---
st.markdown("---")
st.header("🏖️ Simulador de Negocio")
st.caption("Proyección estimada de ingresos por rentas vacacionales.")

r_col1, r_col2 = st.columns([1, 2])
with r_col1:
    tarifa = st.number_input("Tarifa Noche Promedio:", value=4500, step=500)
    ocupacion = st.slider("Ocupación Anual (%)", 20, 80, 40)
    gastos_op = st.slider("% Gastos Operativos:", 20, 40, 30)

with r_col2:
    noches = 365 * (ocupacion/100)
    ingreso_bruto = tarifa * noches
    gastos = ingreso_bruto * (gastos_op/100)
    neto = ingreso_bruto - gastos
    roi = (neto / precio_preventa_total) * 100
    
    st.success(f"💰 Flujo Neto Anual Estimado: **${neto:,.0f} MXN**")
    st.metric("ROI Anual (Cap Rate)", f"{roi:.1f}%")

# --- 5. PDF ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 78, 146)
        self.rect(0, 0, 210, 35, 'F')
        try: self.image('logo.png', 10, 6, 30)
        except: pass
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, '', 0, 1)
        self.cell(0, 10, 'COTIZACIÓN RESIDENCIAL', 0, 1, 'R')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Ananda Kino - Sujeto a cambios sin previo aviso.', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, f'Propiedad: Casa en Lote {lote_label}', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f'Terreno: {m2_terreno} m2 | Construcción: {m2_const_final} m2', 0, 1)
    pdf.ln(5)
    
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(100, 10, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 10, 'Valor', 1, 1, 'R', 1)
    
    pdf.cell(100, 10, f'Terreno (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 10, f'${precio_terreno_actual:,.2f}', 1, 1, 'R')
    pdf.cell(100, 10, 'Construcción (Casa Terminada)', 1, 0)
    pdf.cell(60, 10, f'${valor_construccion:,.2f}', 1, 1, 'R')
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(100, 15, 'TOTAL PREVENTA:', 1, 0)
    pdf.cell(60, 15, f'${precio_preventa_total:,.2f}', 1, 1, 'R')
    
    pdf.ln(10)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, f'Proyección de Negocio:\nEstimamos un flujo neto anual de ${neto:,.2f} con una ocupación del {ocupacion}%.')
    
    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1:
    st.markdown("##### 📄 Descargar Cotización")
with c_down2:
    try:
        st.download_button("DESCARGAR PDF", create_pdf(), file_name=f"Cotizacion_{lote_label}.pdf")
    except:
        st.error("Error al generar PDF")