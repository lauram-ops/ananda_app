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

# --- 1. CARGA DE DATOS ---
@st.cache_data
def load_data():
    file_name = "precios.csv"
    try:
        df = pd.read_csv(file_name)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '').str.replace('no_', '')
        
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
            return df
        else:
            return None
    except:
        return None

df_raw = load_data()

if df_raw is None:
    st.error("⚠️ Usando datos base (Revisa precios.csv).")
    df_raw = pd.DataFrame({
        'lote': range(1, 45),
        'm2': [200 + (i*2) for i in range(44)],
        'm2_construccion': [160] * 44,
        'precio_lista_1': [900000 + (i*10000) for i in range(44)]
    })

# --- 2. SIDEBAR ---
try: st.sidebar.image("logo.png", use_column_width=True)
except: st.sidebar.header("🏠 Ananda Residencial")

st.sidebar.header("1. Configuración")
lista_seleccionada = st.sidebar.selectbox("Lista Vigente:", range(1, 11), index=0)

lote_label = st.sidebar.selectbox("Seleccionar Lote:", df_raw['lote'])
row_lote = df_raw[df_raw['lote'] == lote_label].iloc[0]

m2_terreno = float(row_lote.get('m2', 200))
m2_construccion_default = float(row_lote.get('m2_construccion', 180)) 

cols_precio = [c for c in df_raw.columns if 'precio' in c or 'valor' in c or 'lista_1' in c]
col_base = cols_precio[0] if cols_precio else 'precio_lista_1'
precio_base_lista1 = float(row_lote.get(col_base, 900000))

incremento_pct = 0.03
precio_terreno_actual = precio_base_lista1 * (1 + (incremento_pct * (lista_seleccionada - 1)))
precio_terreno_futuro = precio_base_lista1 * (1 + (incremento_pct * 9))

st.sidebar.markdown("---")
st.sidebar.header("2. Casa Terminada")
st.sidebar.caption("Se entrega residencia construida y equipada.")
costo_m2_const = st.sidebar.number_input("Valor Construcción por m²:", value=14500, step=500)
m2_const_final = st.sidebar.number_input("M² de Construcción:", value=int(m2_construccion_default))
valor_construccion = m2_const_final * costo_m2_const

# TOTALES
precio_preventa_total = precio_terreno_actual + valor_construccion
precio_final_mercado = precio_terreno_futuro + valor_construccion
plusvalia = precio_final_mercado - precio_preventa_total

# --- 3. PANEL PRINCIPAL ---
st.title(f"Residencia Ananda | Lote {lote_label}")
st.markdown(f"**Estado:** Preventa (Lista {lista_seleccionada}) | **Entrega:** Casa Terminada")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f"""<div class="metric-card">
        <div class="metric-label">Precio Preventa (HOY)</div>
        <div class="big-number">${precio_preventa_total:,.0f}</div>
        <small>Terreno + Casa</small>
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

# --- 4. COMPARATIVA DE MERCADO ---
st.markdown("---")
st.header("🏆 Análisis Competitivo")
st.caption("Comparativa directa contra desarrollos verticales y lotes en la zona.")

col_comp_graf, col_comp_tabla = st.columns([1, 1])

# Datos Competencia (Punta Península como referencia alta)
competencia_precio = 4500000 
competencia_m2 = 90 # Promedio depto
precio_m2_comp = competencia_precio / competencia_m2
precio_m2_ananda = precio_preventa_total / m2_const_final

with col_comp_graf:
    st.subheader("Costo Real por M²")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=['Ananda (Casa)', 'Punta Península / CAAY'],
        y=[precio_m2_ananda, precio_m2_comp],
        marker_color=['#004e92', '#d62728'],
        text=[f"${precio_m2_ananda:,.0f}", f"${precio_m2_comp:,.0f}"],
        textposition='auto'
    ))
    fig.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

with col_comp_tabla:
    st.markdown("""
    <table class="comp-table">
        <thead>
            <tr>
                <th>Desarrollo</th>
                <th>Producto</th>
                <th>Precio Aprox.</th>
                <th>Ventaja/Desventaja</th>
            </tr>
        </thead>
        <tbody>
            <tr class="highlight">
                <td>🌊 ANANDA</td>
                <td>Casa + Lote</td>
                <td>$3.5M - $3.9M</td>
                <td>Única Privada (Cerrada) con Amenidades</td>
            </tr>
            <tr>
                <td>Punta Península</td>
                <td>Condo Resort</td>
                <td>$4.1M - $5.0M</td>
                <td>Ticket alto / Cuotas altas</td>
            </tr>
            <tr>
                <td>CAAY</td>
                <td>Deptos</td>
                <td>$3.5M+</td>
                <td>Compacto / Menos amenidades</td>
            </tr>
            <tr>
                <td>Marenza</td>
                <td>Torres</td>
                <td>Medio-Alto</td>
                <td>Sin privacidad de casa sola</td>
            </tr>
            <tr>
                <td>Vistas Reserva</td>
                <td>Lotes</td>
                <td>Bajo (Lote)</td>
                <td>Sin frente de playa directo</td>
            </tr>
        </tbody>
    </table>
    """, unsafe_allow_html=True)

# --- 5. SIMULADOR DE NEGOCIO (RENTAS) ---
st.markdown("---")
st.header("📈 Negocio Patrimonial (Airbnb)")
st.caption("Proyección financiera con costos operativos reales.")

col_r1, col_r2 = st.columns([1, 2])

with col_r1:
    st.markdown("#### Configuración")
    tarifa = st.number_input("Tarifa Noche Promedio:", value=4500, step=500)
    ocupacion = st.slider("Ocupación Anual (%):", 20, 80, 45)
    
    st.markdown("#### Costos Operativos")
    comision_admin = st.slider("Comisión Administración (%):", 20, 30, 25)
    mantenimiento = st.number_input("Mantenimiento Mensual (Fijo):", value=2000, disabled=False)

with col_r2:
    # Cálculos Reales
    noches_rentadas = 365 * (ocupacion/100)
    ingreso_bruto = tarifa * noches_rentadas
    
    # Egresos
    pago_admin = ingreso_bruto * (comision_admin/100)
    pago_mto_anual = mantenimiento * 12
    total_egresos = pago_admin + pago_mto_anual
    
    utilidad_neta = ingreso_bruto - total_egresos
    roi = (utilidad_neta / precio_preventa_total) * 100
    
    # Métricas
    m1, m2, m3 = st.columns(3)
    m1.metric("Ingreso Bruto", f"${ingreso_bruto:,.0f}")
    m2.metric("Gastos Totales", f"-${total_egresos:,.0f}", delta_color="inverse")
    m3.metric("Utilidad Neta (Bolsillo)", f"${utilidad_neta:,.0f}", delta_color="normal")
    
    # Gráfica de Cascada (Waterfall) para que se vea clarito
    fig_water = go.Figure(go.Waterfall(
        name = "20", orientation = "v",
        measure = ["relative", "relative", "relative", "total"],
        x = ["Ingreso Bruto", "Comisión Admin", "Mantenimiento Anual", "NETO"],
        textposition = "outside",
        text = [f"${ingreso_bruto/1000:.0f}k", f"-${pago_admin/1000:.0f}k", f"-${pago_mto_anual/1000:.0f}k", f"${utilidad_neta/1000:.0f}k"],
        y = [ingreso_bruto, -pago_admin, -pago_mto_anual, utilidad_neta],
        connector = {"line":{"color":"rgb(63, 63, 63)"}},
        decreasing = {"marker":{"color":"#ef553b"}},
        increasing = {"marker":{"color":"#28a745"}},
        totals = {"marker":{"color":"#004e92"}}
    ))
    fig_water.update_layout(title="Flujo de Efectivo Anual", height=300)
    st.plotly_chart(fig_water, use_container_width=True)

    st.info(f"💡 **Dato Clave:** Con un ROI del **{roi:.1f}%**, la propiedad se paga sola y genera plusvalía simultánea.")

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
    pdf.cell(0, 10, f'Propiedad: Casa en Lote {lote_label}', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0)
    pdf.cell(0, 8, f'Terreno: {m2_terreno} m2 | Construcción: {m2_const_final} m2', 0, 1)
    pdf.ln(5)
    
    # Tabla Precios
    pdf.set_fill_color(240, 245, 255)
    pdf.cell(100, 10, 'Concepto', 1, 0, 'L', 1)
    pdf.cell(60, 10, 'Valor', 1, 1, 'R', 1)
    pdf.cell(100, 10, f'Terreno (Lista {lista_seleccionada})', 1, 0)
    pdf.cell(60, 10, f'${precio_terreno_actual:,.2f}', 1, 1, 'R')
    pdf.cell(100, 10, 'Construcción (Casa Terminada)', 1, 0)
    pdf.cell(60, 10, f'${valor_construccion:,.2f}', 1, 1, 'R')
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(100, 15, 'TOTAL INVERSIÓN:', 1, 0)
    pdf.cell(60, 15, f'${precio_preventa_total:,.2f}', 1, 1, 'R')
    
    # Rentas
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Simulador de Negocio (Anual)', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(100, 10, 'Ingreso Bruto Estimado:', 1, 0)
    pdf.cell(60, 10, f'${ingreso_bruto:,.2f}', 1, 1, 'R')
    
    pdf.cell(100, 10, f'Admin ({comision_admin}%) + Mto ($2000/mes):', 1, 0)
    pdf.cell(60, 10, f'-${total_egresos:,.2f}', 1, 1, 'R')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(40, 167, 69)
    pdf.cell(100, 10, 'UTILIDAD NETA (Bolsillo):', 1, 0)
    pdf.cell(60, 10, f'${utilidad_neta:,.2f}', 1, 1, 'R')

    return pdf.output(dest='S').encode('latin-1')

st.markdown("---")
c_down1, c_down2 = st.columns([3,1])
with c_down1: st.markdown("##### 📄 Descargar PDF")
with c_down2:
    try: st.download_button("DESCARGAR PDF", create_pdf(), file_name=f"Cotizacion_{lote_label}.pdf")
    except: st.error("Error PDF")