# Guía de Datos — Boston Open Data

## Resumen
El agente tiene acceso a herramientas para consultar el portal de Datos Abiertos de Boston (data.boston.gov).

## Herramientas Disponibles
1. **search_datasets(query, limit)** — Buscar conjuntos de datos por palabra clave
2. **list_all_datasets(limit)** — Navegar todos los conjuntos de datos
3. **get_dataset_info(dataset_id)** — Obtener metadatos de un conjunto de datos
4. **get_datastore_schema(resource_id)** — Obtener nombres y tipos de campos
5. **query_datastore(resource_id, ...)** — Consultar registros con filtros, ordenamiento y búsqueda

## Conjuntos de Datos Clave
- Solicitudes de servicio 311 (sistema nuevo y legado)
- Horarios de basura por dirección
- Permisos de construcción aprobados
- Violaciones de propiedad y edificios
- Licencias de establecimientos de comida activos
- Ubicaciones de alumbrado público
- Árboles de la ciudad
- Datos de crimen
