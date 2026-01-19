import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from fpdf import FPDF
from datetime import date
import base64

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
    
    /* Tabla Comparativa */
    .comp-table { width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 10px; }
    .comp-table th { background-color: #004e92; color: white; padding: 12px; text-align: center; }
    .comp-table td { border-bottom: 1px solid #ddd; padding: 10px; text-align: center; color: #333; }
    .feature-table td { text-align: left; padding: 12px; border-bottom: 1px solid #eee; font-size: 15px; }
    .check { color: green; font-weight: bold; font-size: 1.1em;}
    
    /* Ficha Técnica */
    .specs-box { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 5px solid #004e92; margin-bottom: 20px; }
    .specs-list { list-style-type: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 10px; }
    .specs-item { background: white; padding: 5px 10px; border-radius: 15px; font-size: 13px; font-weight: bold; color: #004e92; border: 1px solid #bbdefb; }

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
            
            # Status Original
            col_status = next((c for c in df.columns if 'cliente' in c or 'estatus' in c), None)
            if col_status:
                df['status'] = df[col_status].apply(lambda x: 'Vendido' if pd.notnull(x) and str(x).strip() not in ['', 'nan'] else 'Disponible')
            else:
                df['status'] = 'Disponible'
            
            # REGLA FORZADA: Lotes 11 al 22 VENDIDOS
            df.loc[(df['lote'] >= 11) & (df['lote'] <= 22), 'status'] = 'Vendido'
            
            return df
        return None
    except: return None

df_raw = load_data()
if df_raw is None: df_raw = pd.DataFrame({'lote': range(1, 45), 'status': ['Disponible']*44})

# --- 2. SIDEBAR ---
try: st.sidebar.image("logo.png", use_column_width=True)
except: st.sidebar.header("🏠 Ananda Residencial")

# DATOS DEL CLIENTE (NUEVO)
st.sidebar.header("👤 Personalización")
cliente_nombre = st.sidebar.text_input("Nombre del Cliente:", value="")
asesor_nombre = st.sidebar.text_input("Asesor de Ventas:", value="")

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Configuración")
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
plusvalia_preventa = precio_final_mercado - precio_lista_actual

st.sidebar.info(f"📋 **Lote {num_lote_selec}:** {m2_terreno:.0f}m² Terreno | {m2_construccion:.0f}m² Const.")

# --- 3. PANEL PRINCIPAL ---
st.title(f"Residencia Ananda | Lote {num_lote_selec}")
if "Vendido" in lote_str_selec: st.warning("⛔ LOTE VENDIDO")

# BLOQUE FICHA TÉCNICA
st.markdown("""
<div class="specs-box">
    <strong>🏡 MODELO ANANDA (Casa Independiente)</strong><br><br>
    <ul class="specs-list">
        <li class="specs-item">🛏️ 3 Recámaras</li>
        <li class="specs-item">🚿 2.5 Baños</li>
        <li class="specs-item">🚗 Cochera Doble</li>
        <li class="specs-item">🍳 Cocina con Barra</li>
        <li class="specs-item">👕 Closets</li>
        <li class="specs-item">🪟 Cancelería</li>
        <li class="specs-item">✨ Pisos Incluidos</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# CONTADOR
entrega = date(2027, 2, 28)
dias_restantes = (entrega - date.today()).days
st.markdown(f"""<div style="background:#004e92; color:white; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
    <div style="font-size:14px; text-transform:uppercase;">Entrega Feb 2027 - Plusvalía en Marcha</div>
    <div style="font-size:32px; font-weight:900;">{dias_restantes} Días</div>
</div>""", unsafe_allow_html=True)

# TARJETAS
c1, c2, c3 = st.columns(3)
with c1: st.markdown(f"""<div class="metric-card"><div>Inversión Inicial</div><div class="big-number">${precio_lista_actual:,.0f}</div><small>Preventa</small></div>""", unsafe_allow_html=True)
with c2: st.markdown(f"""<div class="metric-card" style="border:2px solid #ffc107; background:#fffdf5"><div>Valor Entrega</div><div class="future-number">${precio_final_mercado:,.0f}</div><small>Feb 2027</small></div>""", unsafe_allow_html=True)
with c3: st.markdown(f"""<div class="metric-card" style="background:#f0fff4; border:2px solid #28a745;"><div>Plusvalía Ganada</div><div class="big-number" style="color:#28a745">+${plusvalia_preventa:,.0f}</div><small>Al cierre de preventa</small></div>""", unsafe_allow_html=True)

# --- 4. PROYECCIÓN PATRIMONIAL ---
st.markdown("---")
st.header("📈 Tu Patrimonio en 5 Años (2028-2032)")
st.caption("Gráfica: Valor Propiedad + Rentas Acumuladas | Tabla: Valor Propiedad.")

tarifa_base = 4500
ocupacion_base = 0.45
inflacion = 0.05
plusvalia_anual = 0.08
years = range(2028, 2033)

data_proy = []
val_prop = precio_final_mercado
acum_rentas = 0

for i, y in enumerate(years):
    val_prop = val_prop * (1 + plusvalia_anual)
    t_act = tarifa_base * ((1+inflacion)**i)
    neto_anual_est = (t_act * 365 * ocupacion_base) * 0.70 
    acum_rentas += neto_anual_est
    
    data_proy.append({
        "Año": y, 
        "Valor Propiedad": val_prop, 
        "Renta Acumulada": acum_rentas,
        "Total Patrimonio": val_prop + acum_rentas
    })

df_proy = pd.DataFrame(data_proy)

col_graf_plus, col_tab_plus = st.columns([2, 1])

with col_graf_plus:
    fig_area = px.area(df_proy, x="Año", y=["Valor Propiedad", "Renta Acumulada"], 
                      title="Crecimiento Total (Plusvalía + Rentas)",
                      color_discrete_map={"Valor Propiedad":"#004e92", "Renta Acumulada":"#28a745"})
    fig_area.update_layout(plot_bgcolor='rgba(0,0,0,0)', legend_title_text='')
    st.plotly_chart(fig_area, use_container_width=True)

with col_tab_plus:
    st.subheader("Evolución Valor Casa")
    st.markdown(f"""
    <table class="comp-table">
        <tr><th>Año</th><th>Valor Propiedad</th></tr>
        {''.join([f"<tr><td>{r['Año']}</td><td><b>${r['Valor Propiedad']:,.0f}</b></td></tr>" for i,r in df_proy.iterrows()])}
    </table>
    """, unsafe_allow_html=True)

# --- 5. ANANDA VS EL MERCADO ---
st.markdown("---")
st.header("🏆 Ananda vs El Mercado")

precio_m2_ananda = precio_lista_actual / m2_construccion if m2_construccion > 0 else 0
data_comp = [
    {"Proyecto": "ANANDA", "Precio": precio_lista_actual, "M2": m2_construccion, "Tipo": "Casa", "PrecioM2": precio_m2_ananda},
    {"Proyecto": "Punta Península", "Precio": 4850000, "M2": 100, "Tipo": "Depto", "PrecioM2": 48500},
    {"Proyecto": "HAX", "Precio": 3600000, "M2": 70, "Tipo": "Depto", "PrecioM2": 51428},
    {"Proyecto": "Azaluma", "Precio": 4100000, "M2": 85, "Tipo": "Depto", "PrecioM2": 48235}
]
df_comp = pd.DataFrame(data_comp)

col_feat, col_price = st.columns([1, 1])

with col_feat:
    st.metric(label=f"Tu Precio por M² (Lote {num_lote_selec})", value=f"${precio_m2_ananda:,.0f}")
    st.subheader("Diferenciadores Clave")
    st.markdown("""
    <table class="comp-table feature-table">
        <tr><th>Ventajas de tu Casa en Ananda</th></tr>
        <tr><td><span class='check'>✔</span> Precio por M² más bajo del mercado</td></tr>
        <tr><td><span class='check'>✔</span> Privacidad (Sin vecinos arriba ni abajo)</td></tr>
        <tr><td><span class='check'>✔</span> Cochera Doble</td></tr>
        <tr><td><span class='check'>✔</span> Mantenimiento Bajo (No frente al mar)</td></tr>
        <tr><td><span class='check'>✔</span> Dueño de la Tierra + Construcción</td></tr>
    </table>
    """, unsafe_allow_html=True)

with col_price:
    st.subheader("Comparativa Precio por M²")
    fig_bar = go.Figure(go.Bar(
        x=df_comp.sort_values('PrecioM2')['Proyecto'], 
        y=df_comp.sort_values('PrecioM2')['PrecioM2'],
        marker_color=['#28a745' if 'ANANDA' in p else '#ef553b' for p in df_comp.sort_values('PrecioM2')['Proyecto']],
        text=[f"${x:,.0f}" for x in df_comp.sort_values('PrecioM2')['PrecioM2']],
        textposition='auto'
    ))
    fig_bar.update_layout(height=300, plot_bgcolor='rgba(0,0,0,0)', yaxis_title="$/m2")
    st.plotly_chart(fig_bar, use_container_width=True)

# --- 6. SIMULADOR DE RENTAS ---
st.markdown("---")
st.header("📊 Simulador de Negocio")
st.markdown('<div class="section-box">', unsafe_allow_html=True)

col_inputs, col_results = st.columns([1, 2])
with col_inputs:
    tarifa = st.number_input("Tarifa Noche Promedio:", value=4500, step=500)
    ocupacion_pct = st.slider("Ocupación Anual (%):", 20, 80, 45)
    comision_pct = st.slider("Comisión Administración (%):", 15, 35, 25) / 100
    mto_mensual = st.number_input("Mantenimiento Mensual ($):", value=2000)

with col_results:
    ingreso_bruto = tarifa * 365 * (ocupacion_pct/100)
    gasto_admin = ingreso_bruto * comision_pct
    gasto_mto = mto_mensual * 12
    total_gastos = gasto_admin + gasto_mto
    neto_anual = ingreso_bruto - total_gastos
    roi = (neto_anual / precio_lista_actual) * 100
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingreso Bruto", f"${ingreso_bruto:,.0f}")
    m2.metric("Gastos", f"-${total_gastos:,.0f}")
    m3.metric("Neto Bolsillo", f"${neto_anual:,.0f}", delta=f"ROI {roi:.1f}%")
    
    fig_pie = go.Figure(data=[go.Pie(labels=['Ganancia', 'Comisión', 'Mantenimiento'], values=[neto_anual, gasto_admin, gasto_mto], hole=.4)])
    fig_pie.update_layout(height=250, margin=dict(t=0,b=0))
    st.plotly_chart(fig_pie, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 7. PDF ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 78, 146)
        self.rect(0, 0, 210, 35, 'F')
        try: self.image('logo.png', 10, 6, 30)
        except: pass
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, '', 0, 1)
        self.cell(0, 10, 'COTIZACION & NEGOCIO', 0, 1, 'R')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Ananda Kino | {date.today().strftime("%d/%m/%Y")}', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    # 0. HEADER CLIENTE
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(100)
    if cliente_nombre: pdf.cell(0, 5, f'Preparado para: {cliente_nombre}', 0, 1, 'R')
    if asesor_nombre: pdf.cell(0, 5, f'Asesor: {asesor_nombre}', 0, 1, 'R')
    pdf.ln(5)

    # 1. Detalles
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, f'Propiedad: Casa en Lote {num_lote_selec}', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f'Terreno: {m2_terreno:.2f} m2 | Construccion: {m2_construccion:.2f} m2', 0, 1)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 10)
    pdf.multi_cell(0, 6, "Incluye: 3 Recamaras, 2.5 Banios, Cochera Doble, Cocina con barra, Closets y Pisos.")
    
    # 2. Precios
    pdf.ln(5)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 8, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 8, 'Monto', 1, 1, 'R', 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(100, 8, f'Precio Preventa (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 8, f'${precio_lista_actual:,.2f}', 1, 1, 'R')
    pdf.cell(100, 8, 'Valor Mercado (Feb 2027)', 1, 0)
    pdf.cell(60, 8, f'${precio_final_mercado:,.2f}', 1, 1, 'R')
    
    # 3. Rentas Detallado (NUEVO DESGLOSE)
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, 'Analisis de Negocio (Estimado Anual)', 0, 1)
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0)
    pdf.cell(100, 8, 'Ingresos Brutos (Renta):', 1, 0)
    pdf.cell(60, 8, f'+ ${ingreso_bruto:,.2f}', 1, 1, 'R')
    
    pdf.set_text_color(150, 0, 0)
    pdf.cell(100, 8, 'Gastos Operativos (Admin + Mto):', 1, 0)
    pdf.cell(60, 8, f'- ${total_gastos:,.2f}', 1, 1, 'R')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(40, 167, 69)
    pdf.cell(100, 8, 'UTILIDAD NETA (Bolsillo):', 1, 0)
    pdf.cell(60, 8, f'= ${neto_anual:,.2f}', 1, 1, 'R')
    
    pdf.set_font('Arial', 'I', 10)
    pdf.set_text_color(100)
    pdf.cell(0, 8, f'Retorno sobre Inversion (ROI): {roi:.1f}% Anual', 0, 1, 'R')

    # 4. Proyección Anual
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, 'Crecimiento Patrimonial (5 Anios)', 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.set_fill_color(220)
    pdf.cell(40, 8, 'Year', 1, 0, 'C', 1)
    pdf.cell(60, 8, 'Valor Propiedad', 1, 0, 'C', 1)
    pdf.cell(60, 8, 'Ingreso Renta Acum.', 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 10)
    for index, row in df_proy.iterrows():
        pdf.cell(40, 8, str(row['Año']), 1, 0, 'C')
        pdf.cell(60, 8, f"${row['Valor Propiedad']:,.0f}", 1, 0, 'R')
        pdf.cell(60, 8, f"${row['Renta Acumulada']:,.0f}", 1, 1, 'R')

    # 5. Características
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, 'Ventajas Ananda', 0, 1)
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0)
    
    features = [
        "Precio por M2 mas competitivo",
        "Privacidad (Sin vecinos arriba ni abajo)",
        "Cochera Doble",
        "Mantenimiento Eficiente"
    ]
    for f in features:
        pdf.cell(0, 6, f"- {f}", 0, 1)

    return pdf.output(dest='S').encode('latin-1', 'replace')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar PDF Personalizado")
with c_down2:
    try:
        pdf_bytes = create_pdf()
        filename_pdf = f"Cotizacion_{cliente_nombre.replace(' ','_') if cliente_nombre else 'Ananda'}.pdf"
        st.download_button("DESCARGAR PDF", pdf_bytes, file_name=filename_pdf, mime='application/pdf')
    except Exception as e:
        st.error(f"Error PDF: {e}")