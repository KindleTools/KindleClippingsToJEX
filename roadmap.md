# Roadmap de Desarrollo: Evolución a Arquitectura "Enterprise"

Tras el análisis de la arquitectura encontrada en el antiguo proyecto (`.idea`), se ha definido un nuevo camino ambicioso para llevar `KindleClippingsToJEX` al siguiente nivel. El objetivo es transicionar de un "script de conversión" a una **Plataforma de Gestión de Conocimiento Personal**.

## ✅ Logros Consolidados (v1.0 - Core)
El núcleo funcional de la herramienta está completo, robusto y probado:
- ✅ **Parsing A prueba de balas**: Soporte multi-idioma (ES, EN, FR, DE, IT, PT) con detección automática.
- ✅ **Sanitización UX**: Limpieza automática de títulos sucios, BOM, y caracteres corruptos.
- ✅ **Exportación Fiable**: Generación de JEX/JSON/CSV/MD con integridad referencial.
- ✅ **UX Zen**: Interfaz moderna (Qt), rápida y con feedback visual de errores.

---

## Fase 1: Identidad y Limpieza (Completado)
*Objetivo: Asegurar que los datos sean consistentes y únicos antes de persistirlos.*

- [x] **IdentityService Determinista**: Implementar el generador de IDs basado en hash SHA-256 (`content | author | book | page`), excluyendo deliberadamente la fecha.
    - *Beneficio*: Deduplicación real incluso si se importa el mismo libro años después.
- [x] **Limpieza de Títulos Avanzada**: Integrar y refinar el `TitleCleaner` (ya iniciado) para normalizar nombres de libros (eliminar "(Spanish Edition)", extensiones .mobi, etc.).
- [x] **Deduplicación Difusa**: Implementar algoritmo de Jaccard (threshold 0.9) para detectar "casi duplicados" (ej. corrección de typos).

## Fase 2: El Nuevo Corazón (Unified Database)
*Objetivo: Cambiar el paradigma de "procesar archivo" a "base de datos persistente".*

- [ ] **MySQLite Backend (`unified_database.py`)**: Migrar el almacenamiento a SQLite.
    - Tabla `persistent_highlights`: Separación estricta entre datos originales (inmutables) y datos actuales (editables).
    - Tabla `modification_history`: Auditoría completa de cambios (Undo/Redo).
    - Tabla `import_batches`: Rastreo de qué highlights vinieron en qué importación.
- [ ] **Configuración Persistente (`configuration_service.py`)**: Mover la configuración de archivos JSON planos a la base de datos con tipado fuerte y validación.

## Fase 3: Rendimiento y Parsing "Turbo"
*Objetivo: Manejar librerías masivas sin bloquear la UI.*

- [ ] **Streaming Parser**: Implementar el parser por chunks (16KB) para archivos >5MB.
    - Evitar cargar todo el archivo en RAM.
- [ ] **Feedback Granular**: Integrar los callbacks de progreso detallados (`reading`, `linking`, `finalizing`) en la GUI actual para una barra de carga real.

## Fase 4: Experiencia de Edición (GUI v2.0)
*Objetivo: Convertir la herramienta en un editor, no solo un exportador.*

- [ ] **Editor de Notas**: Permitir editar el texto/tags de una nota en la GUI y guardar los cambios en `persistent_highlights` (manteniendo el original intacto).
- [ ] **Historial de Cambios**: Visualizar en la UI quién modificó qué y cuándo.
- [ ] **Persistencia de Estado de Ventana**: Recordar tamaño/posición al cerrar (recuperado del backlog antiguo).
- [ ] **Importación Inteligente**: Al importar un `My Clippings.txt`, mostrar un dashboard: "X Nuevas, Y Actualizadas, Z Duplicados exactos".

## Fase 5: Integraciones y Exportación
- [ ] **Joplin Exporter v2**:
    - Jerarquía de Notebooks independiente (IDs virtuales para carpetas).
    - Gestión correcta de vínculos Tag-Nota (relación N:M).
- [ ] **Direct Joplin Sync (API)**: Sincronización HTTP directa sin archivos intermedios (recuperado del backlog antiguo).
- [ ] **Filtros Avanzados**: "Ver solo nuevos" o "Ver modificados hoy" (recuperado del backlog antiguo).
- [ ] **Smart Links**: Generación automática de enlaces a Goodreads/Amazon basados en título/autor.
- [ ] **Templating Simple**: Permitir definir el formato de salida (ej. Markdown) mediante plantillas configurables en `config.json`.
- [ ] **Safe Tag Mining**: Restringir la detección automática de tags (desde notas) para evitar "tags basura" (ej. requerir prefijo '#' o '.').

---
*Estado actual: Fase 1 completada. Listo para iniciar Fase 2 (Unified Database).*

## Fase 6: Diferenciación y Enriquecimiento (Inspirado en Análisis de Mercado)
*Objetivo: Superar a la competencia (Kindle Mate, Readwise) con características premium.*

- [ ] **Enrichment Service (Metadatos Visuales)**:
    - Uso de la **Open Library Covers API** (`covers.openlibrary.org`) para obtener portadas legalmente y sin keys.
    - Adjuntar portadas como recursos de imagen en las notas de Joplin para una vista de "estantería" visualmente impactante.
- [ ] **Soporte `vocab.db` (Flashcards)**:
    - Parsear el archivo SQLite interno del Kindle (`system/vocabulary/vocab.db`) para extraer palabras buscadas y contexto.
    - Generar notas tipo "Flashcard" para Joplin o exportación directa a **Anki** (.apkg).
- [ ] **Zero-Touch Sync**:
    - Detección automática de conexión USB del Kindle.
    - Popup proactivo: "Kindle detectado. ¿Importar 5 nuevos highlights?".
- [ ] **Quote Card Generator**:
    - Generador de imágenes (PNG) para compartir citas en redes sociales (fondo estético + tipografía).

## Fase 7: Tendencias 2025 (AI & Analytics)
*Objetivo: Modernización total mediante Inteligencia Artificial y métricas.*

- [ ] **AI Auto-Tagging & Classification (Zero-Shot)**:
    - Implementación de **Zero-Shot Classification** (usando modelos ligeros como `Knowledgator/GLiClass` o similar onnx) para categorizar highlights automáticamente sin entrenamiento previo.
    - Detección de entidades (NER) para extraer nombres de personajes y lugares automáticamente.
- [ ] **Knowledge Connections Graph**:
    - Visualización de grafo interactivo (usando `Cytoscape.js` o similar) para explorar conexiones entre libros y autores.
    - Exportación a formato `.gexf` para análisis profundo en herramientas como Gephi.
- [ ] **Nerdy Stats & Active Recall**:
    - Dashboard de "Insights de Lectura" (Libros/año, Hora de lectura).
    - **Daily Review / Active Recall**: Popup o vista de "Morning Wisdom" que muestra 3 highlights aleatorios antiguos para reforzar la memoria (estilo Anki/Readwise).
- [ ] **Integración Obsidian Premium**:
    - Exportación Markdown con **YAML Frontmatter** rico para plugins como *Dataview*:
        - Campos: `total_highlights`, `category`, `finished_date`, `cover_url`.

## Fase 8: Technical Excellence (Robustez & Mantenibilidad)
*Objetivo: Elevar el estándar de ingeniería para garantizar estabilidad en producción.*

- [ ] **UI Robustness & Error Handling**:
    - Implementar un **Global Exception Handler** (`sys.excepthook`) para capturar crashes no controlados y mostrar un diálogo de error amigable en lugar de cerrar la app.
    - Revisar y blindar la comunicación entre hilos (Signals & Slots) para evitar `AttributeError` o condiciones de carrera en actualizaciones de UI.
- [ ] **Logging de Producción**:
    - Configurar `RotatingFileHandler` para guardar logs en el directorio de usuario (ej. AppData/Local) con rotación automática, esencial para debugging post-release.
- [ ] **Testing de UI**:
    - Integrar `pytest-qt` para realizar pruebas automáticas de la interfaz gráfica, simulando clics y flujos de usuario para prevenir regresiones.
- [ ] **Refactorización de Plataforma**:
    - Mover lógica específica de SO (como el fix de iconos de Windows en `main.py`) a un módulo utilitario `platform_utils.py` para mantener el entry point limpio.
- [ ] **Build Automation (Cross-Platform)**:
    - Crear scripts `Makefile` o `build.sh` para facilitar la compilación local en Linux/macOS usando PyInstaller, complementando el `build_exe.bat` de Windows.
