import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from fpdf import FPDF
from datetime import date
import base64

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ananda Kino | Preventa", page_icon="💎", layout="wide")

# --- ESTILOS VISUALES ---
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #F9FCFF 0%, #FFFFFF 100%); }
    h1, h2, h3, .metric-label { color: #004e92 !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Títulos de Sección Atractivos */
    .section-title { 
        background-color: #f0f7ff; 
        padding: 15px; 
        border-radius: 8px; 
        border-left: 6px solid #004e92; 
        color: #004e92; 
        font-size: 24px; 
        font-weight: 800; 
        margin-top: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Cajas Financieras */
    .fin-card { background: white; padding: 15px; border-radius: 10px; border: 1px solid #e1e5e8; text-align: center; box-shadow: 0 4px 8px rgba(0,0,0,0.05); height: 100%; }
    .fin-label { font-size: 12px; color: #666; text-transform: uppercase; letter-spacing: 1px; }
    .fin-val { font-size: 24px; font-weight: 900; color: #004e92; }
    .fin-discount { font-size: 20px; font-weight: 700; color: #dc3545; }
    .fin-final { font-size: 26px; font-weight: 900; color: #28a745; }

    /* Tablas y Listas */
    .comp-table { width: 100%; border-collapse: collapse; font-size: 14px; }
    .comp-table th { background-color: #004e92; color: white; padding: 10px; text-align: center; }
    .comp-table td { border-bottom: 1px solid #eee; padding: 8px; text-align: center; color: #444; }
    .feature-table td { text-align: left; padding: 10px; font-weight: 500;}
    .check { color: green; font-weight: bold; }
    
    /* Specs */
    .specs-list { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 10px; justify-content: center; }
    .specs-item { background: #fff; padding: 8px 15px; border-radius: 20px; font-size: 13px; font-weight: bold; color: #004e92; border: 1px solid #004e92; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }

    .stButton>button { background-color: #004e92; color: white; font-weight: bold; width: 100%; border-radius: 8px; height: 50px;}
    
    /* Nuevos Estilos para la Sección de Pagos */
    .payment-card {
        background-color: white;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 1px solid #eef2f6;
    }
    .payment-title {
        color: #6c757d;
        font-size: 14px;
        font-weight: 700;
        text-transform: uppercase;
        margin-bottom: 10px;
    }
    .payment-amount {
        color: #004e92;
        font-size: 36px;
        font-weight: 900;
        margin-bottom: 10px;
    }
    .payment-subtitle {
        color: #00c6ff;
        font-size: 14px;
        font-weight: 600;
    }
    .payment-table-header {
        background-color: #004e92;
        color: white;
        padding: 12px;
        text-align: left;
        font-weight: bold;
    }
    .payment-table-row {
        background-color: white;
        border-bottom: 1px solid #eee;
        padding: 12px;
        text-align: left;
    }
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
# 🟦 BARRA LATERAL (CONFIGURACIÓN)
# ==============================================================================
try: st.sidebar.image("logo.png", use_column_width=True)
except: st.sidebar.header("💎 PREVENTA Ananda")

st.sidebar.markdown(f"📅 **{date.today().strftime('%d/%m/%Y')}**")
cliente_nombre = st.sidebar.text_input("Cliente:", value="")
asesor_nombre = st.sidebar.text_input("Asesor:", value="")

st.sidebar.markdown("---")
st.sidebar.header("1. Propiedad")
lista_seleccionada = st.sidebar.selectbox("Lista de Precio:", range(1, 11), index=0)
opciones_lotes = df_raw.apply(lambda x: f"Lote {x['lote']} ({x['status']})", axis=1).tolist()
lote_str_selec = st.sidebar.selectbox("Lote:", opciones_lotes)
num_lote_selec = int(lote_str_selec.split(' ')[1])

st.sidebar.header("2. Forma de Pago")
enganche_pct = st.sidebar.select_slider("% Enganche:", options=[15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 95], value=30)
plazo_meses = st.sidebar.selectbox("Plazo Enganche (Meses):", [0] + list(range(1, 14)), index=12)

# === CÁLCULOS ===
row_lote = df_raw[df_raw['lote'] == num_lote_selec].iloc[0]
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

col_l10 = next((c for c in df_raw.columns if 'lista_10' in c), None)
precio_futuro_lista10 = clean_currency(row_lote[col_l10]) if col_l10 else precio_lista_base * 1.30

# Financiero
descuento_pct = obtener_descuento(plazo_meses, enganche_pct)
monto_descuento = precio_lista_base * descuento_pct
precio_final_venta = precio_lista_base - monto_descuento
plusvalia_preventa = precio_futuro_lista10 - precio_final_venta

# Pagos
monto_enganche = precio_final_venta * (enganche_pct / 100.0)
saldo_final = precio_final_venta - monto_enganche
mensualidad = monto_enganche / plazo_meses if plazo_meses > 0 else 0

st.sidebar.info(f"📋 **Lote {num_lote_selec}:** {m2_terreno:.0f}m² T | {m2_construccion:.0f}m² C")

# ==============================================================================
# 📄 CUERPO PRINCIPAL
# ==============================================================================
st.title(f"💎 PREVENTA Ananda | Lote {num_lote_selec}")
if "Vendido" in lote_str_selec: st.error("⛔ ESTE LOTE YA ESTÁ VENDIDO")

# --- SECCIÓN 1: ESPECIFICACIONES ---
st.markdown('<div class="section-title">1. 44 casas en Bahía Kino</div>', unsafe_allow_html=True)
st.markdown("""
<ul class="specs-list">
    <li class="specs-item">🛏️ 3 Recámaras</li>
    <li class="specs-item">🚿 2.5 Baños</li>
    <li class="specs-item">🚗 Cochera Doble</li>
    <li class="specs-item">🍳 Cocina Equipada</li>
    <li class="specs-item">👕 Closets</li>
    <li class="specs-item">🪟 Cancelería</li>
    <li class="specs-item">✨ Pisos Incluidos</li>
</ul>
""", unsafe_allow_html=True)

# --- SECCIÓN 2: MERCADO & PRECIO ---
st.markdown('<div class="section-title">2. Ananda vs El Mercado</div>', unsafe_allow_html=True)

# BLOQUE DE PRECIO
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f"""<div class="fin-card"><div class="fin-label">Precio de Lista</div><div class="fin-val">${precio_lista_base:,.0f}</div></div>""", unsafe_allow_html=True)
with c2: st.markdown(f"""<div class="fin-card"><div class="fin-label">Tu Descuento ({descuento_pct*100:.1f}%)</div><div class="fin-discount">-${monto_descuento:,.0f}</div></div>""", unsafe_allow_html=True)
with c3: st.markdown(f"""<div class="fin-card" style="border: 2px solid #28a745; background:#f0fff4"><div class="fin-label">PRECIO FINAL A LA ENTREGA</div><div class="fin-final">${precio_final_venta:,.0f}</div></div>""", unsafe_allow_html=True)

st.write("")

precio_m2_ananda = precio_final_venta / m2_construccion if m2_construccion > 0 else 0
data_comp = [
    {"Proyecto": "ANANDA", "Precio": precio_final_venta, "M2": m2_construccion, "Tipo": "Casa", "PrecioM2": precio_m2_ananda},
    {"Proyecto": "Punta Península", "Precio": 4850000, "M2": 100, "Tipo": "Depto", "PrecioM2": 48500},
    {"Proyecto": "HAX", "Precio": 3600000, "M2": 70, "Tipo": "Depto", "PrecioM2": 51428},
    {"Proyecto": "Azaluma", "Precio": 4100000, "M2": 85, "Tipo": "Depto", "PrecioM2": 48235}
]
df_comp = pd.DataFrame(data_comp)

col_comp_1, col_comp_2 = st.columns([1, 1])
with col_comp_1:
    st.markdown(f"#### 🏷️ Tu Precio M²: **${precio_m2_ananda:,.0f}**")
    st.markdown("""
    <table class="comp-table feature-table">
        <tr><th>Ventajas Competitivas</th></tr>
        <tr><td><span class='check'>✔</span> Precio por M² más bajo</td></tr>
        <tr><td><span class='check'>✔</span> Privacidad (Sin vecinos arriba/abajo)</td></tr>
        <tr><td><span class='check'>✔</span> Cochera Doble</td></tr>
        <tr><td><span class='check'>✔</span> Mantenimiento Bajo</td></tr>
        <tr><td><span class='check'>✔</span> Dueño de Tierra + Casa</td></tr>
    </table>
    """, unsafe_allow_html=True)
with col_comp_2:
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
st.markdown('<div class="section-title">3. Proyección de Plusvalía</div>', unsafe_allow_html=True)

# Variables Proyección
tarifa_base = 4500
ocupacion_base = 0.45
inflacion = 0.05
plusvalia_anual = 0.08
years = range(2027, 2033)

data_proy = []
val_prop = precio_futuro_lista10 # Empieza en valor lista 10
acum_rentas = 0

for i, y in enumerate(years):
    t_act = tarifa_base * ((1+inflacion)**i)
    neto_anual_est = (t_act * 365 * ocupacion_base) * 0.70
    if y > 2027:
        acum_rentas += neto_anual_est
    data_proy.append({
        "Año": y, 
        "Valor Propiedad": val_prop, 
        "Renta Acumulada": acum_rentas,
        "Total Patrimonio": val_prop + acum_rentas
    })
    val_prop *= (1 + plusvalia_anual)

df_proy = pd.DataFrame(data_proy)
valor_final_5y = df_proy.iloc[-1]['Valor Propiedad']

col_plus_1, col_plus_2 = st.columns([2, 1])
with col_plus_1:
    fig_area = px.area(df_proy, x="Año", y=["Valor Propiedad", "Renta Acumulada"], 
                      title="Crecimiento Total (Valor Casa + Rentas)",
                      color_discrete_map={"Valor Propiedad":"#004e92", "Renta Acumulada":"#28a745"})
    fig_area.update_layout(plot_bgcolor='rgba(0,0,0,0)', legend_title_text='')
    st.plotly_chart(fig_area, use_container_width=True)
with col_plus_2:
    st.markdown(f"""
    <div class="fin-card" style="margin-bottom:15px;">
        <div class="fin-label">Plusvalía a la Entrega (2027)</div>
        <div class="fin-val" style="color:#28a745">+${plusvalia_preventa:,.0f}</div>
        <small>Ganancia vs Lista 10</small>
    </div>
    <div class="fin-card" style="background:#f9f9f9;">
        <div class="fin-label">Valor Propiedad (2032)</div>
        <div class="fin-val">${valor_final_5y:,.0f}</div>
        <small>Proyección 5 Años</small>
    </div>
    """, unsafe_allow_html=True)

# --- SECCIÓN 4: RENTAS ---
st.markdown('<div class="section-title">4. Simulador de Negocio (Rentas)</div>', unsafe_allow_html=True)

c4a, c4b = st.columns([1, 2])
with c4a:
    st.markdown("##### Variables")
    tarifa = st.number_input("Tarifa Noche ($):", value=4500, step=500)
    ocupacion = st.slider("Ocupación Anual %:", 20, 80, 45) / 100
    st.markdown("##### Gastos")
    admin_pct = st.slider("Comisión Administración %:", 15, 30, 25) / 100
    gastos_fijos = st.number_input("Gastos Fijos Mensuales (Luz/Net) $:", value=3000, step=500)

with c4b:
    ingreso_bruto = tarifa * 365 * ocupacion
    gasto_admin = ingreso_bruto * admin_pct
    gasto_servicios = gastos_fijos * 12
    total_gastos = gasto_admin + gasto_servicios
    neto_bolsillo = ingreso_bruto - total_gastos
    roi = (neto_bolsillo / precio_final_venta) * 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingreso Bruto", f"${ingreso_bruto:,.0f}")
    m2.metric("Total Gastos", f"-${total_gastos:,.0f}")
    m3.metric("UTILIDAD NETA", f"${neto_bolsillo:,.0f}", delta=f"ROI {roi:.1f}%")
    
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Tu Ganancia', 'Comisión Admin', 'Servicios/Gastos'],
        values=[neto_bolsillo, gasto_admin, gasto_servicios],
        hole=.4,
        marker_colors=['#28a745', '#ef553b', '#ffc107']
    )])
    fig_pie.update_layout(height=250, margin=dict(t=0,b=0,l=0,r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

# --- SECCIÓN 5: PLAN DE INVERSIÓN (NUEVO DISEÑO) ---
st.markdown('<div class="section-title">5. Plan de Inversión</div>', unsafe_allow_html=True)

col_izq, col_der = st.columns([1, 1])

with col_izq:
    st.markdown(f"""
        <div class="payment-card">
            <div class="payment-title">ENGANCHE TOTAL ({enganche_pct}%)</div>
            <div class="payment-amount">${monto_enganche:,.2f}</div>
            <div class="payment-subtitle">A pagar en {plazo_meses} meses</div>
        </div>
    """, unsafe_allow_html=True)

with col_der:
    st.markdown(f"""
        <div class="payment-card">
            <div class="payment-title">LIQUIDACIÓN FINAL</div>
            <div class="payment-amount" style="color:#2c3e50">${saldo_final:,.2f}</div>
            <div class="payment-subtitle" style="color:#7f8c8d">Contra Entrega (Febrero 2027)</div>
        </div>
    """, unsafe_allow_html=True)

if plazo_meses > 0:
    st.markdown("### 📅 Desglose de Mensualidades")
    
    # Crear tabla HTML
    html_table = """
    <table style="width:100%; border-collapse: collapse; margin-top: 20px;">
        <thead>
            <tr style="background-color: #004e92; color: white;">
                <th style="padding: 12px; text-align: left;">#</th>
                <th style="padding: 12px; text-align: left;">Concepto</th>
                <th style="padding: 12px; text-align: right;">Monto</th>
            </tr>
        </thead>
        <tbody>
    """
    for i in range(1, plazo_meses + 1):
        html_table += f"""
            <tr style="border-bottom: 1px solid #eee;">
                <td style="padding: 12px;">{i}</td>
                <td style="padding: 12px;">Mensualidad Enganche</td>
                <td style="padding: 12px; text-align: right; font-weight: bold;">${mensualidad:,.2f}</td>
            </tr>
        """
    html_table += "</tbody></table>"
    st.markdown(html_table, unsafe_allow_html=True)

# --- PDF GENERATOR (BRIEF DE VENTA) ---
class PDF(FPDF):
    def header(self):
        try: self.image('logo.png', 10, 8, 30)
        except: pass
        self.set_y(12)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 78, 146)
        self.cell(0, 10, 'COTIZACION PREVENTA ANANDA', 0, 1, 'R')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Ananda Kino | {date.today().strftime("%d/%m/%Y")} | Pagina {self.page_no()}', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    
    # 1. HEADER
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(50)
    pdf.cell(100, 5, f'Cliente: {cliente_nombre if cliente_nombre else "_________________"}', 0, 0)
    pdf.cell(0, 5, f'Fecha: {date.today().strftime("%d/%m/%Y")}', 0, 1, 'R')
    pdf.cell(100, 5, f'Asesor: {asesor_nombre if asesor_nombre else "_________________"}', 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 5, f'LOTE {num_lote_selec} ({m2_terreno:.0f}m2)', 0, 1, 'R')
    pdf.ln(5)

    # 2. SECCION PRECIOS
    pdf.set_fill_color(0, 78, 146)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' 1. OFERTA DE PREVENTA', 0, 1, 'L', 1)
    
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    pdf.ln(2)
    pdf.cell(60, 6, 'Precio Lista:', 0)
    pdf.cell(40, 6, f"${precio_lista_base:,.0f}", 0, 1, 'R')
    pdf.ln()
    pdf.set_text_color(220, 53, 69)
    pdf.cell(60, 6, f"Descuento ({descuento_pct*100:.1f}%):", 0)
    pdf.cell(40, 6, f"-${monto_descuento:,.0f}", 0, 1, 'R')
    pdf.ln()
    pdf.set_text_color(0, 78, 146)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(60, 6, "PRECIO FINAL A LA ENTREGA:", 0)
    pdf.cell(40, 6, f"${precio_final_venta:,.0f}", 0, 1, 'R')
    
    # 3. SECCION PLUSVALIA
    pdf.ln(4)
    pdf.set_fill_color(0, 78, 146)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' 2. PROYECCION DE PLUSVALIA', 0, 1, 'L', 1)
    
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    pdf.ln(2)
    pdf.cell(60, 6, "Valor a la Entrega (2027):", 0)
    pdf.cell(40, 6, f"${precio_futuro_lista10:,.0f}", 0, 1, 'R')
    pdf.set_text_color(40, 167, 69)
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(60, 6, "Plusvalia Preventa Ganada:", 0)
    pdf.cell(40, 6, f"+${plusvalia_preventa:,.0f}", 0, 1, 'R')
    pdf.set_font('Arial', '', 9)
    pdf.set_text_color(0)
    pdf.cell(60, 6, "Valor Proyectado (5 Anios):", 0)
    pdf.cell(40, 6, f"${valor_final_5y:,.0f}", 0, 1, 'R')

    # 4. PLAN DE INVERSION (NUEVO DISEÑO PDF)
    pdf.ln(4)
    pdf.set_fill_color(0, 78, 146)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' 3. PLAN DE INVERSION', 0, 1, 'L', 1)
    
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    pdf.ln(2)
    
    # Tabla de pagos
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(30, 6, "CONCEPTO", 1, 0, 'C', 1)
    pdf.cell(40, 6, "DETALLE", 1, 0, 'C', 1)
    pdf.cell(30, 6, "MONTO", 1, 1, 'C', 1)
    
    pdf.cell(30, 6, "Enganche", 1, 0)
    pdf.cell(40, 6, f"{enganche_pct}% del Valor", 1, 0)
    pdf.cell(30, 6, f"${monto_enganche:,.0f}", 1, 1, 'R')
    
    pdf.cell(30, 6, "Saldo Final", 1, 0)
    pdf.cell(40, 6, "Contra Entrega", 1, 0)
    pdf.cell(30, 6, f"${saldo_final:,.0f}", 1, 1, 'R')
    
    if plazo_meses > 0:
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 9)
        pdf.cell(0, 6, "DESGLOSE DE MENSUALIDADES:", 0, 1)
        pdf.set_font('Arial', '', 9)
        for i in range(1, plazo_meses + 1):
            pdf.cell(30, 6, f"Pago {i}", 1, 0, 'C')
            pdf.cell(40, 6, "Mensualidad Enganche", 1, 0)
            pdf.cell(30, 6, f"${mensualidad:,.0f}", 1, 1, 'R')

    # 5. RENTAS
    pdf.ln(4)
    pdf.set_fill_color(0, 78, 146)
    pdf.set_text_color(255)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, ' 4. NEGOCIO RENTAS (ESTIMADO)', 0, 1, 'L', 1)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 9)
    pdf.ln(1)
    
    pdf.cell(50, 6, f"Ingreso Bruto Anual:", 0)
    pdf.cell(30, 6, f"${ingreso_bruto:,.0f}", 0, 1, 'R')
    pdf.ln()
    pdf.cell(50, 6, f"Gastos (Admin + Serv.):", 0)
    pdf.cell(30, 6, f"-${total_gastos:,.0f}", 0, 1, 'R')
    pdf.ln()
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(40, 167, 69)
    pdf.cell(50, 6, f"UTILIDAD NETA:", 0)
    pdf.cell(30, 6, f"${neto_bolsillo:,.0f}", 0, 1, 'R')
    pdf.set_text_color(0)

    # 6. VENTAJAS
    pdf.ln(4)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 6, ' VENTAJAS EXCLUSIVAS', 0, 1)
    pdf.set_text_color(0)
    pdf.set_font('Arial', '', 8)
    
    features = ["Precio por M2 mas bajo", "Privacidad Total", "Cochera Doble", "Mantenimiento Bajo", "Dueño de Tierra + Casa"]
    for i in range(0, len(features), 2):
        t1 = f"- {features[i]}"
        try: t2 = f"- {features[i+1]}" if i+1 < len(features) else ""
        except: t2 = ""
        pdf.cell(90, 5, t1.encode('latin-1', 'replace').decode('latin-1'), 0, 0)
        pdf.cell(90, 5, t2.encode('latin-1', 'replace').decode('latin-1'), 0, 1)

    # FOOTER
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(0, 0, 255)
    pdf.cell(0, 5, 'https://anandakino.mx/', 0, 1, 'C', link='https://anandakino.mx/')

    return pdf.output(dest='S').encode('latin-1', 'replace')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar Cotización Preventa")
with c_down2:
    try:
        pdf_bytes = create_pdf()
        fn = f"Cotizacion_Preventa_{cliente_nombre}_{num_lote_selec}.pdf"
        st.download_button("DESCARGAR PDF", pdf_bytes, file_name=fn, mime='application/pdf')
    except Exception as e:
        st.error(f"Error PDF: {e}")