import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF

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
    .comp-table th { background-color: #004e92; color: white; padding: 12px; text-align: left; }
    .comp-table td { border-bottom: 1px solid #ddd; padding: 10px; text-align: left; color: #333; }
    .highlight { background-color: #e3f2fd; font-weight: bold; color: #004e92; }
    .stButton>button { background-color: #004e92; color: white; font-weight: bold; height: 50px; width: 100%; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE LIMPIEZA (ESTO ARREGLA TU ERROR) ---
def clean_currency(val):
    """Convierte textos como '$3,500,000' a numeros reales 3500000.0"""
    if pd.isna(val): return 0.0
    s = str(val)
    s = s.replace('$', '').replace(',', '').replace(' ', '')
    try:
        return float(s)
    except:
        return 0.0

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    file_name = "precios.csv"
    try:
        # Probamos leer normal (header=0)
        df = pd.read_csv(file_name)
        
        # Detectamos si la fila 0 son los encabezados reales (pasa mucho)
        cols_str = "".join([str(c).lower() for c in df.columns])
        if "lote" not in cols_str and "precio" not in cols_str:
            # Si no están arriba, probamos con la fila 1
            df = pd.read_csv(file_name, header=1)

        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '').str.replace('(', '').str.replace(')', '')
        
        # BUSCAR COLUMNA LOTE
        col_lote = None
        for col in df.columns:
            if 'lote' in col or 'unidad' in col:
                col_lote = col
                break
        
        if col_lote:
            df.rename(columns={col_lote: 'lote'}, inplace=True)
            # Limpieza de Lotes
            df['lote'] = pd.to_numeric(df['lote'], errors='coerce')
            df = df.dropna(subset=['lote'])
            df['lote'] = df['lote'].astype(int)
            df = df[(df['lote'] >= 1) & (df['lote'] <= 44)]
            df = df.sort_values('lote')
            
            # IDENTIFICAR VENDIDOS (Busca columna cliente/status)
            col_status = None
            for c in df.columns:
                if 'cliente' in c or 'estatus' in c or 'estado' in c:
                    col_status = c
                    break
            
            if col_status:
                # Si tiene texto, es vendido
                df['status'] = df[col_status].apply(lambda x: 'Vendido' if pd.notnull(x) and str(x).strip() not in ['', 'nan'] else 'Disponible')
            else:
                df['status'] = 'Disponible'
            
            return df
        else:
            return None
    except Exception as e:
        return None

df_raw = load_data()

# DATOS RESPALDO
if df_raw is None:
    st.error("⚠️ Error en archivo. Usando datos base.")
    df_raw = pd.DataFrame({'lote': range(1, 45), 'status': ['Disponible']*44})

# --- 2. SIDEBAR ---
try: st.sidebar.image("logo.png", use_column_width=True)
except: st.sidebar.header("🏠 Ananda Residencial")

st.sidebar.header("1. Configuración")
lista_seleccionada = st.sidebar.selectbox("Lista Vigente:", range(1, 11), index=0)

# Selector de Lote con Status
opciones_lotes = df_raw.apply(lambda x: f"Lote {x['lote']} ({x['status']})", axis=1).tolist()
lote_str_selec = st.sidebar.selectbox("Seleccionar Lote:", opciones_lotes)
num_lote_selec = int(lote_str_selec.split(' ')[1])
row_lote = df_raw[df_raw['lote'] == num_lote_selec].iloc[0]

# --- LÓGICA DE PRECIOS SEGURA ---
# Buscamos columnas de m2
col_m2 = [c for c in df_raw.columns if 'm2' in c and 'privativo' in c]
if not col_m2: col_m2 = [c for c in df_raw.columns if 'm2' in c or 'terreno' in c]
m2_terreno = clean_currency(row_lote.get(col_m2[0], 216.0)) if col_m2 else 216.0

col_const = [c for c in df_raw.columns if 'construccion' in c and 'total' in c]
m2_construccion = clean_currency(row_lote.get(col_const[0], 128.8)) if col_const else 128.8

# Búsqueda PRECIO LISTA
col_precio_lista = None
# Intenta buscar 'lista_X'
for col in df_raw.columns:
    if f"lista_{lista_seleccionada}" in col:
        col_precio_lista = col
        break

if col_precio_lista:
    precio_lista_actual = clean_currency(row_lote[col_precio_lista])
else:
    # Si no halla la columna exacta, busca la lista 1 y proyecta
    col_l1 = [c for c in df_raw.columns if 'lista_1' in c]
    base = clean_currency(row_lote[col_l1[0]]) if col_l1 else 3300000.0
    precio_lista_actual = base * (1 + 0.03 * (lista_seleccionada - 1))

# Precio Futuro (Lista 10)
col_l10 = [c for c in df_raw.columns if 'lista_10' in c]
if col_l10:
    precio_final_mercado = clean_currency(row_lote[col_l10[0]])
else:
    precio_final_mercado = precio_lista_actual * 1.30

plusvalia = precio_final_mercado - precio_lista_actual

st.sidebar.markdown("---")
st.sidebar.info(f"📋 **Ficha Lote {num_lote_selec}:**\n- Terreno: {m2_terreno:.0f} m²\n- Construcción: {m2_construccion:.0f} m²")

# --- 3. PANEL PRINCIPAL ---
st.title(f"Residencia Ananda | Lote {num_lote_selec}")

if "Vendido" in lote_str_selec:
    st.warning("⛔ LOTE VENDIDO / RESERVADO")

st.markdown(f"**Estado:** Preventa (Lista {lista_seleccionada}) | **Entrega:** Casa Terminada")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Precio Preventa (HOY)</div>
        <div class="big-number">${precio_lista_actual:,.0f}</div>
        <small>Casa + Terreno</small>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card" style="border: 2px solid #ffc107; background:#fffdf5">
        <div class="metric-label">Valor Final (Lista 10)</div>
        <div class="future-number">${precio_final_mercado:,.0f}</div>
        <small>Al terminar preventa</small>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card" style="background:#f0fff4; border: 2px solid #28a745;">
        <div class="metric-label" style="color:#28a745!important">Plusvalía Proyectada</div>
        <div class="big-number" style="color:#28a745">+${plusvalia:,.0f}</div>
        <small>Ganancia inmediata</small>
    </div>""", unsafe_allow_html=True)

# --- 4. COMPARATIVA DE MERCADO (DATOS REALES) ---
st.markdown("---")
st.header("🏆 Ananda vs. Competencia en Kino")
st.caption("Comparativa directa con desarrollos actuales.")

col_comp_graf, col_comp_tabla = st.columns([1, 1])

# Cálculo M2 Real
precio_m2_ananda = precio_lista_actual / m2_construccion if m2_construccion > 0 else 0
# Datos de Mercado Proporcionados
precio_m2_punta = 4500000 / 90 # Aprox Condo
precio_m2_caay = 3800000 / 85  # Aprox Depto

with col_comp_graf:
    st.subheader("Costo Eficiente por M²")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Ananda (Casa)', 'Punta Península', 'CAAY / Marenza'],
        y=[precio_m2_ananda, precio_m2_punta, precio_m2_caay],
        marker_color=['#004e92', '#d62728', '#ff7f0e'],
        text=[f"${precio_m2_ananda:,.0f}", f"${precio_m2_punta:,.0f}", f"${precio_m2_caay:,.0f}"],
        textposition='auto'
    ))
    fig.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', title="Tu inversión compra más metros en Ananda")
    st.plotly_chart(fig, use_container_width=True)

with col_comp_tabla:
    st.markdown("""
    <table class="comp-table">
        <thead>
            <tr>
                <th>Desarrollo</th>
                <th>Producto</th>
                <th>Rango Precio*</th>
                <th>Diferenciador</th>
            </tr>
        </thead>
        <tbody>
            <tr class="highlight">
                <td>🌊 ANANDA</td>
                <td>Casa + Lote</td>
                <td>$3.3M - $4.0M</td>
                <td>Privacidad total, Cochera propia</td>
            </tr>
            <tr>
                <td>Punta Península</td>
                <td>Condo / Resort</td>
                <td>$4.1M - $5.0M</td>
                <td>Frente de Playa / Ticket Alto</td>
            </tr>
            <tr>
                <td>CAAY</td>
                <td>Deptos</td>
                <td>$3.5M+</td>
                <td>Compacto / Frente al mar</td>
            </tr>
            <tr>
                <td>Marenza</td>
                <td>Torres</td>
                <td>$3.2M+</td>
                <td>Sin privacidad de casa</td>
            </tr>
            <tr>
                <td>Vistas Reserva</td>
                <td>Lotes</td>
                <td>Bajo (Solo Lote)</td>
                <td>Debes construir tú mismo</td>
            </tr>
        </tbody>
    </table>
    <small>*Precios de mercado estimados oct 2025.</small>
    """, unsafe_allow_html=True)

# --- 5. ROI 5 AÑOS (CON DATOS REALES) ---
st.markdown("---")
st.header("📈 Negocio Patrimonial (2028 - 2032)")
st.caption("Proyección de rentas vacacionales con inicio de operaciones en 2028.")

col_r1, col_r2 = st.columns([1, 2])
with col_r1:
    st.markdown("#### Variables de Renta")
    tarifa_2028 = st.number_input("Tarifa Noche (2028):", value=5500, step=500)
    ocupacion = st.slider("Ocupación Anual:", 30, 70, 45) / 100
    
    st.markdown("#### Costos Operativos")
    comision_admin = st.slider("Admin. Propiedades (%):", 20, 30, 25) / 100
    mto_mensual = st.number_input("Mantenimiento Mensual:", value=2000)

with col_r2:
    years = range(2028, 2033)
    netos = []
    acumulados = []
    suma = 0
    inflacion = 0.05
    
    for i, y in enumerate(years):
        t_actual = tarifa_2028 * ((1+inflacion)**i)
        bruto = t_actual * 365 * ocupacion
        
        gastos_admin = bruto * comision_admin
        gastos_mto = mto_mensual * 12 * ((1+inflacion)**i)
        
        neto = bruto - gastos_admin - gastos_mto
        netos.append(neto)
        suma += neto
        acumulados.append(suma)
    
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Bar(x=list(years), y=netos, name='Flujo Neto Anual', marker_color='#28a745', text=[f"${x/1000:,.0f}k" for x in netos]))
    fig_roi.add_trace(go.Scatter(x=list(years), y=acumulados, name='Acumulado', mode='lines+markers', line=dict(color='#004e92')))
    fig_roi.update_layout(height=400, title="Flujo de Efectivo Libre (Después de Gastos)", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_roi, use_container_width=True)
    
    c_res1, c_res2 = st.columns(2)
    c_res1.metric("Ingreso Neto Año 1", f"${netos[0]:,.0f}")
    c_res2.metric("Recuperación a 5 Años", f"${acumulados[-1]:,.0f}")

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
        self.cell(0, 10, 'COTIZACIÓN & NEGOCIO', 0, 1, 'R')
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
    
    # Precios
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(100, 10, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 10, 'Valor', 1, 1, 'R', 1)
    pdf.cell(100, 10, f'Precio Preventa (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 10, f'${precio_lista_actual:,.2f}', 1, 1, 'R')
    pdf.cell(100, 10, 'Valor Futuro (Lista 10)', 1, 0)
    pdf.cell(60, 10, f'${precio_final_mercado:,.2f}', 1, 1, 'R')
    
    # ROI
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Proyeccion Financiera (2028-2032)', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(100, 10, 'Utilidad Neta Año 1:', 1, 0)
    pdf.cell(60, 10, f'${netos[0]:,.2f}', 1, 1, 'R')
    pdf.cell(100, 10, 'Acumulado 5 Años:', 1, 0)
    pdf.cell(60, 10, f'${acumulados[-1]:,.2f}', 1, 1, 'R')

    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar PDF")
with c_down2:
    try: st.download_button("DESCARGAR PDF", create_pdf(), file_name=f"Cotizacion_{num_lote_selec}.pdf")
    except: st.error("Error PDF")