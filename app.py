import streamlit as st
import pandas as pd
import io

# Configuración de la página web corporativa
st.set_page_config(page_title="Conciliación Bancaria con KPIs", page_icon="📊", layout="wide")

# ESTILOS CSS PERSONALIZADOS: Look Premium de Alta Visibilidad
custom_css = """
    <style>
    .stApp {
        background-color: #0d1b2a;
        color: #e0e1dd;
    }
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .stSelectbox label, .stFileUploader label {
        color: #e0e1dd !important;
        font-weight: bold !important;
    }
    /* Pestañas de alto contraste corregidas */
    button[data-baseweb="tab"] p {
        color: #e0e1dd !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #00b4d8 !important;
        font-weight: bold !important;
    }
    div[data-baseweb="tab-highlight-line"] {
        background-color: #00b4d8 !important;
    }
    /* Métricas */
    div[data-testid="stMetricValue"] {
        color: #00b4d8 !important;
        font-size: 28px !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #ffffff !important;
    }
    .stDownloadButton button {
        background-color: #0077b6 !important;
        color: white !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    .stDownloadButton button:hover {
        background-color: #00b4d8 !important;
        color: #0d1b2a !important;
    }
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0b132b;
        color: #bcbed8;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        font-weight: 500;
        border-top: 2px solid #0077b6;
        z-index: 100;
    }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Footer
st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p></div>', unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# Configuración básica
c1, c2 = st.columns(2)
with c1:
    empresa_seleccionada = st.selectbox("🏢 Seleccione la empresa a conciliar:", ["Thermo Group", "Mystic", "Keravital"])

bancos_por_empresa = {
    "Thermo Group": ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"],
    "Mystic": ["Banesco", "Venezuela", "Banplus", "Banplus Mazal"],
    "Keravital": ["Banesco", "Venezuela"]
}

with c2:
    banco_seleccionado = st.selectbox("🏦 Seleccione el banco a conciliar:", bancos_por_empresa[empresa_seleccionada])

st.markdown("### 📅 Configuración del Período")
p1, p2, p3 = st.columns(3)
with p1: frecuencia = st.selectbox("⏱️ Frecuencia del control:", ["Semanal", "Quincenal", "Mensual"])
with p2: mes = st.selectbox("📆 Mes correspondiente:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
with p3: ano = st.selectbox("📅 Año:", ["2026", "2027", "2025"])

st.markdown("---")
st.info(f"⚙️ **Configuración activa:** {empresa_seleccionada} | {banco_seleccionado} | {frecuencia} de {mes} {ano}")

col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader(f"📥 Cargar Estado de Cuenta de {banco_seleccionado} (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader(f"📥 Cargar Reporte de Profit Plus (.csv)", type=["csv"])

def procesar_csv(file):
    try:
        df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
        return df
    except:
        return None

# Función auxiliar para convertir columnas monetarias a números limpios
def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    df_banco = procesar_csv(banco_file)
    df_profit = procesar_csv(profit_file)
    
    if df_banco is not None and df_profit is not None:
        try:
            df_banco.columns = [str(c).strip() for c in df_banco.columns]
            df_profit.columns = [str(c).strip() for c in df_profit.columns]

            while len(df_banco.columns) < 5: df_banco[f'Comodin_B_{len(df_banco.columns)}'] = ""
            while len(df_profit.columns) < 5: df_profit[f'Comodin_P_{len(df_profit.columns)}'] = 0

            cols_banco = list(df_banco.columns)
            cols_banco[0], cols_banco[1], cols_banco[2], cols_banco[3], cols_banco[4] = 'Fecha', 'Ref', 'Desc', 'Deb', 'Cred'
            df_banco.columns = cols_banco

            cols_profit = list(df_profit.columns)
            cols_profit[0], cols_profit[1], cols_profit[2], cols_profit[3], cols_profit[4] = 'Fecha', 'Ref', 'Desc', 'Debe', 'Haber'
            df_profit.columns = cols_profit
            
            df_banco['Ref'] = df_banco['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            df_profit['Ref'] = df_profit['Ref'].fillna('').astype(str).str.strip().str.lstrip('0').str.replace('.0', '', regex=False)
            
            df_banco = df_banco[df_banco['Ref'] != '']
            df_profit = df_profit[df_profit['Ref'] != '']
            
            refs_profit = set(df_profit['Ref'].unique())
            refs_banco = set(df_banco['Ref'].unique())
            
            cruces_df = df_banco[df_banco['Ref'].isin(refs_profit)]
            solo_banco_df = df_banco[~df_banco['Ref'].isin(refs_profit)]
            solo_profit_df = df_profit[~df_profit['Ref'].isin(refs_banco)]
            
            # PESTAÑAS AMPLIADAS CON INDICADORES DE GESTIÓN
            tab1, tab2, tab3, tab4 = st.tabs(["✅ Cruces Exitosos", f"🏦 Solo en {banco_seleccionado}", f"💻 Solo en Profit", "📈 Indicadores de Gestión (KPIs)"])
            
            with tab1:
                st.subheader("Transacciones Conciliadas Correctamente")
                st.dataframe(cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab2:
                st.subheader("Movimientos en Banco pendientes por registrar")
                st.dataframe(solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                
            with tab3:
                st.subheader("Movimientos en Profit pendientes por pasar por el Banco")
                st.dataframe(solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']], use_container_width=True)
                
            with tab4:
                st.subheader("📊 Cuadro de Mando Estratégico e Indicadores")
                
                # Cálculos rápidos de volúmenes
                total_banco_ops = len(df_banco)
                ops_conciliadas = len(cruces_df)
                tasa_eficiencia = (ops_conciliadas / total_banco_ops * 100) if total_banco_ops > 0 else 0
                
                # Cálculos financieros limpios
                monto_banco_pendiente = limpiar_monto(solo_banco_df['Deb']).sum() + limpiar_monto(solo_banco_df['Cred']).sum()
                monto_profit_pendiente = limpiar_monto(solo_profit_df['Debe']).sum() + limpiar_monto(solo_profit_df['Haber']).sum()
                
                # Render de Tarjetas KPI
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("🎯 Tasa de Conciliación", f"{tasa_eficiencia:.1f}%", help="Porcentaje de transacciones bancarias mapeadas con éxito en Profit Plus.")
                kpi2.metric("⚠️ Pendiente Neto Banco", f"{monto_banco_pendiente:,.2f}", help="Monto total monetario acumulado que falta registrar en Profit.")
                kpi3.metric("💻 Tránsito Neto Profit", f"{monto_profit_pendiente:,.2f}", help="Monto total registrado en Profit pendiente por efectividad bancaria.")
                
                # Gráfico Visual de Distribución de los Datos
                st.markdown("#### Distribución del Volumen de Operaciones Auditadas")
                chart_data = pd.DataFrame({
                    'Categoría': ['Conciliados', 'Pendiente Banco', 'Pendiente Profit'],
                    'Movimientos': [len(cruces_df), len(solo_banco_df), len(solo_profit_df)]
                })
                st.bar_chart(data=chart_data, x='Categoría', y='Movimientos', color='#00b4d8')
            
            # Exportación Excel
            st.markdown("---")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Cruces_Exitosos', index=False)
                solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Solo_en_Banco', index=False)
                solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']].to_excel(writer, sheet_name='Solo_en_Profit', index=False)
            
            emp_nom = empresa_seleccionada.replace(" ", "_")
            bnc_nom = banco_seleccionado.replace(" ", "_")
            nombre_archivo_excel = f"Conciliacion_{emp_nom}_{bnc_nom}_{frecuencia}_{mes}_{ano}.xlsx"
            
            st.download_button(label="📥 Descargar Conciliación Completa (Excel)", data=output.getvalue(), file_name=nombre_archivo_excel, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            st.success("¡Conciliación y KPIs procesados con éxito!")
            
        except Exception as e:
            st.error(f"Ocurrió un error al procesar los datos: {e}")

st.markdown("<br><br><br>", unsafe_allow_html=True)
