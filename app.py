import streamlit as st
import pandas as pd
import io

# Configuración de la página web corporativa
st.set_page_config(page_title="Sistema de Auditoría y Conciliación Avanzada", page_icon="📊", layout="wide")

# ESTILOS CSS PERSONALIZADOS: Look Premium de Alto Contraste y Visibilidad
custom_css = """
    <style>
    /* Fondo principal de la app */
    .stApp {
        background-color: #0d1b2a;
        color: #e0e1dd;
    }
    
    /* Títulos principales */
    h1, h2, h3, h4 {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Etiquetas de los selectores y cajas de carga */
    .stSelectbox label, .stFileUploader label, .stTextInput label, .stNumberInput label {
        color: #e0e1dd !important;
        font-weight: bold !important;
    }
    
    /* 🛠️ CORRECCIÓN DE COLORES EN LAS PESTAÑAS (TABS) 🛠️ */
    button[data-baseweb="tab"] p {
        color: #ffffff !important;  /* Blanco puro para que no se pierda en el fondo */
        font-size: 16px !important;
        font-weight: bold !important;
    }
    
    /* Pestaña seleccionada (Azul Cian Brillante) */
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #00b4d8 !important;
    }
    
    /* Línea indicadora inferior de la pestaña activa */
    div[data-baseweb="tab-highlight-line"] {
        background-color: #00b4d8 !important;
    }
    
    /* Tarjetas de Métricas Fijas Arriba */
    div[data-testid="stMetricValue"] {
        color: #00b4d8 !important;
        font-size: 28px !important;
        font-weight: bold !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #ffffff !important;
        font-size: 15px !important;
    }
    
    /* Botón de descarga de Excel */
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
    
    /* Pie de página elegante fijo abajo */
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

# Render de derechos de autor fijo abajo
st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p></div>', unsafe_allow_html=True)

st.title("📊 Sistema Avanzado de Conciliación Bancaria y Control de Gestión")

# PASO 1: Ingreso de Información Base
st.markdown("### 🏢 Paso 1: Configuración de Empresa y Período")
c1, c2 = st.columns(2)
with c1:
    empresa_seleccionada = st.selectbox("Seleccione la empresa a conciliar:", ["Thermo Group", "Mystic", "Keravital"])

bancos_por_empresa = {
    "Thermo Group": ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"],
    "Mystic": ["Banesco", "Venezuela", "Banplus", "Banplus Mazal"],
    "Keravital": ["Banesco", "Venezuela"]
}

with c2:
    banco_seleccionado = st.selectbox("Seleccione el banco a conciliar:", bancos_por_empresa[empresa_seleccionada])

p1, p2, p3 = st.columns(3)
with p1: frecuencia = st.selectbox("⏱️ Frecuencia del control:", ["Semanal", "Quincenal", "Mensual"])
with p2: mes = st.selectbox("📆 Mes correspondiente:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
with p3: ano = st.selectbox("📅 Año:", ["2026", "2027", "2025"])

st.markdown("---")
st.markdown("### 📥 Carga de Archivos")
col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader(f"Estado de Cuenta de {banco_seleccionado} (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader(f"Reporte de Profit Plus para {empresa_seleccionada} (.csv)", type=["csv"])

def procesar_csv(file):
    try:
        df = pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
        return df
    except:
        return None

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
            
            # PESTAÑA APARTE PARA REVISIÓN MANUAL (Definida de manera persistente en la sesión)
            st.markdown("---")
            tab_datos, tab_ajustes, tab_kpis, tab_cierre = st.tabs([
                "📋 PASO 1: Resultados y Cruces", 
                "🛠️ PASO 2: Registro de Diferencias Aclaradas", 
                "📈 PASO 3: Indicadores de Gestión (KPIs)", 
                "🔒 PASO 4: Amarre de Saldos Iniciales/Finales"
            ])
            
            with tab_ajustes:
                st.subheader("🛠️ Módulo de Ajustes de Auditoría")
                st.markdown("Una vez realizada tu revisión manual, escribe aquí abajo las referencias que detectaste para forzar su conciliación en el sistema.")
                ajustes_input = st.text_input("Ingrese las referencias separadas por coma (Ej: 14520, 998231):", key="ajustes_manuales")
                referencias_ajustadas = [ref.strip().lstrip('0').replace('.0', '') for ref in ajustes_input.split(',') if ref.strip()]
            
            # Base de referencias cruzadas aplicando los ajustes ingresados en el paso 2
            refs_profit = set(df_profit['Ref'].unique())
            if referencias_ajustadas:
                refs_profit.update(referencias_ajustadas)
            
            refs_banco = set(df_banco['Ref'].unique())
            if referencias_ajustadas:
                refs_banco.update(referencias_ajustadas)

            # Clasificación final de los conjuntos
            cruces_df = df_banco[df_banco['Ref'].isin(refs_profit)]
            solo_banco_df = df_banco[~df_banco['Ref'].isin(refs_profit)]
            solo_profit_df = df_profit[~df_profit['Ref'].isin(refs_banco)]
            
            # METRICAS FIJAS EN LA PARTE SUPERIOR DE LOS DETALLES
            m1, m2, m3 = st.columns(3)
            m1.metric("Cruces Exitosos", f"{len(cruces_df)} movimientos")
            m2.metric(f"Pendientes en {banco_seleccionado}", f"{len(solo_banco_df)} movimientos")
            m3.metric("Pendientes en Profit", f"{len(solo_profit_df)} movimientos")
            st.markdown("<br>", unsafe_allow_html=True)
            
            with tab_datos:
                # Sub-pestañas internas para limpiar la navegación de las tablas
                sub_tab1, sub_tab2, sub_tab3 = st.tabs(["✅ Cruces Exitosos", f"🏦 Solo en {banco_seleccionado}", "💻 Solo en Profit"])
                
                with sub_tab1:
                    st.dataframe(cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                with sub_tab2:
                    st.dataframe(solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']], use_container_width=True)
                with sub_tab3:
                    st.dataframe(solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']], use_container_width=True)
                
            with tab_kpis:
                st.subheader("📊 Línea de Flujo Estratégico")
                
                total_banco_ops = len(df_banco)
                ops_conciliadas = len(cruces_df)
                tasa_eficiencia = (ops_conciliadas / total_banco_ops * 100) if total_banco_ops > 0 else 0
                
                # Clasificador de gastos específicos (Artículos de Oficina)
                df_banco['Desc_Lower'] = df_banco['Desc'].astype(str).str.lower()
                oficina_df = df_banco[df_banco['Desc_Lower'].str.contains('oficina|papeleria|articulos|compra|libreria', na=False)]
                monto_oficina = limpiar_monto(oficina_df['Deb']).sum() + limpiar_monto(oficina_df['Cred']).sum()
                
                k1, k2 = st.columns(2)
                k1.metric("🎯 Eficiencia General del Registro", f"{tasa_eficiencia:.1f}%")
                k2.metric("📎 Inversión en Artículos de Oficina", f"{monto_oficina:,.2f} Bs")
                
                # Gráfico de barras compacto y más pequeño para entenderse rápido
                st.markdown("#### Proporciones del Universo de Datos Procesado")
                chart_data = pd.DataFrame({
                    'Estado': ['Conciliados', 'Falta en Banco', 'Falta en Profit'],
                    'Movimientos': [len(cruces_df), len(solo_banco_df), len(solo_profit_df)]
                })
                # Estructura compacta usando columnas para reducir el ancho del gráfico
                g_col1, g_col2 = st.columns([1, 1])
                with g_col1:
                    st.bar_chart(data=chart_data, x='Estado', y='Movimientos', color='#00b4d8', use_container_width=True)
                
            with tab_cierre:
                st.subheader("🔒 Cierre de Mes Contable y Punto de Partida")
                st.markdown("Introduce los saldos de tus libros para calcular el cuadre exacto.")
                
                s_c1, s_c2 = st.columns(2)
                with s_c1: saldo_inicial_banco = st.number_input(f"Saldo Inicial Estado de Cuenta ({banco_seleccionado}):", value=0.0)
                with s_c2: saldo_inicial_profit = st.number_input(f"Saldo Inicial Sistema Profit ({empresa_seleccionada}):", value=0.0)
                
                # Operaciones matemáticas de saldos
                saldo_final_banco_calculado = saldo_inicial_banco + limpiar_monto(cruces_df['Cred']).sum() - limpiar_monto(cruces_df['Deb']).sum()
                saldo_final_profit_calculado = saldo_inicial_profit + limpiar_monto(cruces_df['Haber']).sum() - limpiar_monto(cruces_df['Debe']).sum()
                
                st.markdown("---")
                r_c1, r_c2 = st.columns(2)
                r_c1.metric("📋 Saldo Final Conciliado en Banco", f"{saldo_final_banco_calculado:,.2f} Bs")
                r_c2.metric("💻 Saldo Final Conciliado en Profit", f"{saldo_final_profit_calculado:,.2f} Bs")
                
                diferencia_saldos = abs(saldo_final_banco_calculado - saldo_final_profit_calculado)
                if diferencia_saldos < 0.05:
                    st.success("🎉 ¡CONCILIACIÓN CUADRADA CON ÉXITO! Ambos saldos son idénticos. Estos montos son tus Puntos de Partida oficiales para el siguiente período.")
                else:
                    st.warning(f"⚠️ Alerta de Discrepancia: Hay una diferencia de {diferencia_saldos:,.2f} Bs. Revisa si falta registrar alguna referencia en el Paso 2.")

            # Descarga unificada de reportes en Excel
            st.markdown("---")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Cruces_Exitosos', index=False)
                solo_banco_df[['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']].to_excel(writer, sheet_name='Solo_en_Banco', index=False)
                solo_profit_df[['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']].to_excel(writer, sheet_name='Solo_en_Profit', index=False)
            
            emp_nom = empresa_seleccionada.replace(" ", "_")
            bnc_nom = banco_seleccionado.replace(" ", "_")
            nombre_archivo_excel = f"Conciliacion_{emp_nom}_{bnc_nom}_{frecuencia}_{mes}_{ano}.xlsx"
            
            st.download_button(label="📥 Descargar Reporte Completo en Excel", data=output.getvalue(), file_name=nombre_archivo_excel, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
        except Exception as e:
            st.error(f"Error técnico en el procesamiento: {e}")

st.markdown("<br><br><br>", unsafe_allow_html=True)
