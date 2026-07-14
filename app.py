# Definir qué columnas quieres conservar de los originales
    # Asumiendo que quieres mantener las columnas originales de tus archivos
    # Ejemplo: si tus columnas originales son ['Fecha', 'Ref', 'Desc', 'M1', 'M2', 'Estado']
    cols_a_mantener = ['Fecha', 'Ref', 'Desc', 'M1', 'M2', 'Estado'] 
    
    # Preparamos los DataFrames filtrados
    df_b_final = df_b.reindex(columns=cols_a_mantener)
    df_p_final = df_p.reindex(columns=cols_a_mantener)
    
    # Si necesitas la columna Origen, agrégala después del filtro
    df_full = pd.concat([df_b_final.assign(Origen='Banco'), df_p_final.assign(Origen='Profit')])

    # --- AJUSTAR LA VISUALIZACIÓN ---
    with tab1: st.dataframe(df_full, use_container_width=True)
    with tab2: st.dataframe(df_b_final[df_b['Estado'] == 'Pendiente'], use_container_width=True)
    with tab3: st.dataframe(df_p_final[df_p['Estado'] == 'Pendiente'], use_container_width=True)

    # --- AJUSTAR LA DESCARGA ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_full.to_excel(writer, sheet_name='Todos_Movimientos', index=False)
