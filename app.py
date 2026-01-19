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
    
    /* Contenedores */
    .section-box { background-color: white; padding: 20px; border-radius: 12px; border: 1px solid #eee; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }
    
    /* Tabla */
    .comp-table { width: 100%; border-collapse: collapse; font-size: 14px; }
    .comp-table th { background-color: #004e92; color: white; padding: 12px; text-align: center; }
    .comp-table td { border-bottom: 1px solid #ddd; padding: 10px; text-align: center; color: #333; }
    
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

# Precio Futuro
col_l10 = next((c for c in df_raw.columns if 'lista_10' in c), None)
precio_final_mercado = clean_currency(row_lote[col_l10]) if col_l10 else precio_lista_actual * 1.30
plusvalia_preventa = precio_final_mercado - precio_lista_actual

st.sidebar.markdown("---")
st.sidebar.info(f"📋 **Ficha Lote {num_lote_selec}:**\n- Terreno: {m2_terreno:.0f} m²\n- Construcción: {m2_construccion:.0f} m²")

# --- 3. DASHBOARD PRINCIPAL ---
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
with c3: st.markdown(f"""<div class="metric-card" style="background:#f0fff4; border:2px solid #28a745;"><div>Plusvalía Ganada</div><div class="big-number" style="color:#28a745">+${plusvalia_preventa:,.0f}</div><small>Al cierre de preventa</small></div>""", unsafe_allow_html=True)

# --- 4. COMPARATIVA ---
st.markdown("---")
st.header("🏆 Ananda vs El Mercado")

# Datos
precio_m2_ananda = precio_lista_actual / m2_construccion if m2_construccion > 0 else 0
data_comp = [
    {"Proyecto": "ANANDA", "Precio": precio_lista_actual, "M2": m2_construccion, "Tipo": "Casa", "PrecioM2": precio_m2_ananda},
    {"Proyecto": "Punta Península", "Precio": 4850000, "M2": 100, "Tipo": "Depto", "PrecioM2": 48500},
    {"Proyecto": "HAX", "Precio": 3600000, "M2": 70, "Tipo": "Depto", "PrecioM2": 51428},
    {"Proyecto": "Azaluma", "Precio": 4100000, "M2": 85, "Tipo": "Depto", "PrecioM2": 48235}
]
df_comp = pd.DataFrame(data_comp)

col_comp_graf, col_comp_info = st.columns([1, 1])

with col_comp_graf:
    st.subheader("Costo Real por M²")
    fig_bar = go.Figure(go.Bar(
        x=df_comp.sort_values('PrecioM2')['Proyecto'], 
        y=df_comp.sort_values('PrecioM2')['PrecioM2'],
        marker_color=['#28a745' if 'ANANDA' in p else '#ef553b' for p in df_comp.sort_values('PrecioM2')['Proyecto']],
        text=[f"${x:,.0f}" for x in df_comp.sort_values('PrecioM2')['PrecioM2']],
        textposition='auto'
    ))
    fig_bar.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', yaxis_title="Pesos por Metro Cuadrado")
    st.plotly_chart(fig_bar, use_container_width=True)

with col_comp_info:
    st.subheader("Tabla Comparativa")
    st.markdown(f"""
    <table class="comp-table">
        <tr><th>Proyecto</th><th>Tipo</th><th>Precio Aprox</th><th>Precio M²</th></tr>
        {''.join([f"<tr {'style=background-color:#e3f2fd;font-weight:bold' if 'ANANDA' in r['Proyecto'] else ''}><td>{r['Proyecto']}</td><td>{r['Tipo']}</td><td>${r['Precio']:,.0f}</td><td>${r['PrecioM2']:,.0f}</td></tr>" for i,r in df_comp.sort_values('PrecioM2').iterrows()])}
    </table>
    """, unsafe_allow_html=True)
    st.info("💡 **Dato:** En Ananda pagas casi la mitad por metro cuadrado que en los desarrollos verticales, y eres dueño de la tierra.")

# --- 5. RENTAS (REGRESO AL PANEL PRINCIPAL) ---
st.markdown("---")
st.header("📈 Simulador de Negocio (Rentas)")
st.markdown('<div class="section-box">', unsafe_allow_html=True)

col_inputs, col_results = st.columns([1, 2])

with col_inputs:
    st.markdown("#### Variables")
    tarifa = st.number_input("Tarifa Noche Promedio:", value=4500, step=500)
    ocupacion_pct = st.slider("Ocupación Anual (%):", 20, 80, 45)
    
    st.markdown("#### Gastos")
    comision_pct = st.slider("Comisión Administración (%):", 15, 35, 25) / 100
    mto_mensual = st.number_input("Mantenimiento Mensual ($):", value=2000)

with col_results:
    # Cálculos
    ingreso_bruto = tarifa * 365 * (ocupacion_pct/100)
    gasto_admin = ingreso_bruto * comision_pct
    gasto_mto = mto_mensual * 12
    total_gastos = gasto_admin + gasto_mto
    neto_anual = ingreso_bruto - total_gastos
    roi = (neto_anual / precio_lista_actual) * 100
    
    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingreso Bruto", f"${ingreso_bruto:,.0f}")
    m2.metric("Total Gastos", f"-${total_gastos:,.0f}")
    m3.metric("Neto Bolsillo", f"${neto_anual:,.0f}", delta=f"ROI {roi:.1f}%")
    
    # Gráfica Dona
    fig_pie = go.Figure(data=[go.Pie(
        labels=['Tu Ganancia', 'Comisión Admin', 'Mantenimiento'],
        values=[neto_anual, gasto_admin, gasto_mto],
        hole=.4, marker_colors=['#28a745', '#ef553b', '#ffa600']
    )])
    fig_pie.update_layout(height=250, margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pie, use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- 6. PROYECCIÓN 5 AÑOS ---
st.subheader("💰 Tu Patrimonio en 5 Años (2028-2032)")
st.caption("Considerando Plusvalía (8% anual) + Ingresos por Renta (Inflación 5%).")

years = range(2028, 2033)
inflacion = 0.05
plusvalia_anual = 0.08

data_proy = []
val_prop = precio_final_mercado
acum_rentas = 0

for i, y in enumerate(years):
    val_prop = val_prop * (1 + plusvalia_anual)
    
    t_act = tarifa * ((1+inflacion)**i)
    bruto = t_act * 365 * (ocupacion_pct/100)
    gastos = (bruto * comision_pct) + (mto_mensual * 12 * ((1+inflacion)**i))
    neto = bruto - gastos
    acum_rentas += neto
    
    data_proy.append({"Año": y, "Valor Propiedad": val_prop, "Renta Acumulada": acum_rentas})

df_proy = pd.DataFrame(data_proy)
df_proy['Patrimonio Total'] = df_proy['Valor Propiedad'] + df_proy['Renta Acumulada']

fig_area = px.area(df_proy, x="Año", y=["Valor Propiedad", "Renta Acumulada"], 
                  color_discrete_map={"Valor Propiedad":"#004e92", "Renta Acumulada":"#28a745"})
st.plotly_chart(fig_area, use_container_width=True)

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
        self.cell(0, 10, 'REPORTE FINANCIERO', 0, 1, 'R')
        self.ln(10)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, 'Ananda Kino - Confidencial', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    
    # 1. Detalles
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, f'Propiedad: Casa en Lote {num_lote_selec}', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f'Terreno: {m2_terreno:.2f} m2 | Construcción: {m2_construccion:.2f} m2', 0, 1)
    
    # 2. Precios
    pdf.ln(5)
    pdf.set_fill_color(240, 245, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 8, 'Inversión', 1, 0, 'L', 1)
    pdf.cell(60, 8, 'Monto', 1, 1, 'R', 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(100, 8, f'Precio Preventa (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 8, f'${precio_lista_actual:,.2f}', 1, 1, 'R')
    pdf.cell(100, 8, 'Valor Futuro (Feb 2027)', 1, 0)
    pdf.cell(60, 8, f'${precio_final_mercado:,.2f}', 1, 1, 'R')
    
    # 3. Competencia
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, 'Comparativa de Mercado', 0, 1)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.set_fill_color(220)
    pdf.cell(50, 8, 'Proyecto', 1, 0, 'C', 1)
    pdf.cell(40, 8, 'Precio Aprox', 1, 0, 'C', 1)
    pdf.cell(40, 8, 'Precio M2', 1, 1, 'C', 1)
    pdf.set_font('Arial', '', 10)
    for index, row in df_comp.iterrows():
        pdf.cell(50, 8, row['Proyecto'], 1, 0)
        pdf.cell(40, 8, f"${row['Precio']:,.0f}", 1, 0, 'R')
        pdf.cell(40, 8, f"${row['PrecioM2']:,.0f}", 1, 1, 'R')
        
    # 4. Rentas
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, 'Negocio de Rentas (Estimado)', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0)
    pdf.multi_cell(0, 6, f"Escenario: Ocupación {ocupacion_pct}% | Tarifa ${tarifa:,.0f} | Admin {comision_pct*100}% | Mto ${mto_mensual:,.0f}")
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 8, 'Ingreso Neto Anual (Bolsillo):', 1, 0)
    pdf.cell(60, 8, f'${neto_anual:,.2f}', 1, 1, 'R')
    
    # 5. Proyección
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, 'Proyección Patrimonial (5 Años)', 0, 1)
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(0)
    pdf.set_fill_color(220)
    pdf.cell(30, 8, 'Año', 1, 0, 'C', 1)
    pdf.cell(50, 8, 'Valor Propiedad', 1, 0, 'C', 1)
    pdf.cell(50, 8, 'Renta Acumulada', 1, 0, 'C', 1)
    pdf.cell(50, 8, 'Patrimonio Total', 1, 1, 'C', 1)
    pdf.set_font('Arial', '', 10)
    for row in data_proy:
        pdf.cell(30, 8, str(row['Año']), 1, 0, 'C')
        pdf.cell(50, 8, f"${row['Valor Propiedad']:,.0f}", 1, 0, 'R')
        pdf.cell(50, 8, f"${row['Renta Acumulada']:,.0f}", 1, 0, 'R')
        pdf.cell(50, 8, f"${row['Patrimonio Total']:,.0f}", 1, 1, 'R')

    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar PDF Completo")
with c_down2:
    try: st.download_button("DESCARGAR PDF", create_pdf(), file_name=f"Reporte_Ananda_{num_lote_selec}.pdf")
    except: st.error("Error PDF")