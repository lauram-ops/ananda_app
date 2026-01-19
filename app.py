import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from fpdf import FPDF
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ananda Kino | Master Cotizador", page_icon="🌊", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #F9FCFF 0%, #FFFFFF 100%); }
    h1, h2, h3, .metric-label { color: #004e92 !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Tarjetas */
    .metric-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center; border: 1px solid #e1e5e8; height: 100%;}
    .big-number { font-size: 28px; font-weight: 800; color: #004e92; }
    .future-number { font-size: 28px; font-weight: 800; color: #ffc107; }
    
    /* Contador */
    .countdown-box { background: #004e92; color: white; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,78,146,0.3); }
    .countdown-number { font-size: 32px; font-weight: 900; }
    .countdown-label { font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }

    /* Tabla Comparativa */
    .comp-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
    .comp-table th { background-color: #004e92; color: white; padding: 12px; text-align: left; }
    .comp-table td { border-bottom: 1px solid #ddd; padding: 10px; text-align: left; color: #333; }
    .highlight { background-color: #e3f2fd; font-weight: bold; color: #004e92; }
    
    .stButton>button { background-color: #004e92; color: white; font-weight: bold; height: 50px; width: 100%; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN LIMPIEZA ---
def clean_currency(val):
    if pd.isna(val): return 0.0
    s = str(val).replace('$', '').replace(',', '').replace(' ', '')
    try: return float(s)
    except: return 0.0

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    file_name = "precios.csv"
    try:
        df = pd.read_csv(file_name)
        cols_str = "".join([str(c).lower() for c in df.columns])
        if "lote" not in cols_str: df = pd.read_csv(file_name, header=1)
        
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '').str.replace('(', '').str.replace(')', '')
        
        col_lote = None
        for col in df.columns:
            if 'lote' in col or 'unidad' in col:
                col_lote = col
                break
        
        if col_lote:
            df.rename(columns={col_lote: 'lote'}, inplace=True)
            df['lote'] = pd.to_numeric(df['lote'], errors='coerce')
            df = df.dropna(subset=['lote'])
            df['lote'] = df['lote'].astype(int)
            df = df[(df['lote'] >= 1) & (df['lote'] <= 44)]
            df = df.sort_values('lote')
            
            # Status
            col_status = next((c for c in df.columns if 'cliente' in c or 'estatus' in c), None)
            if col_status:
                df['status'] = df[col_status].apply(lambda x: 'Vendido' if pd.notnull(x) and str(x).strip() not in ['', 'nan'] else 'Disponible')
            else:
                df['status'] = 'Disponible'
            return df
        return None
    except: return None

df_raw = load_data()
if df_raw is None:
    st.error("⚠️ Usando datos base.")
    df_raw = pd.DataFrame({'lote': range(1, 45), 'status': ['Disponible']*44})

# --- 2. SIDEBAR ---
try: st.sidebar.image("logo.png", use_column_width=True)
except: st.sidebar.header("🏠 Ananda Residencial")

st.sidebar.header("1. Configuración")
lista_seleccionada = st.sidebar.selectbox("Lista Vigente:", range(1, 11), index=0)

# Selector Lote
opciones_lotes = df_raw.apply(lambda x: f"Lote {x['lote']} ({x['status']})", axis=1).tolist()
lote_str_selec = st.sidebar.selectbox("Seleccionar Lote:", opciones_lotes)
num_lote_selec = int(lote_str_selec.split(' ')[1])
row_lote = df_raw[df_raw['lote'] == num_lote_selec].iloc[0]

# Datos Lote
col_m2 = next((c for c in df_raw.columns if 'm2' in c and 'privativo' in c), None) or next((c for c in df_raw.columns if 'm2' in c), None)
m2_terreno = clean_currency(row_lote.get(col_m2, 216.0)) if col_m2 else 216.0

col_const = next((c for c in df_raw.columns if 'construccion' in c and 'total' in c), None)
m2_construccion = clean_currency(row_lote.get(col_const, 128.8)) if col_const else 128.8

# Precio Lista
col_precio_lista = next((c for c in df_raw.columns if f"lista_{lista_seleccionada}" in c), None)
if col_precio_lista:
    precio_lista_actual = clean_currency(row_lote[col_precio_lista])
else:
    col_l1 = next((c for c in df_raw.columns if 'lista_1' in c), None)
    base = clean_currency(row_lote[col_l1]) if col_l1 else 3300000.0
    precio_lista_actual = base * (1 + 0.03 * (lista_seleccionada - 1))

# Precio Futuro
col_l10 = next((c for c in df_raw.columns if 'lista_10' in c), None)
precio_final_mercado = clean_currency(row_lote[col_l10]) if col_l10 else precio_lista_actual * 1.30
plusvalia = precio_final_mercado - precio_lista_actual

st.sidebar.markdown("---")
st.sidebar.info(f"📋 **Lote {num_lote_selec}:**\n- Terreno: {m2_terreno:.0f} m²\n- Construcción: {m2_construccion:.0f} m²")

# --- 3. PANEL SUPERIOR (CONTADOR) ---
col_logo, col_title = st.columns([1, 4])
with col_title:
    st.title(f"Residencia Ananda | Lote {num_lote_selec}")
    if "Vendido" in lote_str_selec: st.warning("⛔ LOTE VENDIDO")

# CONTADOR REGRESIVO
entrega = date(2027, 2, 28)
hoy = date.today()
dias_restantes = (entrega - hoy).days

st.markdown(f"""
<div class="countdown-box">
    <div class="countdown-label">Tiempo para Entrega (Feb 2027) - Plusvalía en Proceso</div>
    <div class="countdown-number">{dias_restantes} Días</div>
</div>
""", unsafe_allow_html=True)

# TARJETAS
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Precio Preventa (HOY)</div>
        <div class="big-number">${precio_lista_actual:,.0f}</div>
        <small>Casa Independiente + Terreno</small>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card" style="border: 2px solid #ffc107; background:#fffdf5">
        <div class="metric-label">Valor Entrega (Lista 10)</div>
        <div class="future-number">${precio_final_mercado:,.0f}</div>
        <small>Feb 2027</small>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card" style="background:#f0fff4; border: 2px solid #28a745;">
        <div class="metric-label" style="color:#28a745!important">Plusvalía Ganada</div>
        <div class="big-number" style="color:#28a745">+${plusvalia:,.0f}</div>
        <small>Tu ganancia por comprar hoy</small>
    </div>""", unsafe_allow_html=True)

# --- 4. COMPARATIVA VISUAL (MEJORADA) ---
st.markdown("---")
st.header("🏆 El Reto del Metro Cuadrado")
st.caption("Comparativa real basada en precios de mercado actuales (PPK Lantana, HAX, Azaluma).")

# PREPARACIÓN DE DATOS COMPETENCIA
precio_m2_ananda = precio_lista_actual / m2_construccion if m2_construccion > 0 else 0

# Datos aproximados de los PDFs
data_comp = [
    {"Proyecto": "ANANDA (Casa)", "Precio": precio_lista_actual, "M2": m2_construccion, "Tipo": "Casa", "Privacidad": "Alta"},
    {"Proyecto": "Punta Península (Lantana)", "Precio": 4850000, "M2": 100, "Tipo": "Depto", "Privacidad": "Baja"},
    {"Proyecto": "HAX (Condo)", "Precio": 3600000, "M2": 75, "Tipo": "Depto", "Privacidad": "Baja"},
    {"Proyecto": "Azaluma", "Precio": 4100000, "M2": 85, "Tipo": "Depto", "Privacidad": "Baja"},
]
df_comp = pd.DataFrame(data_comp)
df_comp['Precio_M2'] = df_comp['Precio'] / df_comp['M2']

col_scatter, col_bar = st.columns([2, 1])

with col_scatter:
    st.subheader("Mapa de Valor: Tamaño vs. Precio")
    # Gráfica de Dispersión (Scatter)
    fig_sc = px.scatter(df_comp, x="Precio", y="M2", 
                     color="Tipo", size="M2", 
                     text="Proyecto",
                     color_discrete_map={"Casa": "#004e92", "Depto": "#ef553b"},
                     title="Busca la esquina superior izquierda (Más M² por menos $)")
    
    fig_sc.update_traces(textposition='top center', marker=dict(size=25, line=dict(width=2, color='DarkSlateGrey')))
    fig_sc.add_shape(type="rect", x0=precio_lista_actual*0.9, y0=m2_construccion*0.9, x1=precio_lista_actual*1.1, y1=m2_construccion*1.1,
                     line=dict(color="Green"), fillcolor="rgba(0,255,0,0.1)")
    fig_sc.update_layout(height=400, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_sc, use_container_width=True)

with col_bar:
    st.subheader("Precio Real por M²")
    # Bar Chart ordenado
    df_bar = df_comp.sort_values('Precio_M2')
    fig_bar = go.Figure(go.Bar(
        x=df_bar['Proyecto'], y=df_bar['Precio_M2'],
        marker_color=['#28a745' if p == 'ANANDA (Casa)' else '#d62728' for p in df_bar['Proyecto']],
        text=[f"${x:,.0f}" for x in df_bar['Precio_M2']],
        textposition='auto'
    ))
    fig_bar.update_layout(height=400, title="", plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig_bar, use_container_width=True)

# COMPARATIVA DE ESTILO DE VIDA (TEXTO/ICONOS)
st.markdown("---")
col_vis1, col_vis2 = st.columns(2)

with col_vis1:
    st.subheader("🏢 Vivir en Departamento")
    st.markdown("""
    * ❌ **Vecino Arriba:** Ruidos de pasos y muebles.
    * ❌ **Vecino Abajo:** Quejas si tus hijos corren.
    * ❌ **Vecino al Lado:** Pared con pared (ruido TV).
    * ❌ **Cochera:** Generalmente común o lejos.
    * ⚠️ **Cuotas:** Mantenimiento de elevadores y edificios es alto.
    """)

with col_vis2:
    st.subheader("🏡 Vivir en ANANDA (Casa)")
    st.markdown("""
    * ✅ **Cielo Abierto:** Nadie arriba de ti.
    * ✅ **Tierra Firme:** Nadie abajo de ti.
    * ✅ **Muros Separados:** Pasillos laterales (sin pared compartida).
    * ✅ **Cochera Privada:** Frente a tu puerta.
    * ✅ **Plusvalía:** Eres dueño del **terreno**, no solo del aire.
    """)

# --- 5. RENTAS ---
st.markdown("---")
st.header("📈 Negocio Patrimonial")
col_r1, col_r2 = st.columns([1, 2])
with col_r1:
    tarifa = st.number_input("Tarifa Noche:", value=4500, step=500)
    ocupacion = st.slider("Ocupación %:", 30, 70, 45) / 100
    mto = st.number_input("Mantenimiento Mensual:", value=2000)
with col_r2:
    ingreso = tarifa * 365 * ocupacion
    gastos = (ingreso * 0.25) + (mto * 12)
    neto = ingreso - gastos
    st.metric("Ingreso Neto Anual", f"${neto:,.0f}")
    st.progress(min(100, int((neto/precio_lista_actual)*1000))) 
    st.caption("Barra de Rendimiento vs Inversión")

# --- 6. PDF ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 78, 146)
        self.rect(0, 0, 210, 35, 'F')
        try: self.image('logo.png', 10, 6, 30)
        except: pass
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, '', 0, 1)
        self.cell(0, 10, 'COTIZACIÓN & ANÁLISIS', 0, 1, 'R')
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
    pdf.cell(0, 10, f'Propiedad: Casa en Lote {num_lote_selec}', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f'Terreno: {m2_terreno:.2f} m2 | Construcción: {m2_construccion:.2f} m2', 0, 1)
    pdf.ln(5)
    
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(100, 10, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 10, 'Valor', 1, 1, 'R', 1)
    pdf.cell(100, 10, f'Precio Preventa (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 10, f'${precio_lista_actual:,.2f}', 1, 1, 'R')
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Analisis de Competencia (M2)', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(100, 10, 'Precio M2 ANANDA:', 1, 0)
    pdf.cell(60, 10, f'${precio_m2_ananda:,.2f}', 1, 1, 'R')
    pdf.cell(100, 10, 'Promedio M2 Condos:', 1, 0)
    pdf.cell(60, 10, f'$46,000.00', 1, 1, 'R') # Promedio mercado

    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar PDF")
with c_down2:
    try: st.download_button("DESCARGAR PDF", create_pdf(), file_name=f"Cotizacion_{num_lote_selec}.pdf")
    except: st.error("Error PDF")