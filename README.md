# VotoSeguro — PIA de Criptografía

> **Prototipo académico. No utilizar en elecciones reales.** Todos los votantes y candidatos son ficticios. La autoridad se considera honesta, conforme al supuesto indicado por el profesor.

## 1. ¿Qué es?

VotoSeguro simula una elección municipal en un sitio web local. Un votante de prueba inicia sesión, el navegador cifra su selección con AES-256-GCM, protege la clave AES con RSA-OAEP, y la urna registra únicamente el **sobre cifrado**. Un bloqueo transaccional de SQLite impide que la misma cuenta emita dos votos. La autoridad cierra la elección desde la terminal, descifra y cuenta los votos y firma los resultados con Ed25519.

## 2. Requisitos

- Python 3.11 o posterior (recomendado Python 3.13).
- Navegador compatible con Web Crypto API (Chrome, Safari o Firefox actual).
- Internet **solo para instalar dependencias** la primera vez; después puede funcionar en `127.0.0.1`.
- Node.js **opcional**, solo para prueba de interoperabilidad JavaScript/Python.
- Overleaf para el reporte LaTeX.

## 3. Cómo instalarlo en macOS

Desde VS Code: `Terminal → New Terminal` y colócate en la raíz donde están `launcher.py` y `requirements.txt`.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Inicialización (SOLO UNA VEZ)

```bash
python manage.py init
```

Crea cuatro archivos de claves criptográficas, una base de datos de prueba y cinco cuentas ficticias. Sus credenciales aleatorias aparecen en `data/demo_credentials.txt`.

**Nunca subas `data/` a un repositorio.** Contiene claves privadas y contraseñas de demostración. La carpeta está ignorada por Git mediante `.gitignore`.

### Iniciar el servidor local

```bash
python launcher.py
```

Abre: **http://127.0.0.1:5000/login**.

Selecciona una cuenta del archivo local de credenciales, inicia sesión, selecciona una candidatura ficticia y pulsa **Cifrar y registrar mi voto**. Guarda una captura del comprobante.

### Cerrar y contar

En una segunda terminal, desde la misma carpeta (con el entorno activado):

```bash
python manage.py close
python manage.py tally
python manage.py verify
```

- `close`: impide registrar nuevos votos.
- `tally`: verifica la cadena, descifra votos con la clave privada **local** y publica `data/results.json` y `data/audit.json`.
- `verify`: verifica la firma de resultados y su coherencia con la cadena pública.

Abre `/resultados` en el navegador para mostrar los resultados ficticios.

### Pruebas automatizadas

```bash
python -m pytest -q
```

Se incluyen 20 pruebas de funciones y persistencia, incluidas una prueba de compatibilidad JavaScript/Python (si Node está disponible) y dos votos concurrentes. Para comprobar JavaScript sin ejecutar el servidor:

```bash
node --check static/vote.js
```

**Nota de verificación:** en el entorno de elaboración se ejecutaron 20 pruebas con éxito; el servidor Flask no se pudo arrancar allí porque no estaba instalada esa dependencia. Ejecuta también el flujo web en tu Mac para obtener evidencias reales del front-end.

## 4. Qué contiene cada carpeta

- `src/votoseguro/config.py`: identificador de elección, candidaturas ficticias y rutas.
- `src/votoseguro/crypto.py`: RSA-OAEP, AES-GCM, Ed25519, SHA-256, Base64 y claves.
- `src/votoseguro/storage.py`: tablas SQLite y registro atómico de votos.
- `src/votoseguro/services.py`: contraseñas Argon2id, auditoría y escrutinio.
- `src/votoseguro/manage.py`: inicialización, cierre, conteo y verificación desde terminal.
- `app.py`: rutas HTTP de Flask, sesiones, CSRF y cabeceras de seguridad.
- `launcher.py`: arranque local sin necesidad de instalar el paquete en modo editable.
- `manage.py`: acceso rápido a comandos administrativos desde la raíz.
- `templates/`: pantallas HTML: acceso, voto, comprobante, auditoría y resultados.
- `static/`: CSS y el JavaScript que cifra los votos en el navegador.
- `tests/`: casos de prueba independientes de la interfaz Flask.
- `scripts/`: ejercicio de interoperabilidad JavaScript/Python.
- `data/`: **privada**, autogenerada; no se comparte.
- `docs/`: reporte LaTeX y diagramas editables.
- `evidencias/`: instrucciones de capturas para el reporte.
- `MANUAL_DE_ARCHIVOS.md`: explicación archivo por archivo y correspondencia con la rúbrica.

## 5. Protocolo resumido

1. Autoridad local prepara claves RSA y Ed25519, candidatos y cuentas de prueba.
2. Ciudadano de prueba se autentica con contraseña cuyo hash se verifica usando Argon2id.
3. El navegador consulta la clave pública RSA de la elección.
4. El navegador genera al azar una clave AES de 256 bits y un nonce de 96 bits.
5. Cifra el voto con AES-GCM, usando el identificador electoral como datos adicionales autenticados (AAD).
6. Protege la clave AES con RSA-OAEP SHA-256 y remite el sobre cifrado por POST.
7. SQLite marca a la cuenta como votante que ya participó y guarda el sobre en una transacción atómica.
8. El sistema devuelve la huella SHA-256 del sobre y agrega un eslabón a la cadena de registros.
9. Al cerrar, la autoridad comprueba la cadena, descifra con RSA/AES, cuenta los votos válidos y firma el manifiesto con Ed25519.
10. Se publica un registro de huellas y resultados firmados para una auditoría parcial.

## 6. Limitaciones IMPORTANTES

- **No hay anonimato criptográfico completo:** se evita guardar la identidad junto al voto, pero una autoridad con acceso a logs, sesiones y tiempos podría correlacionar eventos. Asumimos una autoridad honesta.
- **La identidad no se verifica fuera de las cuentas ficticias**: no se integra INE, padrón oficial ni biometría.
- **No hay verificación universal del conteo:** la firma prueba que la autoridad publicó esos resultados, no que el descifrado se hizo correctamente. Eso requeriría mecanismos criptográficos adicionales.
- **No hay resistencia a malware, coerción, robo de dispositivos o servidor malicioso.**
- Las cookies se marcan `Secure` si se sirve por HTTPS (`VOTOSEGURO_HTTPS=1`). En `127.0.0.1` se usa HTTP solo para pruebas locales. Si se desplegara públicamente, serían obligatorios HTTPS, gestión de claves con HSM, monitorización y controles de acceso administrativos.
- El **servidor Flask de desarrollo no es un servidor de producción**.
- No es una blockchain distribuida: se usa una cadena SHA-256 cuyos resultados se firman al cerrar.

## 7. Cómo preparar el informe en Overleaf

Importa el ZIP `VotoSeguro_Overleaf.zip` como proyecto nuevo en Overleaf, selecciona `reporte.tex` como archivo principal y compila con `pdfLaTeX`. Personaliza la portada y añade las capturas auténticas siguiendo `evidencias/README.md`.

## 8. Checklist para la entrega

- [x] Diseño del protocolo y arquitectura técnica.
- [x] Implementación de cifrado de voto, registro y escrutinio.
- [x] Hashes Argon2id, Ed25519 y SHA-256.
- [x] Pruebas de función y concurrencia.
- [x] Documento LaTeX y diagramas TikZ.
- [ ] Probar el flujo web completo en macOS con Flask instalado.
- [ ] Tomar capturas personales de funcionamiento.
- [ ] Llenar portada y verificar formato final del PDF.
- [ ] Confirmar con el docente si pide ZIP + PDF o solo PDF con código anexo.
