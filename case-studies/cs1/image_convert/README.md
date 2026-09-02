# image_convert

Convierte imagenes .heic/.HEIC a JPG (calidad 90) de forma recursiva e idempotente.

## Uso

```bash
python -m image_convert.convert --input <dir> --output <dir> [--delete]
```

- `--input` y `--output` son requeridos.
- `--delete` elimina el `.heic` original solo si la conversion fue exitosa.
- El resultado de cada corrida queda en `image_convert/output/manifest.json`.
