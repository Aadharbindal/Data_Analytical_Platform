def get_schema_context(db_engine, table_name="active_dataset", dataset_display_name=None, semantic_dict=None):
    """
    Returns a formatted string containing the schema, row count,
    and a few sample rows of the specified table using the DuckDB engine.
    """
    schema_str = ""
    sample_str = ""
    row_count = 0
    dataset_name_str = ""
    if dataset_display_name:
        dataset_name_str = f"The user's dataset is named '{dataset_display_name}' and its data is fully available in the table described above - treat any reference to this filename/dataset name as referring to this table.\n"
        
    try:
        desc_res = db_engine.execute(f"DESCRIBE {table_name}")
        cols = desc_res.get("rows", [])
        
        sem = semantic_dict.get("semantic_dictionary", {}) if semantic_dict else {}
        bus_term = semantic_dict.get("business_terminology", {}) if semantic_dict else {}
        
        primary_metric = bus_term.get("primary_metric")
        primary_date = bus_term.get("primary_date")
        identifiers = sem.get("entity_identifiers", [])
        
        schema_lines = []
        for c in cols:
            col_name = c['column_name']
            roles = []
            if col_name == primary_metric:
                roles.append("primary_metric")
            if col_name == primary_date:
                roles.append("primary_date")
            if col_name in identifiers:
                roles.append("identifier")
                
            role_str = f" [Role: {','.join(roles)}]" if roles else ""
            schema_lines.append(f"- {col_name} ({c['column_type']}){role_str}")
            
        schema_str = "\n".join(schema_lines)
        
        count_res = db_engine.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
        if count_res.get("rows"):
            row_count = count_res["rows"][0].get("cnt", 0)
        
        df = db_engine.con.sql(f"SELECT * FROM {table_name} LIMIT 3").df()
        df = df.astype(str)
        sample_rows = df.to_dict(orient="records")
        sample_str = "\n".join([str(r) for r in sample_rows])
    except Exception as e:
        schema_str = f"(Error loading schema: {e})"
        sample_str = "(Could not load samples)"
        
    instruction_str = ""
    if semantic_dict:
        instruction_str = "\nCRITICAL SEMANTIC RULES:\n- DO NOT perform pattern-matching (e.g. LIKE), aggregations (SUM, AVG), or arithmetic on columns marked as [Role: identifier]. They are strictly for grouping or counting unique entities.\n"
        
    return {
        "schema_str": schema_str,
        "sample_str": sample_str,
        "row_count": row_count,
        "formatted_context": f"DATABASE SCHEMA:\n{dataset_name_str}The data is in a table named '{table_name}'. Use ONLY this table name.\nRow Count: {row_count}\nColumns:\n{schema_str}\n\nSample data:\n{sample_str}{instruction_str}"
    }
