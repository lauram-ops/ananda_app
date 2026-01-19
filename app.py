import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from fpdf import FPDF
from datetime import date
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ananda Kino | Super Cotizador", page_icon="🌊", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #F9FCFF 0%, #FFFFFF 100%); }
    h1, h2, h3, .metric-label { color: #004e92 !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Tarjetas */
    .metric-card { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center; border: 1px solid #e1e5e8; height: 100%; }
    .big-number { font-size: 24px; font-weight: 800; color: #004e92; }
    .highlight-number { font-size: 24px; font-weight: 800; color: #28a745; }
    
    /* Secciones */
    .section-header { border-bottom: 2px solid #004e92; margin-bottom: 20px; padding-bottom: 5px; color: #004e92; font-size: 22px; font-weight: bold; }
    .sub-section { background-color: white; padding: 20px; border-radius: 15px; margin-bottom: 20px; border: 1px solid #eee; }

    /* Tabla */
    .comp-table { width: 100%; border-collapse: collapse; font-size: 14px; }
    .comp-table th { background-color: #004e92; color: white; padding: 10px; text-align: center; }
    .comp-table td { border-bottom: 1px solid #ddd; padding: 8px; text-align: center; color: #333; }
    .feature-table td { text-align: left; padding: 10px; }
    .check { color: green; font-weight: bold; }
    
    /* Ficha Técnica */
    .specs-list { list-style-type: none; padding: 0; display: flex; flex-wrap: wrap; gap: 10px; }
    .specs-item { background: #e3f2fd; padding: 5px 12px; border-radius: 15px; font-size: 13px; font-weight: bold; color: #004e92; border: 1px solid #bbdefb; }

    .stButton>button { background-color: #004e92; color: white; font-weight: bold; width: 100%; border-radius: 8px; height: 50px;}
    </style>
    """, unsafe_allow_html=True)

# --- MATRIZ DE DESCUENTOS ---
TABLA_DESCUENTOS = {
    0: {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    1: {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    2: {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    3: {95: 0.105, 90: 0.095, 80: 0.085, 70: 0.075, 60: 0.065, 50: 0.055, 40: 0.045, 30: 0.035, 25: 0.025, 20: 0.020, 15: 0.015},
    4: {95: 0.100, 90: 0.090, 80: 0.080, 70: 0.070, 60: 0.060, 50: 0.050, 40: 0.040, 30: 0.030, 25: 0.020, 20: 0.015, 15: 0.010},
    5: {95: 0.095, 90: 0.085, 80: 0.075, 70: 0.065, 60: 0.055, 50: 0.045, 40: 0.035, 30: 0.025, 25: 0.015, 20: 0.010, 15: 0.005},
    6: {95: 0.090, 90: 0.080, 80: 0.070, 70: 0.060, 60: 0.050, 50: 0.040, 40: 0.030, 30: 0.020, 25: 0.010, 20: 0.005},
    7: {95: 0.085, 90: 0.075, 80: 0.065, 70: 0.055, 60: 0.045, 50: 0.035, 40: 0.025, 30: 0.015, 25: 0.005},
    8: {95: 0.080, 90: 0.070, 80: 0.060, 70: 0.050, 60: 0.040, 50: 0.030, 40: 0.020, 30: 0.010},
    9: {95: 0.075, 90: 0.065, 80: 0.055, 70: 0.045, 60: 0.035, 50: 0.025, 40: 0.015, 30: 0.005},
    10: {95: 0.070, 90: 0.060, 80: 0.050, 70: 0.040, 60: 0.030, 50: 0.020, 40: 0.010},
    11: {95: 0.0675, 90: 0.0575, 80: 0.0475, 70: 0.0375, 60: 0.0275, 50: 0.0175, 40: 0.0075},
    12: {95: 0.065, 90: 0.055, 80: 0.045, 70: 0.035, 60: 0.025, 50: 0.015, 40: 0.005},
    13: {95: 0.0625, 90: 0.0525, 80: 0.0425, 70: 0.0325, 60: 0.0225, 50: 0.0125, 40: 0.0025},
}

def obtener_descuento(plazo, enganche):
    if plazo not in TABLA_DESCUENTOS: return 0.0
    niveles = sorted(TABLA_DESCUENTOS[plazo].keys(), reverse=True)
    for n in niveles:
        if enganche >= n: return TABLA_DESCUENTOS[plazo][n]
    return 0.0

def clean_currency(val):
    if pd.isna(val): return 0.0
    s = str(val).replace('$', '').replace(',', '').replace(' ', '')
    try: return float(s)
    except: return 0.0

@st.cache_data
def load_data():
    file_name = "precios.csv"
    try:
        df = pd.read_csv(file_name)
        cols_str = "".join([str(c).lower() for c in df.columns])
        if "lote" not in cols_str: df = pd.read_csv(file_name, header=1)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '').str.replace('(', '').str.replace(')', '')
        col_lote = next((c for c in df.columns if 'lote' in c or 'unidad' in c), None)
        if col_lote:
            df.rename(columns={col_lote: 'lote'}, inplace=True)
            df['lote'] = pd.to_numeric(df['lote'], errors='coerce')
            df = df.dropna(subset=['lote'])
            df['lote'] = df['lote'].astype(int)
            df = df[(df['lote'] >= 1) & (df['lote'] <= 44)]
            df = df.sort_values('lote')
            col_status = next((c for c in df.columns if 'cliente' in c or 'estatus' in c), None)
            df['status'] = df[col_status].apply(lambda x: 'Vendido' if pd.notnull(x) and str(x).strip() not in ['', 'nan'] else 'Disponible') if col_status else 'Disponible'
            df.loc[(df['lote'] >= 11) & (df['lote'] <= 22), 'status'] = 'Vendido'
            return df
        return None
    except: return None

df_raw = load_data()
if df_raw is None: df_raw = pd.DataFrame({'lote': range(1, 45), 'status': ['Disponible']*44})

# ==============================================================================
# 🟦 BARRA LATERAL (MENU Y DATOS)
# ==============================================================================
try: st.sidebar.image("logo.png", use_column_width=True)
except: st.sidebar.header("🏠 Ananda Kino")

st.sidebar.markdown(f"**📅 {date.today().strftime('%d/%m/%Y')}**")
st.sidebar.header("👤 Datos del Cliente")
cliente_nombre = st.sidebar.text_input("Nombre Cliente:", value="")
asesor_nombre = st.sidebar.text_input("Nombre Asesor:", value="")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Propiedad")
lista_seleccionada = st.sidebar.selectbox("Lista de Precio:", range(1, 11), index=0)

opciones_lotes = df_raw.apply(lambda x: f"Lote {x['lote']} ({x['status']})", axis=1).tolist()
lote_str_selec = st.sidebar.selectbox("Seleccionar Lote:", opciones_lotes)
num_lote_selec = int(lote_str_selec.split(' ')[1])
row_lote = df_raw[df_raw['lote'] == num_lote_selec].iloc[0]

# Cálculo de Datos del Lote
col_m2 = next((c for c in df_raw.columns if 'm2' in c and 'privativo' in c), None) or next((c for c in df_raw.columns if 'm2' in c), None)
m2_terreno = clean_currency(row_lote.get(col_m2, 216.0)) if col_m2 else 216.0
col_const = next((c for c in df_raw.columns if 'construccion' in c and 'total' in c), None)
m2_construccion = clean_currency(row_lote.get(col_const, 128.8)) if col_const else 128.8

col_precio_lista = next((c for c in df_raw.columns if f"lista_{lista_seleccionada}" in c), None)
if col_precio_lista:
    precio_lista_base = clean_currency(row_lote[col_precio_lista])
else:
    col_l1 = next((c for c in df_raw.columns if 'lista_1' in c), None)
    base = clean_currency(row_lote[col_l1]) if col_l1 else 3300000.0
    precio_lista_base = base * (1 + 0.03 * (lista_seleccionada - 1))

# Valor Futuro
col_l10 = next((c for c in df_raw.columns if 'lista_10' in c), None)
precio_futuro = clean_currency(row_lote[col_l10]) if col_l10 else precio_lista_base * 1.30

# Mostrar en Sidebar
st.sidebar.info(f"""
**LOTE {num_lote_selec}**
\n📏 Terreno: {m2_terreno:.2f} m²
\n🏗️ Const: {m2_construccion:.2f} m²
""")

# ==============================================================================
# 📄 CUERPO PRINCIPAL (5 SECCIONES)
# ==============================================================================
st.title(f"Residencia Ananda | Lote {num_lote_selec}")
if "Vendido" in lote_str_selec: st.warning("⛔ ESTE LOTE YA ESTÁ VENDIDO")

# --- SECCIÓN 1: ESPECIFICACIONES ---
st.markdown('<div class="section-header">1. Especificaciones de la Residencia</div>', unsafe_allow_html=True)
st.markdown("""
<div class="sub-section">
    <ul class="specs-list">
        <li class="specs-item">🛏️ 3 Recámaras</li>
        <li class="specs-item">🚿 2.5 Baños</li>
        <li class="specs-item">🚗 Cochera Doble</li>
        <li class="specs-item">🍳 Cocina con Barra</li>
        <li class="specs-item">👕 Closets</li>
        <li class="specs-item">🪟 Cancelería</li>
        <li class="specs-item">✨ Pisos Incluidos</li>
    </ul>
    <br>
    <small><i>*Modelo de casa independiente con terreno propio.</i></small>
</div>
""", unsafe_allow_html=True)

# --- SECCIÓN 2: COMPARATIVO ---
st.markdown('<div class="section-header">2. Ananda vs El Mercado</div>', unsafe_allow_html=True)
precio_m2_ananda = precio_lista_base / m2_construccion if m2_construccion > 0 else 0
data_comp = [
    {"Proyecto": "ANANDA", "Precio": precio_lista_base, "M2": m2_construccion, "Tipo": "Casa", "PrecioM2": precio_m2_ananda},
    {"Proyecto": "Punta Península", "Precio": 4850000, "M2": 100, "Tipo": "Depto", "PrecioM2": 48500},
    {"Proyecto": "HAX", "Precio": 3600000, "M2": 70, "Tipo": "Depto", "PrecioM2": 51428},
    {"Proyecto": "Azaluma", "Precio": 4100000, "M2": 85, "Tipo": "Depto", "PrecioM2": 48235}
]
df_comp = pd.DataFrame(data_comp)

c2a, c2b = st.columns([1, 1])
with c2a:
    st.markdown(f"#### Tu Precio M²: **${precio_m2_ananda:,.0f}**")
    st.markdown("""
    <table class="comp-table feature-table">
        <tr><th>Ventajas Ananda</th></tr>
        <tr><td><span class='check'>✔</span> Precio por M² más bajo</td></tr>
        <tr><td><span class='check'>✔</span> Privacidad (Sin vecinos arriba/abajo)</td></tr>
        <tr><td><span class='check'>✔</span> Cochera Doble</td></tr>
        <tr><td><span class='check'>✔</span> Mantenimiento Bajo</td></tr>
        <tr><td><span class='check'>✔</span> Dueño de Tierra + Casa</td></tr>
    </table>
    """, unsafe_allow_html=True)
with c2b:
    fig_bar = go.Figure(go.Bar(
        x=df_comp.sort_values('PrecioM2')['Proyecto'], 
        y=df_comp.sort_values('PrecioM2')['PrecioM2'],
        marker_color=['#28a745' if 'ANANDA' in p else '#ef553b' for p in df_comp.sort_values('PrecioM2')['Proyecto']],
        text=[f"${x:,.0f}" for x in df_comp.sort_values('PrecioM2')['PrecioM2']],
        textposition='auto'
    ))
    fig_bar.update_layout(height=250, margin=dict(t=10,b=10), yaxis_title="$/m2")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- SECCIÓN 3: PLUSVALÍA ---
st.markdown('<div class="section-header">3. Proyección de Plusvalía</div>', unsafe_allow_html=True)
years = range(2027, 2033)
val_prop = precio_futuro # Inicia en valor de entrega
data_plus = []
for y in years:
    data_plus.append({"Año": y, "Valor": val_prop})
    val_prop *= 1.08 # 8% anual

df_plus = pd.DataFrame(data_plus)
c3a, c3b = st.columns([2, 1])
with c3a:
    fig_area = px.area(df_plus, x="Año", y="Valor", title="Crecimiento de Valor (8% Anual)")
    fig_area.update_traces(line_color='#004e92')
    st.plotly_chart(fig_area, use_container_width=True)
with c3b:
    st.markdown(f"""
    <div class="metric-card">
        <div>Valor Entrega (2027)</div>
        <div class="big-number">${precio_futuro:,.0f}</div>
    </div>
    <br>
    <div class="metric-card" style="border: 2px solid #28a745;">
        <div>Valor Proyectado (2032)</div>
        <div class="highlight-number">${data_plus[-1]['Valor']:,.0f}</div>
    </div>
    """, unsafe_allow_html=True)

# --- SECCIÓN 4: RENTAS ---
st.markdown('<div class="section-header">4. Simulador de Rentas</div>', unsafe_allow_html=True)
c4a, c4b = st.columns([1, 2])
with c4a:
    tarifa = st.number_input("Tarifa Noche:", value=4500, step=500)
    ocupacion = st.slider("Ocupación %:", 20, 80, 45) / 100
with c4b:
    ingreso = tarifa * 365 * ocupacion
    gastos = ingreso * 0.30 # 30% estimado gastos
    neto = ingreso - gastos
    roi = (neto / precio_lista_base) * 100
    st.metric("Utilidad Neta Anual (Estimada)", f"${neto:,.0f}", delta=f"ROI: {roi:.1f}%")

# --- SECCIÓN 5: COTIZADOR DE PAGOS (APP 2 INTEGRADA) ---
st.markdown('<div class="section-header">5. Plan de Pagos y Descuentos</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-section">', unsafe_allow_html=True)

col_pay_1, col_pay_2 = st.columns([1, 2])

with col_pay_1:
    st.markdown("#### Configura tu Plan")
    enganche_pct = st.select_slider("% Enganche:", options=[15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95], value=30)
    plazo_meses = st.selectbox("Plazo Enganche (Meses):", [0] + list(range(1, 14)), index=12)

# CÁLCULOS COTIZADOR
descuento_pct = obtener_descuento(plazo_meses, enganche_pct)
monto_descuento = precio_lista_base * descuento_pct
precio_cierre = precio_lista_base - monto_descuento
monto_enganche = precio_cierre * (enganche_pct / 100.0)
saldo_final = precio_cierre - monto_enganche
mensualidad = monto_enganche / plazo_meses if plazo_meses > 0 else 0

with col_pay_2:
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Precio Lista", f"${precio_lista_base:,.0f}")
    cc2.metric("Descuento", f"{descuento_pct*100:.1f}%", f"-${monto_descuento:,.0f}")
    cc3.metric("PRECIO CIERRE", f"${precio_cierre:,.0f}", delta_color="normal")
    
    st.divider()
    
    cp1, cp2 = st.columns(2)
    with cp1:
        st.markdown(f"""
        <div style="background:#e3f2fd; padding:15px; border-radius:10px; text-align:center;">
            <small>ENGANCHE ({enganche_pct}%)</small><br>
            <strong style="font-size:20px; color:#004e92">${monto_enganche:,.2f}</strong><br>
            <small>{plazo_meses} Mensualidades de: <b>${mensualidad:,.2f}</b></small>
        </div>
        """, unsafe_allow_html=True)
    with cp2:
        st.markdown(f"""
        <div style="background:#fff3cd; padding:15px; border-radius:10px; text-align:center;">
            <small>SALDO FINAL (FEB 2027)</small><br>
            <strong style="font-size:20px; color:#856404">${saldo_final:,.2f}</strong><br>
            <small>Contra Entrega / Crédito</small>
        </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- GENERACIÓN PDF ---
class PDF(FPDF):
    def header(self):
        try: self.image('logo.png', 10, 8, 30)
        except: pass
        self.set_y(12)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 78, 146)
        self.cell(0, 10, 'COTIZACION OFICIAL', 0, 1, 'R')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Ananda Kino | {date.today().strftime("%d/%m/%Y")}', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    # 1. DATOS
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(50)
    pdf.cell(100, 5, f'Cliente: {cliente_nombre}', 0, 0)
    pdf.cell(0, 5, f'Fecha: {fecha_hoy}', 0, 1, 'R')
    pdf.cell(100, 5, f'Asesor: {asesor_nombre}', 0, 0)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 5, f'LOTE {num_lote_selec} ({m2_terreno:.0f}m2)', 0, 1, 'R')
    pdf.ln(5)

    # 2. PLAN FINANCIERO (RESUMEN)
    pdf.set_fill_color(0, 78, 146)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' PLAN FINANCIERO', 0, 1, 'L', 1)
    
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    pdf.ln(2)
    
    # Tabla de Precios
    pdf.cell(60, 6, "Precio de Lista:", 0)
    pdf.cell(40, 6, f"${precio_lista_base:,.2f}", 0, 1, 'R')
    pdf.ln()
    pdf.cell(60, 6, f"Descuento ({descuento_pct*100:.1f}%):", 0)
    pdf.cell(40, 6, f"-${monto_descuento:,.2f}", 0, 1, 'R')
    pdf.ln()
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 6, "PRECIO FINAL:", 0)
    pdf.cell(40, 6, f"${precio_cierre:,.2f}", 0, 1, 'R')
    
    pdf.ln(4)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(0, 6, "FORMA DE PAGO:", 0, 1)
    pdf.set_font('Arial', '', 9)
    pdf.cell(60, 6, f"Enganche ({enganche_pct}%):", 0)
    pdf.cell(40, 6, f"${monto_enganche:,.2f}", 0, 1, 'R')
    pdf.ln()
    if plazo_meses > 0:
        pdf.cell(60, 6, f"Mensualidades ({plazo_meses}):", 0)
        pdf.cell(40, 6, f"${mensualidad:,.2f} / mes", 0, 1, 'R')
        pdf.ln()
    
    pdf.set_text_color(0, 100, 0)
    pdf.cell(60, 6, "Saldo Final (Feb 2027):", 0)
    pdf.cell(40, 6, f"${saldo_final:,.2f}", 0, 1, 'R')
    pdf.set_text_color(0)

    # 3. PROYECCIÓN Y RENTAS
    pdf.ln(5)
    pdf.set_fill_color(0, 78, 146)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' PROYECCION DE NEGOCIO', 0, 1, 'L', 1)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    pdf.ln(2)
    
    pdf.cell(95, 6, f"Plusvalia Estimada (5 Anios): ${df_plus.iloc[-1]['Valor']:,.0f}", 0, 0)
    pdf.cell(95, 6, f"Renta Anual Est.: ${neto:,.0f} (ROI {roi:.1f}%)", 0, 1)

    # 4. CARACTERISTICAS
    pdf.ln(2)
    pdf.multi_cell(0, 5, "Incluye: 3 Recamaras, 2.5 Banios, Cochera Doble, Cocina equipada, Closets. Privacidad total (sin vecinos pared con pared).")
    
    # Footer Link
    pdf.ln(5)
    pdf.set_text_color(0, 0, 255)
    pdf.set_font('Arial', 'U', 9)
    pdf.cell(0, 5, "https://anandakino.mx/", 0, 1, 'C', link="https://anandakino.mx/")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar Cotización Final")
with c_down2:
    try:
        pdf_bytes = create_pdf()
        fn = f"Cotizacion_{cliente_nombre}_{num_lote_selec}.pdf"
        st.download_button("DESCARGAR PDF", pdf_bytes, file_name=fn, mime='application/pdf')
    except Exception as e:
        st.error(f"Error PDF: {e}")