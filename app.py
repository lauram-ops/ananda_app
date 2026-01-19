import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ananda Kino | Cotizador Residencial", page_icon="🏠", layout="wide")

# --- ESTILOS VISUALES PREMIUM ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #F9FCFF 0%, #FFFFFF 100%); }
    h1, h2, h3, .metric-label { color: #004e92 !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Tarjetas de Métricas */
    .metric-card { 
        background: white; padding: 25px; border-radius: 15px; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); text-align: center; border: 1px solid #edf2f7; 
    }
    .big-number { font-size: 30px; font-weight: 800; color: #004e92; }
    .price-tag { font-size: 36px; font-weight: 900; color: #004e92; }
    .future-number { font-size: 28px; font-weight: 800; color: #ffc107; }
    
    /* Botones */
    .stButton>button { background-color: #004e92; color: white; border-radius: 8px; font-weight: bold; height: 50px; }
    .stButton>button:hover { background-color: #003366; }
    
    /* Caja de Amenidades */
    .amenity-box { background-color: #f0f7ff; padding: 10px; border-radius: 8px; color: #004e92; font-weight: 600; text-align: center; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    file_name = "Lista de Precios, Planes Pago y descuentos autorizados 15 Octubre 2025.xlsx - Lista de Precios.csv"
    try:
        df = pd.read_csv(file_name)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    except:
        return pd.DataFrame({
            'lote': range(1, 45),
            'm2': [200 + (i*2) for i in range(44)],
            'm2_construccion': [160] * 44,
            'precio_lista_1': [900000 + (i*10000) for i in range(44)]
        })

df_raw = load_data()

# --- 2. SIDEBAR (CONFIGURACIÓN DE VENTA) ---
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.header("🏠 Ananda Residencial")

st.sidebar.header("1. Selección de Propiedad")

# Listas
lista_seleccionada = st.sidebar.selectbox("Lista de Precio Vigente:", range(1, 11), index=0)

# Lote
lote_label = st.sidebar.selectbox("Lote a Cotizar:", df_raw['lote'])
row_lote = df_raw[df_raw['lote'] == lote_label].iloc[0]

# Datos Base
m2_construccion_default = float(row_lote.get('m2_construccion', 180))
m2_terreno = float(row_lote.get('m2', 200))

# Precio Base Terreno
cols_precio = [c for c in df_raw.columns if 'precio' in c or 'valor' in c]
col_base = cols_precio[0] if cols_precio else 'precio_lista_1'
precio_base_lista1 = float(row_lote.get(col_base, 900000))

# Cálculo Incremento Lista
incremento_pct = 0.03 # 3% entre listas
precio_terreno_actual = precio_base_lista1 * (1 + (incremento_pct * (lista_seleccionada - 1)))
precio_terreno_futuro = precio_base_lista1 * (1 + (incremento_pct * 9)) # Lista 10

st.sidebar.markdown("---")
st.sidebar.header("2. Modelo de Construcción")
st.sidebar.info("La casa se entrega construida (Llave en mano).")

# Costos Construcción (Componente del precio)
costo_m2_const = st.sidebar.number_input("Valor Construcción por m²:", value=14500, step=500)
m2_const_final = st.sidebar.number_input("M² de Construcción (Modelo):", value=int(m2_construccion_default))
valor_construccion = m2_const_final * costo_m2_const

# PRECIO TOTAL DE VENTA (La suma de los dos componentes)
precio_preventa_total = precio_terreno_actual + valor_construccion
precio_final_mercado = precio_terreno_futuro + valor_construccion # Lo que costará terminada/Lista 10
plusvalia = precio_final_mercado - precio_preventa_total

# --- 3. INTERFAZ PRINCIPAL ---

# Encabezado
st.title(f"Residencia Ananda | Lote {lote_label}")
st.markdown(f"**Estado:** Preventa (Lista {lista_seleccionada}) | **Entrega:** Casa Terminada")

# TARJETAS DE PRECIO (NUEVO ENFOQUE)
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Precio Preventa (HOY)</div>
        <div class="price-tag">${precio_preventa_total:,.0f}</div>
        <div style="font-size:14px; color:grey; margin-top:5px">Incluye Terreno + Casa</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="metric-card" style="border: 2px solid #ffc107; background:#fffdf5">
        <div class="metric-label">Valor Final (Lista 10)</div>
        <div class="future-number">${precio_final_mercado:,.0f}</div>
        <div style="font-size:14px; color:#b58900; margin-top:5px">Precio al terminar preventa</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="metric-card" style="background:#f0fff4; border: 2px solid #28a745;">
        <div class="metric-label" style="color:#28a745!important">Tu Plusvalía Garantizada</div>
        <div class="big-number" style="color:#28a745">+${plusvalia:,.0f}</div>
        <div style="font-size:14px; color:#28a745; font-weight:bold; margin-top:5px">Ganancia por comprar en obra</div>
    </div>""", unsafe_allow_html=True)

# DETALLES DEL PRODUCTO
st.markdown("---")
col_info, col_graph = st.columns([1, 1])

with col_info:
    st.subheader("🏡 Tu Casa Incluye:")
    st.markdown("""
    **Modelo Residencial 3 Recámaras**
    * Construcción: **{:.0f} m²**
    * Terreno: **{:.0f} m²**
    
    **Equipamiento Entregado:**
    ✅ Cocina integral con barra y carpintería  
    ✅ Estufa eléctrica y campana  
    ✅ Closets completos en recámaras  
    ✅ Minisplits (Preparación y equipos)  
    ✅ Pisos, canceles y muebles de baño  
    ✅ Cochera doble y Jardín
    """.format(m2_const_final, m2_terreno))

with col_graph:
    st.subheader("📊 Comparativa de Inversión")
    competencia_depto = 4500000 # Precio promedio depto competencia
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Depto Competencia (110m²)', 'Tu Casa Ananda (Terminada)'],
        y=[competencia_depto, precio_preventa_total],
        marker_color=['#a0aec0', '#004e92'],
        text=[f"${competencia_depto/1000000:.1f}M", f"${precio_preventa_total/1000000:.1f}M"],
        textposition='auto'
    ))
    fig.update_layout(height=280, title="Mismo Presupuesto = Más Metros Cuadrados", margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

# --- 4. GENERADOR DE PDF (COTIZACIÓN FORMAL) ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 78, 146) # Azul Ananda
        self.rect(0, 0, 210, 35, 'F')
        try:
            self.image('logo.png', 10, 6, 30)
        except:
            pass
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, '', 0, 1)
        self.cell(0, 10, 'COTIZACIÓN RESIDENCIAL', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Ananda Kino - Precios de preventa sujetos a cambio sin previo aviso.', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    # Título Propiedad
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, f'Propiedad: Casa en Lote {lote_label}', 0, 1)
    
    # Ficha Técnica
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(50)
    pdf.cell(0, 8, f'Superficie Terreno: {m2_terreno} m2  |  Construcción: {m2_const_final} m2', 0, 1)
    pdf.ln(5)

    # Tabla de Precios
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(100, 10, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 10, 'Valor', 1, 1, 'R', 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(100, 10, f'Valor Terreno (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 10, f'${precio_terreno_actual:,.2f}', 1, 1, 'R')
    
    pdf.cell(100, 10, f'Valor Construcción (Casa Equipada)', 1, 0)
    pdf.cell(60, 10, f'${valor_construccion:,.2f}', 1, 1, 'R')
    
    # Total
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(100, 15, 'PRECIO TOTAL PREVENTA:', 1, 0)
    pdf.cell(60, 15, f'${precio_preventa_total:,.2f}', 1, 1, 'R')
    
    # Nota de Plusvalía
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 11)
    pdf.set_text_color(100)
    pdf.multi_cell(0, 8, f'Nota: Al adquirir en esta etapa, obtienes precio preferencial. El valor proyectado a la entrega (Lista 10) es ${precio_final_mercado:,.2f}, representando una plusvalia inmediata de ${plusvalia:,.2f}.')
    
    # Amenidades
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 10, 'Incluye acceso a Amenidades:', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, '- Alberca y Terraza Club\n- Andador y Juegos Infantiles\n- Pet Park y Areas Verdes\n- Seguridad 24/7 (Cerrada Exclusiva)')

    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
col_d1, col_d2 = st.columns([3,1])
with col_d1:
    st.markdown("##### 📄 Descargar Cotización Formal")
    st.caption("Genera un PDF listo para enviar al cliente por WhatsApp.")
with col_d2:
    try:
        pdf_bytes = create_pdf()
        st.download_button(
            label="DESCARGAR PDF",
            data=pdf_bytes,
            file_name=f"Cotizacion_Casa_Ananda_{lote_label}.pdf",
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Error generando PDF: {e}")
        