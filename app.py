import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Ananda Kino | Proyección Feb 2027",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PREMIUM ---
st.markdown("""
    <style>
    /* Fondo Degradado Suave */
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #F0F8FF 0%, #FFFFFF 100%); }
    
    /* Tipografía Corporativa */
    h1, h2, h3, .metric-label { color: #004e92 !important; font-family: 'Helvetica Neue', sans-serif; }
    
    /* Tarjetas de Métricas */
    .metric-card {
        background: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); text-align: center; border: 1px solid #e1e5e8;
        height: 100%;
    }
    .big-number { font-size: 28px; font-weight: 800; color: #004e92; }
    .future-number { font-size: 28px; font-weight: 800; color: #ffc107; }
    
    /* Ficha Técnica */
    .feature-box {
        background-color: #f8f9fa; padding: 15px; border-radius: 10px;
        border-left: 5px solid #004e92; margin-bottom: 10px;
    }
    .amenity-tag {
        display: inline-block; background-color: #e3f2fd; color: #004e92;
        padding: 5px 10px; border-radius: 15px; font-size: 12px; margin: 2px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    # CAMBIA ESTO POR EL NOMBRE EXACTO DE TU ARCHIVO SI ES DIFERENTE
    file_name = "Lista de Precios, Planes Pago y descuentos autorizados 15 Octubre 2025.xlsx - Lista de Precios.csv"
    try:
        df = pd.read_csv(file_name)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    except:
        # Datos Dummy de respaldo
        return pd.DataFrame({
            'lote': range(1, 45),
            'm2': np.random.randint(200, 350, 44),
            'precio_lista_1': np.random.randint(900000, 1200000, 44)
        })

df_raw = load_data()

# --- 2. LOGICA DE NEGOCIO Y PRECIOS ---
def get_incremento_lista(lista_actual):
    # Asumimos 3% de incremento por cada lista que avanza
    return 1 + (0.03 * (lista_actual - 1))

# Sidebar Inputs
try:
    st.sidebar.image("logo.png", use_column_width=True)
except:
    st.sidebar.header("🌊 Ananda Kino")

st.sidebar.markdown("### ⚙️ Configuración Cotización")

# Venta Global (Determina Lista Actual)
total_vendidos = st.sidebar.number_input("Casas Vendidas (Avance Global)", 0, 44, 5)
lista_actual = min(10, (total_vendidos // 3) + 1)

# Lote y Construcción
lote_label = st.sidebar.selectbox("Seleccionar Lote", df_raw['lote'])
row_lote = df_raw[df_raw['lote'] == lote_label].iloc[0]
col_precio_base = [c for c in df_raw.columns if 'precio' in c][0]
precio_base_lista1 = row_lote[col_precio_base]

# Costos Casa
m2_construccion = st.sidebar.number_input("M² Construcción Casa", value=180, help="Promedio modelo 3 recámaras")
costo_construccion = st.sidebar.number_input("Costo Construcción (Obra)", value=2500000, step=50000)

# CÁLCULOS CLAVE
# 1. Precio HOY (Según Lista Actual)
precio_terreno_hoy = precio_base_lista1 * get_incremento_lista(lista_actual)
total_inversion_hoy = precio_terreno_hoy + costo_construccion

# 2. Precio FUTURO (Feb 2027 - Lista 10)
# Lista 10 = Precio Base * Incremento de llegar a la lista 10
precio_terreno_futuro = precio_base_lista1 * get_incremento_lista(10)
total_valor_futuro = precio_terreno_futuro + costo_construccion 

# 3. Plusvalía
plusvalia_preventa = total_valor_futuro - total_inversion_hoy

# Competencia
precio_competencia = 4500000 # Punta Península / Torres
m2_competencia = 110 # Promedio de un depto

# --- INTERFAZ PRINCIPAL ---

st.title("Ananda Kino: Análisis de Inversión y Plusvalía")
st.markdown(f"**Escenario:** Compra en Preventa (Lista {lista_actual}) vs. Entrega Final (Feb 2027)")

# --- SECCIÓN 1: LA COMPARATIVA FINANCIERA (EL GANCHO) ---
st.header("1. Tu Ganancia Patrimonial (Preventa vs Entrega)")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Precio Preventa (HOY)</div>
        <div class="big-number">${total_inversion_hoy:,.0f}</div>
        <div style="font-size:12px; color:grey">Terreno + Casa Equipada</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div class="metric-card" style="border: 2px solid #ffc107;">
        <div class="metric-label">Valor Feb 2027 (Lista 10)</div>
        <div class="future-number">${total_valor_futuro:,.0f}</div>
        <div style="font-size:12px; color:grey">Precio Mercado Terminado</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div class="metric-card" style="background:#e8f5e9; border: 2px solid #28a745;">
        <div class="metric-label" style="color:#28a745!important">Plusvalía Directa</div>
        <div class="big-number" style="color:#28a745">+{plusvalia_preventa:,.0f}</div>
        <div style="font-size:12px; color:#28a745; font-weight:bold">Ganancia por comprar antes</div>
    </div>""", unsafe_allow_html=True)

# Gráfica Comparativa 3 Barras
fig_comp = go.Figure()
fig_comp.add_trace(go.Bar(
    x=['Competencia (Depto)', 'Ananda (HOY)', 'Ananda (Feb 2027)'],
    y=[precio_competencia, total_inversion_hoy, total_valor_futuro],
    marker_color=['#9e9e9e', '#004e92', '#ffc107'],
    text=[f"${precio_competencia/1000000:.1f}M", f"${total_inversion_hoy/1000000:.1f}M", f"${total_valor_futuro/1000000:.1f}M"],
    textposition='auto'
))
fig_comp.update_layout(title="Comparativa de Mercado y Evolución de Precio", height=400)
st.plotly_chart(fig_comp, use_container_width=True)

# --- SECCIÓN 2: EL PRODUCTO (CALIDAD Y M2) ---
st.markdown("---")
st.header("2. Ficha Técnica y Costo Inteligente")

col_prod1, col_prod2 = st.columns([1, 1])

with col_prod1:
    st.subheader("🏡 Residencia Ananda (Casa)")
    st.markdown("""
    <div class="feature-box">
        <b>🛌 3 Recámaras | 🚿 2.5 Baños | 🚗 Cochera Doble | 🏗️ 2 Plantas</b>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**💎 Se entrega con:**")
    st.markdown("""
    - ✅ Piso instalado en toda la casa
    - ✅ Cocina integral con barra y carpintería
    - ✅ Estufa eléctrica y campana
    - ✅ Closets completos y carpintería
    - ✅ Canceles y accesorios de baño
    - ✅ Preparación para Minisplits
    """)

with col_prod2:
    st.subheader("🌳 Amenidades Exclusivas (3,200 m²)")
    amenidades = ["Alberca", "Andador", "Pet Park", "Terraza Club", "Asadores", "Juegos Infantiles", "Firepits", "Seguridad 24/7", "Única Cerrada (Privada)"]
    html_amenidades = "".join([f'<span class="amenity-tag">{a}</span>' for a in amenidades])
    st.markdown(html_amenidades, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🆚 Análisis Precio por M²")
    
    # Cálculo m2
    precio_m2_ananda = total_inversion_hoy / m2_construccion
    precio_m2_competencia = precio_competencia / m2_competencia # Asumiendo 110m2 promedio depto
    
    st.markdown(f"""
    <table style="width:100%; text-align:center; border-collapse: collapse;">
        <tr style="background-color:#f1f1f1; font-weight:bold;">
            <td style="padding:10px;">Concepto</td>
            <td>Ananda (Casa)</td>
            <td>Competencia (Depto)</td>
        </tr>
        <tr>
            <td style="padding:10px; font-weight:bold;">Espacio (m²)</td>
            <td>{m2_construccion} m²</td>
            <td>~{m2_competencia} m²</td>
        </tr>
        <tr style="border-top: 1px solid #ddd;">
            <td style="padding:10px; font-weight:bold; color:#004e92;">Precio por M²</td>
            <td style="font-size:18px; font-weight:bold; color:#28a745;">${precio_m2_ananda:,.0f}</td>
            <td style="font-size:18px; font-weight:bold; color:#d62728;">${precio_m2_competencia:,.0f}</td>
        </tr>
    </table>
    <small>Estás comprando un <b>{((precio_m2_competencia - precio_m2_ananda)/precio_m2_competencia)*100:.0f}% más barato</b> por metro cuadrado.</small>
    """, unsafe_allow_html=True)

# --- SECCIÓN 3: RENTAS Y NEGOCIO (SIMULADOR NETO) ---
st.markdown("---")
st.header("3. Potencial de Negocio (Rentas Vacacionales)")

col_renta_params, col_renta_res = st.columns([1, 2])

with col_renta_params:
    st.markdown("#### Simulador")
    tarifa = st.slider("Tarifa Noche Promedio", 3000, 8000, 4500, step=250)
    ocupacion = st.slider("Ocupación Anual (%)", 20, 80, 40)
    admin_fee = st.slider("Comisión Admin (%)", 15, 30, 20)
    mantenimiento = st.number_input("Costo Mantenimiento Mensual (HOA)", value=2500)

with col_renta_res:
    # Cálculos Anuales
    noches_rentadas = 365 * (ocupacion/100)
    ingreso_bruto = tarifa * noches_rentadas
    costo_admin = ingreso_bruto * (admin_fee/100)
    costo_mto_anual = mantenimiento * 12
    
    ingreso_neto = ingreso_bruto - costo_admin - costo_mto_anual
    roi = (ingreso_neto / total_inversion_hoy) * 100
    
    st.success(f"💰 Ingreso Neto Anual Estimado: **${ingreso_neto:,.0f} MXN**")
    
    # Gráfica Cascada (Waterfall) para mostrar descuentos
    fig_water = go.Figure(go.Waterfall(
        orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["Ingreso Bruto", "Comisión Admin", "Mantenimiento", "NETO BOLSILLO"],
        y = [ingreso_bruto, -costo_admin, -costo_mto_anual, ingreso_neto],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#ef553b"}},
        increasing = {"marker":{"color":"#004e92"}},
        totals = {"marker":{"color":"#28a745"}}
    ))
    fig_water.update_layout(title="Flujo de Efectivo Real (Descontando Gastos)", height=350)
    st.plotly_chart(fig_water, use_container_width=True)

# --- BOTÓN DE DESCARGA (RESUMEN) ---
st.markdown("---")
def generar_resumen():
    texto = f"""
    COTIZACIÓN OFICIAL - ANANDA KINO
    --------------------------------
    Lote Seleccionado: {lote_label}
    Superficie Terreno: {row_lote['m2']} m2
    Superficie Construcción: {m2_construccion} m2
    
    PRECIO Y PLUSVALÍA
    --------------------------------
    Precio Lista Actual (Preventa): ${total_inversion_hoy:,.2f}
    Precio Proyectado Feb 2027 (Lista 10): ${total_valor_futuro:,.2f}
    PLUSVALÍA ESTIMADA: ${plusvalia_preventa:,.2f}
    
    FICHA TÉCNICA
    --------------------------------
    Casa 3 Recámaras, 2.5 Baños, Cochera Doble.
    Incluye: Cocina, Closets, Minisplits, Piso, Carpintería.
    Amenidades: Alberca, Pet Park, Seguridad.
    
    PROYECCIÓN RENTAS (ANUAL)
    --------------------------------
    Escenario Ocupación: {ocupacion}%
    Tarifa Noche: ${tarifa:,.2f}
    Ingreso Neto (Libre de gastos): ${ingreso_neto:,.2f}
    
    *Cotización informativa sujeta a disponibilidad y cambios de precio.*
    """
    return texto

resumen_txt = generar_resumen()
st.download_button(
    label="📥 Descargar Resumen de Cotización (TXT)",
    data=resumen_txt,
    file_name=f"Cotizacion_Ananda_{lote_label}.txt",
    mime="text/plain"
)
