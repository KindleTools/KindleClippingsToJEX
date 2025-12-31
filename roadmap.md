# Roadmap de Modernización y Arquitectura

Este documento detalla el plan de evolución técnica de `KindleClippingsToJEX`, basado en el análisis profundo del prototipo legacy ("old project"). El objetivo es migrar hacia una arquitectura de nivel "Enterprise" que garantice robustez, integridad de datos y escalabilidad.

## 🏁 Fase 1: Capa de Persistencia (El "UnifiedDatabase")

Actualmente, la aplicación funciona "en memoria" (Pass-through). Esto impide funcionalidades críticas como actualizaciones incrementales reales o historial de ediciones.

### 1.1. Implementación de SQLite
Diseñar una base de datos local `kindle_data.db` gestionada por una clase Singleton `UnifiedDatabase`. Esto reemplazará el almacenamiento volátil actual.

**Esquema Propuesto:**
*   **`persistent_highlights`**: Tabla maestra.
    *   `id` (PK): Hash único del contenido (MD5/SHA256).
    *   `original_content`: Texto tal cual viene del Kindle (inmutable).
    *   `current_content`: Texto editable por el usuario.
    *   `is_modified` (BOOL): Flag para saber si se editó manualmente.
    *   `is_exported` (BOOL): Flag para exportación incremental "New Only".
    *   `source_file`: Rastreo de origen.
*   **`import_batches`**: Historial de importaciones (cuándo y qué archivo se procesó).
*   **`modification_history`**: (Opcional) Tabla de auditoría para deshacer cambios manuales.

### 1.2. Lógica de Negocio Asociada
*   **Deduplicación Real**: Al importar, verificar contra la DB. Si el hash existe, se omite o se actualiza si hay nuevos metadatos.
*   **Edición Segura**: Permitir editar notas en la GUI y guardar en `current_content` sin perder el original.

---

## 🚀 Fase 2: Motor de Parsing Robusto

El parser actual es funcional pero monolítico. Se debe refactorizar para separar responsabilidades y manejar grandes volúmenes de datos.

### 2.1. Arquitectura de "Streaming"
Implementar un mecanismo híbrido de lectura de archivos en `KindleClippingsParser`.
*   **Archivos Pequeños (<5MB)**: Lectura en memoria (como ahora).
*   **Archivos Grandes (>5MB)**: Lectura por bloques (`chunk_size = 16KB` aprox) y procesamiento de buffer. Esto evita bloqueos de memoria con archivos "My Clippings.txt" de usuarios con años de lectura.

### 2.2. Gestión de "Sanieamiento" (Sanitization)
*   **BOM Handling**: Detectar y eliminar explícitamente `\ufeff` al inicio de los streams para evitar corrupción en Windows.
*   **Normalización**: Unificar finales de línea (`\r\n` -> `\n`) antes de cualquier regex.

### 2.3. Desacople de Patrones
Extraer los patrones Regex hardcodeados a un sistema de configuración extensible.
*   Crear `parsers/kindle/patterns.py`.
*   Soporte dinámico de idiomas cargando diccionarios de patrones.

---

## 📦 Fase 3: Entidades de Dominio y Exportación Estricta

Moverse de diccionarios planos (`dict`) a Objetos de Dominio (DTOs) para garantizar la integridad de la estructura JEX/Joplin.

### 3.1. Clases de Entidad (Joplin Entities)
Implementar clases estrictas en `domain/entities/` que representen los bloques de construcción de Joplin.
*   **`JoplinNote`**: Valida que existan `id`, `parent_id`, `title`, `body`.
*   **`JoplinTag`**: Gestiona la creación de IDs únicos para etiquetas.
*   **`JoplinNotebook`**: Estructura de carpetas.

### 3.2. Refactorización del Exporter
El `JoplinExporter` no debe construir strings manualmente. Debe:
1.  Recibir objetos de dominio.
2.  Orquestar la creación de entidades (`JoplinNote`).
3.  Delegar en la entidad su propia serialización a Markdown/JEX.

**Beneficio**: Si cambia la especificación de Joplin o agregamos otro formato, la lógica de validación está centralizada en la Entidad, no dispersa en el servicio de exportación.

---

## 🏗️ Fase 4: Arquitectura DDD (Domain-Driven Design)

Reoganizar el proyecto para separar claramente "Qué es un dato" de "Cómo se guarda" y "Cómo se procesa".

### 4.1. Repositorios vs Servicios
*   **Services (`HighlightService`)**: Coordinan acciones ("Importar archivo", "Limpiar texto").
*   **Repositories (`HighlightRepository`)**: Abstraen el acceso a datos. Hoy leen de archivo, mañana de la DB SQLite. El servicio no debe saber de dónde vienen los datos.

### 4.2. Inyección de Dependencias
Asegurar que los parsers y exporters reciban sus configuraciones y dependencias (logger, config manager) en el constructor, facilitando los tests unitarios (mocking).

---

## 📝 Pasos Inmediatos Sugeridos

1.  **Refactor Parser**: Comenzar extrayendo los Regex a `patterns.py`.
2.  **DTOs**: Crear la clase `JoplinNote` y usarla en el exporter actual.
3.  **DB Prototipo**: Crear el script de inicialización de SQLite (`sqlite3`) en `storage/`.
