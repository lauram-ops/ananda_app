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
    .metric-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center; border: 1px solid #e1e5e8; height: 100%;}
    .big-number { font-size: 28px; font-weight: 800; color: #004e92; }
    .future-number { font-size: 28px; font-weight: 800; color: #ffc107; }
    .comp-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
    .comp-table th { background-color: #004e92; color: white; padding: 12px; text-align: center; }
    .comp-table td { border-bottom: 1px solid #ddd; padding: 10px; text-align: center; color: #333; }
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
            
            col_status = next((c for c in df.columns if 'cliente' in c or 'estatus' in c), None)
            if col_status:
                df['status'] = df[col_status].apply(lambda x: 'Vendido' if pd.notnull(x) and str(x).strip() not in ['', 'nan'] else 'Disponible')
            else:
                df['status'] = 'Disponible'
            return df
        return None
    except: return None

df_raw = load_data()
if df_raw is None: df_raw = pd.DataFrame({'lote': range(1, 45), 'status': ['Disponible']*44})

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

# Precio Futuro (Entrega)
col_l10 = next((c for c in df_raw.columns if 'lista_10' in c), None)
precio_final_mercado = clean_currency(row_lote[col_l10]) if col_l10 else precio_lista_actual * 1.30
plusvalia_preventa = precio_final_mercado - precio_lista_actual

# --- VARIABLES RENTAS (Globales para usarlas en PDF) ---
st.sidebar.markdown("---")
st.sidebar.markdown("##### ⚙️ Ajustes Financieros")
tarifa = st.sidebar.number_input("Tarifa Noche:", value=4500, step=500)
ocupacion_pct = st.sidebar.slider("Ocupación %:", 30, 70, 45)
comision_pct = st.sidebar.slider("Comisión Admin %:", 15, 35, 25) / 100
mto_mensual = st.sidebar.number_input("Mantenimiento Mensual:", value=2000)

# CÁLCULOS 5 AÑOS (PROYECCIÓN)
years = range(2028, 2033)
inflacion_anual = 0.05
plusvalia_anual_mercado = 0.08 # 8% anual conservador sobre valor propiedad

data_proyeccion = []
valor_propiedad = precio_final_mercado # Inicia en valor de entrega
acumulado_rentas = 0

for i, y in enumerate(years):
    # Plusvalía Propiedad
    valor_propiedad = valor_propiedad * (1 + plusvalia_anual_mercado)
    
    # Rentas
    t_actual = tarifa * ((1 + inflacion_anual) ** i)
    bruto = t_actual * 365 * (ocupacion_pct/100)
    gastos = (bruto * comision_pct) + (mto_mensual * 12 * ((1+inflacion_anual)**i))
    neto = bruto - gastos
    acumulado_rentas += neto
    
    data_proyeccion.append({
        "Año": y,
        "Valor Propiedad": valor_propiedad,
        "Flujo Neto": neto,
        "Acumulado Rentas": acumulado_rentas
    })

# --- 3. PANEL SUPERIOR ---
st.title(f"Residencia Ananda | Lote {num_lote_selec}")
if "Vendido" in lote_str_selec: st.warning("⛔ LOTE VENDIDO")

entrega = date(2027, 2, 28)
dias_restantes = (entrega - date.today()).days
st.markdown(f"""<div style="background:#004e92; color:white; padding:15px; border-radius:10px; text-align:center; margin-bottom:20px;">
    <div style="font-size:14px; text-transform:uppercase;">Entrega Feb 2027 - Plusvalía en Marcha</div>
    <div style="font-size:32px; font-weight:900;">{dias_restantes} Días</div>
</div>""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f"""<div class="metric-card"><div>Inversión Inicial</div><div class="big-number">${precio_lista_actual:,.0f}</div><small>Preventa</small></div>""", unsafe_allow_html=True)
with c2: st.markdown(f"""<div class="metric-card" style="border:2px solid #ffc107; background:#fffdf5"><div>Valor Entrega</div><div class="future-number">${precio_final_mercado:,.0f}</div><small>Feb 2027</small></div>""", unsafe_allow_html=True)
with c3: st.markdown(f"""<div class="metric-card" style="background:#f0fff4; border:2px solid #28a745;"><div>Patrimonio Año 5</div><div class="big-number" style="color:#28a745">${data_proyeccion[-1]['Valor Propiedad']:,.0f}</div><small>Proyectado 2032</small></div>""", unsafe_allow_html=True)

# --- 4. COMPARATIVA ---
st.markdown("---")
st.header("🏆 Análisis de Mercado")
precio_m2_ananda = precio_lista_actual / m2_construccion if m2_construccion > 0 else 0
data_comp = [
    {"Proyecto": "ANANDA", "Precio": precio_lista_actual, "M2": m2_construccion, "Tipo": "Casa"},
    {"Proyecto": "Punta Península", "Precio": 4850000, "M2": 100, "Tipo": "Depto"},
    {"Proyecto": "HAX", "Precio": 3600000, "M2": 70, "Tipo": "Depto"},
    {"Proyecto": "Azaluma", "Precio": 4100000, "M2": 85, "Tipo": "Depto"}
]
df_comp = pd.DataFrame(data_comp)
df_comp['Precio_M2'] = df_comp['Precio'] / df_comp['M2']

c_sc, c_bar = st.columns([2, 1])
with c_sc:
    fig_sc = px.scatter(df_comp, x="Precio", y="M2", color="Tipo", size="M2", text="Proyecto", color_discrete_map={"Casa":"#004e92","Depto":"#ef553b"}, title="Valor por tu Dinero")
    fig_sc.update_traces(textposition='top center', marker=dict(size=25))
    st.plotly_chart(fig_sc, use_container_width=True)
with c_bar:
    st.markdown(f"""<table class="comp-table"><tr><th>Proyecto</th><th>$/M²</th></tr>
    {''.join([f"<tr><td>{r['Proyecto']}</td><td>${r['Precio_M2']:,.0f}</td></tr>" for i,r in df_comp.sort_values('Precio_M2').iterrows()])}
    </table>""", unsafe_allow_html=True)

# --- 5. RENTAS ---
st.markdown("---")
st.header("📈 Proyección Financiera (5 Años)")
col_tab, col_graf = st.columns([1, 1])

with col_tab:
    st.markdown("##### Flujo de Efectivo Proyectado")
    st.dataframe(pd.DataFrame(data_proyeccion).style.format({"Valor Propiedad":"${:,.0f}", "Flujo Neto":"${:,.0f}", "Acumulado Rentas":"${:,.0f}"}))

with col_graf:
    st.markdown("##### Crecimiento Patrimonial")
    fig_area = px.area(pd.DataFrame(data_proyeccion), x="Año", y="Valor Propiedad", title="Plusvalía Acumulada")
    fig_area.update_traces(line_color='#004e92')
    st.plotly_chart(fig_area, use_container_width=True)

# --- 6. PDF ROBUSTO ---
class PDF(FPDF):
    def header(self):
        self.set_fill_color(0, 78, 146)
        self.rect(0, 0, 210, 35, 'F')
        try: self.image('logo.png', 10, 6, 30)
        except: pass
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, '', 0, 1)
        self.cell(0, 10, 'REPORTE DE INVERSIÓN', 0, 1, 'R')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Ananda Kino - Proyecciones informativas sujetas a mercado.', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    # SECCIÓN 1: RESUMEN EJECUTIVO
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, f'Propiedad: Casa en Lote {num_lote_selec}', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f'Terreno: {m2_terreno:.2f} m2 | Construcción: {m2_construccion:.2f} m2', 0, 1)
    
    # Tabla Cotización
    pdf.ln(5)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 8, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 8, 'Monto', 1, 1, 'R', 1)
    
    pdf.set_font('Arial', '', 11)
    pdf.cell(100, 8, f'Precio Preventa (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 8, f'${precio_lista_actual:,.2f}', 1, 1, 'R')
    pdf.cell(100, 8, 'Valor Mercado (Entrega Feb 2027)', 1, 0)
    pdf.cell(60, 8, f'${precio_final_mercado:,.2f}', 1, 1, 'R')
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(40, 167, 69)
    pdf.cell(100, 8, 'PLUSVALÍA INMEDIATA:', 1, 0)
    pdf.cell(60, 8, f'${plusvalia_preventa:,.2f}', 1, 1, 'R')
    
    # SECCIÓN 2: PROYECCIÓN 5 AÑOS (PLUSVALÍA)
    pdf.ln(10)
    pdf.set_text_color(0, 78, 146)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Proyección de Plusvalía (5 Años)', 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(40, 8, 'Año', 1, 0, 'C', 1)
    pdf.cell(60, 8, 'Valor Propiedad', 1, 0, 'C', 1)
    pdf.cell(60, 8, 'Plusvalía Acumulada', 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 10)
    val_inicial = precio_final_mercado
    for row in data_proyeccion:
        pdf.cell(40, 8, str(row['Año']), 1, 0, 'C')
        pdf.cell(60, 8, f"${row['Valor Propiedad']:,.2f}", 1, 0, 'R')
        ganancia = row['Valor Propiedad'] - precio_lista_actual
        pdf.cell(60, 8, f"${ganancia:,.2f}", 1, 1, 'R')

    # SECCIÓN 3: RENTAS
    pdf.ln(10)
    pdf.set_text_color(0, 78, 146)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Negocio de Rentas (Estimado)', 0, 1)
    
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0)
    roi = (data_proyeccion[0]['Flujo Neto'] / precio_lista_actual) * 100
    pdf.multi_cell(0, 6, f"Escenario con Ocupación al {ocupacion_pct}% y Tarifa Promedio de ${tarifa:,.0f}.\nROI Estimado Año 1: {roi:.1f}% anual.")
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(40, 8, 'Año', 1, 0, 'C', 1)
    pdf.cell(60, 8, 'Flujo Neto (Bolsillo)', 1, 0, 'C', 1)
    pdf.cell(60, 8, 'Ingreso Acumulado', 1, 1, 'C', 1)
    
    pdf.set_font('Arial', '', 10)
    for row in data_proyeccion:
        pdf.cell(40, 8, str(row['Año']), 1, 0, 'C')
        pdf.cell(60, 8, f"${row['Flujo Neto']:,.2f}", 1, 0, 'R')
        pdf.cell(60, 8, f"${row['Acumulado Rentas']:,.2f}", 1, 1, 'R')
        
    # TOTAL FINAL
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(0, 78, 146)
    total_beneficio = (data_proyeccion[-1]['Valor Propiedad'] - precio_lista_actual) + data_proyeccion[-1]['Acumulado Rentas']
    pdf.cell(0, 10, f'BENEFICIO TOTAL PROYECTADO (Plusvalía + Rentas): ${total_beneficio:,.2f}', 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar Reporte Completo")
with c_down2:
    try: st.download_button("DESCARGAR PDF", create_pdf(), file_name=f"Reporte_Ananda_Lote_{num_lote_selec}.pdf")
    except: st.error("Error PDF")