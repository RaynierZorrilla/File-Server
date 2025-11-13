# Files & Images Server (FastAPI)

Servidor minimalista y productivo para manejar archivos, videos e imágenes:
- Subida múltiple
- Metadatos en SQLite
- Descarga segura
- Miniaturas con Pillow
- Docker listo

## Correr en local
Ver sección Quickstart en el documento principal.

## Producción
- Servir detrás de un proxy (Nginx/Caddy) y habilitar HTTPS.
- Montar volumen persistente para `/app/storage`.
- Ajustar `MAX_FILE_SIZE_MB` y listas de extensiones permitidas.

## Ideas de mejora
- Autenticación JWT y roles
- Presigned URLs temporales para descarga
- Antivirus/clamav en background
- Subida directa a S3 y CDN