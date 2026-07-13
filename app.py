import streamlit as st
import pandas as pd
import io

# Configuración de la página web
st.set_page_config(page_title="Conciliación Bancaria con KPIs", page_icon="📊", layout="wide")

# ESTILOS CSS PERSONALIZADOS
custom_css = """
    <style>
    .stApp { background-color: #0d1b2a; color: #e0e1dd; }
    h1, h2, h3 { color: #ffffff !important; font-family: 'Helvetica Neue', sans-serif; }
    div[data-testid="stMetricValue"] { color: #00b4d8 !important; font-size: 28px !important; font-weight: bold !important; }
    div[data-testid="stMetricLabel"] { color: #ffffff !important; }
    .stDownloadButton button { background-color: #0077b6 !important; color: white !important; border-radius: 8px !important; font-weight: bold !important; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: #0b132b; color: #bcbed8; text-align: center; padding: 10px; font-size: 14px; border-top: 2px solid #0077b6; z-index: 100; }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

st.markdown('<div class="footer"><p>© 2026 | Sistema Automatizado de Conciliación Bancaria — Creado por Olgleidys Hernández 👩‍💻✨</p></div>', unsafe_allow_html=True)

st.title("📊 Sistema Automatizado de Conciliación Bancaria")

# Configuración inicial
c1, c2 = st.columns(2)
with c1: empresa_seleccionada = st.selectbox("🏢 Seleccione la empresa:", ["Thermo Group", "Mystic", "Keravital"])
bancos_por_empresa = {"Thermo Group": ["Banesco", "Venezuela", "Banplus", "Mercantil", "Banco Fondo Común"], "Mystic": ["Banesco", "Venezuela", "Banplus", "Banplus Mazal"], "Keravital": ["Banesco", "Venezuela"]}
with c2: banco_seleccionado = st.selectbox("🏦 Seleccione el banco:", bancos_por_empresa[empresa_seleccionada])

p1, p2, p3 = st.columns(3)
with p1: frecuencia = st.selectbox("⏱️ Frecuencia:", ["Semanal", "Quincenal", "Mensual"])
with p2: mes = st.selectbox("📆 Mes:", ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"])
with p3: ano = st.selectbox("📅 Año:", ["2026", "2027", "2025"])

col1, col2 = st.columns(2)
with col1: banco_file = st.file_uploader(f"📥 Estado de Cuenta {banco_seleccionado} (.csv)", type=["csv"])
with col2: profit_file = st.file_uploader(f"📥 Reporte Profit Plus (.csv)", type=["csv"])

def procesar_csv(file):
    try: return pd.read_csv(file, sep=None, encoding="latin-1", engine="python", on_bad_lines="skip")
    except: return None

def limpiar_monto(serie):
    return pd.to_numeric(serie.astype(str).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)

if banco_file and profit_file:
    df_banco = procesar_csv(banco_file)
    df_profit = procesar_csv(profit_file)
    
    if df_banco is not None and df_profit is not None:
        try:
            df_banco.columns = [str(c).strip() for c in df_banco.columns]
            df_profit.columns = [str(c).strip() for c in df_profit.columns]
            
            # Ajuste de columnas
            cols_banco = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
            cols_profit = ['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']
            df_banco = df_banco.iloc[:, :5]; df_banco.columns = cols_banco
            df_profit = df_profit.iloc[:, :5]; df_profit.columns = cols_profit
            
            # Limpieza básica
            df_banco['Ref'] = df_banco['Ref'].fillna('').astype(str).str.strip().str.lstrip('0')
            df_profit['Ref'] = df_profit['Ref'].fillna('').astype(str).str.strip().str.lstrip('0')
            df_banco['Monto_Num'] = limpiar_monto(df_banco['Cred'])
            df_profit['Monto_Num'] = limpiar_monto(df_profit['Haber'])

            # LÓGICA DE CONCILIACIÓN
            # 1. Cruce Exacto
            df_banco['Key_Exacta'] = df_banco['Ref'] + "_" + df_banco['Monto_Num'].astype(str)
            df_profit['Key_Exacta'] = df_profit['Ref'] + "_" + df_profit['Monto_Num'].astype(str)
            
            cruces_exactos = df_banco[df_banco['Key_Exacta'].isin(df_profit['Key_Exacta'])]
            pendientes_banco = df_banco[~df_banco['Key_Exacta'].isin(df_profit['Key_Exacta'])]
            pendientes_profit = df_profit[~df_profit['Key_Exacta'].isin(df_banco['Key_Exacta'])]
            
            # 2. Cruce Secundario (Ref >= 3 dígitos + Monto exacto)
            pendientes_banco_valido = pendientes_banco[pendientes_banco['Ref'].str.len() >= 3].copy()
            pendientes_profit_valido = pendientes_profit[pendientes_profit['Ref'].str.len() >= 3].copy()
            
            pendientes_banco_valido['Key_Sec'] = pendientes_banco_valido['Ref'].str[-3:] + "_" + pendientes_banco_valido['Monto_Num'].astype(str)
            pendientes_profit_valido['Key_Sec'] = pendientes_profit_valido['Ref'].str[-3:] + "_" + pendientes_profit_valido['Monto_Num'].astype(str)
            
            cruces_secundarios = pendientes_banco_valido[pendientes_banco_valido['Key_Sec'].isin(pendientes_profit_valido['Key_Sec'])]
            
            # Resultados finales consolidados
            cruces_finales = pd.concat([cruces_exactos, cruces_secundarios])
            solo_banco_final = pendientes_banco[~pendientes_banco.index.isin(cruces_secundarios.index)]
            solo_profit_final = pendientes_profit[~pendientes_profit.index.isin(cruces_secundarios.index)]

            # Definición de columnas para visualización y exportación (sin las columnas técnicas)
            cols_banco_export = ['Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
            cols_profit_export = ['Fecha', 'Ref', 'Desc', 'Debe', 'Haber']

            # UI de Resultados (limpios)
            tab1, tab2, tab3, tab4 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo Banco", "💻 Solo Profit", "📈 KPIs"])
            with tab1: st.dataframe(cruces_finales[cols_banco_export], use_container_width=True)
            with tab2: st.dataframe(solo_banco_final[cols_banco_export], use_container_width=True)
            with tab3: st.dataframe(solo_profit_final[cols_profit_export], use_container_width=True)
            
            with tab4:
                monto_b_pend = solo_banco_final['Monto_Num'].sum()
                monto_p_pend = solo_profit_final['Monto_Num'].sum()
                kpi1, kpi2, kpi3 = st.columns(3)
                kpi1.metric("Tasa de Conciliación", f"{(len(cruces_finales)/(len(df_banco))*100):.1f}%")
                kpi2.metric("Pendiente Banco", f"{monto_b_pend:,.2f}")
                kpi3.metric("Tránsito Profit", f"{monto_p_pend:,.2f}")

            # Exportación LIMPIA (sin columnas auxiliares)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                cruces_finales[cols_banco_export].to_excel(writer, sheet_name='Cruces_Exitosos', index=False)
                solo_banco_final[cols_banco_export].to_excel(writer, sheet_name='Solo_Banco', index=False)
                solo_profit_final[cols_profit_export].to_excel(writer, sheet_name='Solo_Profit', index=False)
            
            st.download_button("📥 Descargar Conciliación Completa", output.getvalue(), f"Conciliacion_{mes}_{ano}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        except Exception as e: st.error(f"Error procesando datos: {e}")
