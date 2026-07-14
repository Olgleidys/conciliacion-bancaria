# ... (código anterior igual)

    # --- RESULTADOS FINALES ---
    # Añadimos una etiqueta para identificar el tipo de cruce
    cruces_1['Metodo_Cruce'] = '100% Exacto'
    cruces_2['Metodo_Cruce'] = '3 Últimos Dígitos'
    
    final_cruces = pd.concat([cruces_1, cruces_2])
    
    # Aseguramos que la columna Metodo_Cruce sea la primera
    cols_a_mostrar = ['Metodo_Cruce', 'Fecha', 'Ref', 'Desc', 'Deb', 'Cred']
    
    # Mostrar tablas
    t1, t2, t3 = st.tabs(["✅ Cruces Exitosos", "🏦 Solo Banco", "💻 Solo Profit"])
    t1.dataframe(final_cruces[cols_a_mostrar], use_container_width=True)
    # ... (resto del código igual)
