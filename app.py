import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF
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
    .comp-table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 14px; }
    .comp-table th { background-color: #004e92; color: white; padding: 12px; text-align: left; }
    .comp-table td { border-bottom: 1px solid #ddd; padding: 10px; text-align: left; color: #333; }
    .highlight { background-color: #e3f2fd; font-weight: bold; color: #004e92; }
    
    .stButton>button { background-color: #004e92; color: white; font-weight: bold; height: 50px; width: 100%; border-radius: 8px;}
    </style>
    """, unsafe_allow_html=True)

# --- 1. CARGA DE DATOS (LECTURA INTELIGENTE) ---
@st.cache_data
def load_data():
    file_name = "precios.csv"
    try:
        # Intentamos leer con header=1 porque tu archivo tiene títulos en la fila 0
        df = pd.read_csv(file_name, header=1)
        
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '').str.replace('(', '').str.replace(')', '')
        
        # 1. ENCONTRAR COLUMNA LOTE
        col_lote = None
        for col in df.columns:
            if col == 'lote' or 'lote' in col:
                col_lote = col
                break
        
        if col_lote:
            df.rename(columns={col_lote: 'lote'}, inplace=True)
            
            # 2. LIMPIEZA ESTRICTA (SOLO 1-44)
            df['lote'] = pd.to_numeric(df['lote'], errors='coerce') # Convierte a numero, errores son NaN
            df = df.dropna(subset=['lote']) # Borra vacíos
            df['lote'] = df['lote'].astype(int) # Quita el .0
            df = df[(df['lote'] >= 1) & (df['lote'] <= 44)] # Solo del 1 al 44
            df = df.sort_values('lote')
            
            # 3. IDENTIFICAR VENDIDOS (Columna Cliente)
            # Si la columna 'cliente' tiene texto, es vendido.
            if 'cliente' in df.columns:
                df['status'] = df['cliente'].apply(lambda x: 'Vendido' if pd.notnull(x) and str(x).strip() != '' else 'Disponible')
            else:
                df['status'] = 'Disponible'
            
            return df
        else:
            return None
    except Exception as e:
        # st.error(f"Error detalle: {e}") 
        return None

df_raw = load_data()

# DATOS DE RESPALDO (Por si falla la lectura)
if df_raw is None:
    st.error("⚠️ No se pudo leer correctamente 'precios.csv'. Usando datos simulados.")
    df_raw = pd.DataFrame({
        'lote': range(1, 45),
        'status': ['Disponible']*44,
        'total_terreno': [216.0] * 44,
        'total_construccion': [128.8] * 44,
    })
    # Precios simulados
    for i in range(1, 11):
        df_raw[f'lista_{i}'] = 3359776.0 * (1 + (i-1)*0.03)

# --- 2. SIDEBAR ---
try: st.sidebar.image("logo.png", use_column_width=True)
except: st.sidebar.header("🏠 Ananda Residencial")

st.sidebar.header("1. Configuración")
lista_seleccionada = st.sidebar.selectbox("Lista Vigente:", range(1, 11), index=0)

# FILTRO DE LOTES (Mostramos status en el selector)
# Creamos una lista de opciones con formato "Lote X - Status"
opciones_lotes = df_raw.apply(lambda x: f"Lote {x['lote']} ({x['status']})", axis=1).tolist()
lote_str_selec = st.sidebar.selectbox("Seleccionar Lote:", opciones_lotes)

# Extraemos el número de lote de la selección
num_lote_selec = int(lote_str_selec.split(' ')[1])
row_lote = df_raw[df_raw['lote'] == num_lote_selec].iloc[0]

# --- LECTURA DE PRECIOS Y M2 ---
# Intentamos buscar las columnas exactas
m2_terreno = float(row_lote.get('total_terreno', 216.0))
m2_construccion = float(row_lote.get('total_construccion', 128.8))

# Búsqueda dinámica de la columna de precio según la lista seleccionada
# Buscamos columnas que contengan "lista_X"
col_precio_lista = None
possible_col_name = f"lista_{lista_seleccionada}"
for col in df_raw.columns:
    if f"lista_{lista_seleccionada}" in col:
        col_precio_lista = col
        break

# Si no encuentra la columna exacta, calculamos estimado
if col_precio_lista:
    precio_lista_actual = float(row_lote[col_precio_lista])
else:
    # Fallback: Buscar lista 1 y aplicar incremento
    col_lista_1 = [c for c in df_raw.columns if "lista_1" in c][0]
    base = float(row_lote[col_lista_1])
    precio_lista_actual = base * (1 + 0.03 * (lista_seleccionada - 1))

# Precio Futuro (Lista 10)
col_lista_10 = None
for col in df_raw.columns:
    if "lista_10" in col:
        col_lista_10 = col
        break
if col_lista_10:
    precio_final_mercado = float(row_lote[col_lista_10])
else:
    precio_final_mercado = precio_lista_actual * 1.30 # Estimado

plusvalia = precio_final_mercado - precio_lista_actual

st.sidebar.markdown("---")
st.sidebar.info(f"📋 **Ficha Técnica:**\n\n- Lote: {row_lote['lote']}\n- Terreno: {m2_terreno:.2f} m²\n- Construcción: {m2_construccion:.2f} m²")

# --- 3. PANEL PRINCIPAL ---
st.title(f"Residencia Ananda | Lote {num_lote_selec}")

if row_lote['status'] == 'Vendido':
    st.error("⛔ ESTE LOTE YA ESTÁ VENDIDO")
else:
    st.markdown(f"**Estado:** Preventa (Lista {lista_seleccionada}) | **Entrega:** Casa Terminada")

# TARJETAS DE PRECIO
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
st.header("🏆 Análisis Competitivo")
st.caption("Ananda vs. La oferta actual en Bahía de Kino")

col_comp_graf, col_comp_tabla = st.columns([1, 1])

# Datos Competencia Reales
precio_m2_ananda = precio_lista_actual / m2_construccion
# Promedios estimados de la info proporcionada
comp_punta = 4500000 / 90 # Condo chico
comp_caay = 3800000 / 85
comp_marenza = 3500000 / 85

with col_comp_graf:
    st.subheader("Costo por M² (Construcción)")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Ananda (Casa)', 'Punta Península', 'CAAY / Marenza'],
        y=[precio_m2_ananda, comp_punta, comp_caay],
        marker_color=['#004e92', '#d62728', '#ff7f0e'],
        text=[f"${precio_m2_ananda:,.0f}", f"${comp_punta:,.0f}", f"${comp_caay:,.0f}"],
        textposition='auto'
    ))
    fig.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', title="Tu dinero rinde más en Ananda")
    st.plotly_chart(fig, use_container_width=True)

with col_comp_tabla:
    st.markdown("""
    <table class="comp-table">
        <thead>
            <tr>
                <th>Desarrollo</th>
                <th>Producto</th>
                <th>Rango Precio</th>
                <th>Factor Clave</th>
            </tr>
        </thead>
        <tbody>
            <tr class="highlight">
                <td>🌊 ANANDA</td>
                <td>Casa + Lote</td>
                <td>$3.3M - $4.0M</td>
                <td>Privacidad, Cochera Doble, Amenidades</td>
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
                <td>Proyecto compacto</td>
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
                <td>Bajo (Lote)</td>
                <td>Debes construir por tu cuenta</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

# --- 5. SIMULADOR DE ROI (5 AÑOS) ---
st.markdown("---")
st.header("📈 Proyección de Negocio (2028 - 2032)")
st.caption("Rendimiento estimado operando como renta vacacional.")

col_r1, col_r2 = st.columns([1, 2])

with col_r1:
    st.markdown("#### Configuración")
    tarifa_2028 = st.number_input("Tarifa Noche (2028):", value=5500, step=500)
    ocupacion = st.slider("Ocupación Promedio:", 30, 70, 45) / 100
    
    st.markdown("#### Costos Operativos")
    comision_admin = st.slider("Comisión Administración (%):", 20, 30, 25) / 100
    mto_mensual = st.number_input("Mantenimiento Mensual ($):", value=2000)

with col_r2:
    years = range(2028, 2033)
    flujos_netos = []
    acumulado = []
    suma_acum = 0
    inflacion = 0.05
    
    for i, y in enumerate(years):
        # Aumento de tarifa anual
        t_actual = tarifa_2028 * ((1+inflacion)**i)
        ingreso_bruto = t_actual * 365 * ocupacion
        
        # Gastos
        gasto_admin = ingreso_bruto * comision_admin
        gasto_mto = mto_mensual * 12 * ((1+inflacion)**i)
        
        neto = ingreso_bruto - gasto_admin - gasto_mto
        flujos_netos.append(neto)
        suma_acum += neto
        acumulado.append(suma_acum)
    
    # Gráfica
    fig_roi = go.Figure()
    fig_roi.add_trace(go.Bar(
        x=list(years), y=flujos_netos, name='Utilidad Neta Anual', marker_color='#28a745',
        text=[f"${x/1000:,.0f}k" for x in flujos_netos], textposition='auto'
    ))
    fig_roi.add_trace(go.Scatter(
        x=list(years), y=acumulado, name='Utilidad Acumulada', mode='lines+markers',
        line=dict(color='#004e92', width=3)
    ))
    fig_roi.update_layout(height=400, title="Flujo de Efectivo Proyectado", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig_roi, use_container_width=True)
    
    col_res1, col_res2 = st.columns(2)
    col_res1.metric("Ingreso Neto Año 1 (2028)", f"${flujos_netos[0]:,.0f}")
    col_res2.metric("Recuperación Total (5 Años)", f"${acumulado[-1]:,.0f}")

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
    
    # Tabla Precios
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(100, 10, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 10, 'Valor', 1, 1, 'R', 1)
    pdf.cell(100, 10, f'Precio Preventa (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 10, f'${precio_lista_actual:,.2f}', 1, 1, 'R')
    pdf.cell(100, 10, 'Valor Futuro (Lista 10)', 1, 0)
    pdf.cell(60, 10, f'${precio_final_mercado:,.2f}', 1, 1, 'R')
    
    # Rentas
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Proyección Financiera (5 Años)', 0, 1)
    pdf.set_font('Arial', '', 12)
    pdf.cell(100, 10, 'Utilidad Neta Año 1 (2028):', 1, 0)
    pdf.cell(60, 10, f'${flujos_netos[0]:,.2f}', 1, 1, 'R')
    pdf.cell(100, 10, 'Acumulado 5 Años:', 1, 0)
    pdf.cell(60, 10, f'${acumulado[-1]:,.2f}', 1, 1, 'R')

    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar PDF")
with c_down2:
    try: st.download_button("DESCARGAR PDF", create_pdf(), file_name=f"Cotizacion_Lote_{num_lote_selec}.pdf")
    except: st.error("Error PDF")