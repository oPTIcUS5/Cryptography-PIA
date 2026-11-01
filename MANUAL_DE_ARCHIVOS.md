# Manual de código: explicación archivo por archivo

## Arquitectura

**Cliente** (HTML/JavaScript) ⇆ **Flask** (sesión, autenticación, guardado) ⇆ **SQLite** (identidades, sobres cifrados). La autoridad ejecuta el escrutinio **fuera del servidor web** desde la terminal local. Los datos reales de una elección nunca se usan.

| Ruta | Contenido y responsabilidad | Entradas / salidas |
|---|---|---|
| `requirements.txt` | Dependencias y rangos compatibles | `pip install -r requirements.txt` |
| `.gitignore` | Impide subir claves privadas, credenciales y bases locales | Git ignora `data/` |
| `launcher.py` | Agrega `src/` al path y arranca Flask local | URL `127.0.0.1:5000` |
| `manage.py` | Puerta de entrada al CLI administrativo | `init`, `close`, `tally`, `verify` |
| `app.py` | HTTP, cookies, CSRF, rutas de páginas y API | HTML/JSON |
| `src/votoseguro/__init__.py` | Marca paquete Python | Sin lógica |
| `src/votoseguro/config.py` | Identificador electoral, candidatos, rutas, límites | Constantes |
| `src/votoseguro/crypto.py` | Generación RSA-3072, Ed25519, AES-GCM y SHA-256 | Sobres Base64 y firmas |
| `src/votoseguro/storage.py` | Esquema SQLite, unicidad, transacciones y cadena SHA-256 | Votos cifrados, huellas |
| `src/votoseguro/services.py` | Argon2id y autenticación, escrutinio, firma de manifiestos | Voto válido o inválido, resultados |
| `src/votoseguro/manage.py` | Operaciones restringidas a consola local | Crea archivos en `data/` |
| `templates/base.html` | Plantilla general con navegación y aviso académico | Página base |
| `templates/login.html` | Formulario de autenticación con CSRF | Cuenta y contraseña |
| `templates/vote.html` | Selección del candidato con radios y botón cifrar | Identificador de candidato |
| `templates/receipt.html` | Comprobante de hash cifrado, sin candidato | Huella SHA-256 |
| `templates/audit.html` | Lista pública de huellas y cadena de integridad | Tabla de hashes |
| `templates/results.html` | Escrutinio firmado cuando está disponible | Resultados ficticios |
| `static/vote.js` | Web Crypto: cifra el voto ANTES de enviarlo al servidor | Sobre cifrado JSON |
| `static/styles.css` | Diseño visual adaptable a móvil | Apariencia |
| `tests/conftest.py` | Base de datos y claves temporales por prueba | Aislamiento |
| `tests/test_election.py` | 20 pruebas de autenticación, manipulación, doble voto, criptografía y escrutinio | Éxito / falla |
| `scripts/test_browser_crypto.mjs` | Cifra como navegador en Node; Python comprueba el descifrado | JSON cifrado |
| `docs/` | Capítulos y diagramas TikZ del reporte | PDF compilado |
| `evidencias/README.md` | Capturas pendientes de realizar en Mac | Evidencias auténticas |

## Base de datos

`voters(username, password_hash, has_voted)` separa el estado de participación de los sobres cifrados. `ballots(id, receipt, wrapped_key, nonce, ciphertext, prev_hash, chain_hash, created_at)` no incluye el identificador de votante. `settings` almacena el estado de la elección. Se reconoce la posibilidad de correlación por tiempo y acceso al servidor.

## Contratos de API

- `GET /api/config`: devuelve `election_id`, candidaturas, estado, clave pública RSA DER-SPKI Base64.
- `POST /login`: formulario con usuario, contraseña y CSRF; éxito redirige a `/votar`.
- `POST /api/vote`: sesión activa + cabecera `X-CSRF-Token` + JSON con **exactamente** tres campos: `wrapped_key`, `nonce`, `ciphertext`. Retorna `receipt` en formato hexadecimal SHA-256.
- `GET /comprobante/<hash>`: confirma existencia de huella cifrada.
- `GET /auditoria`: lista huellas y eslabones de la cadena SHA-256.
- `GET /resultados`: escrutinio cuando el administrador generó el manifiesto.

## Por qué no se cifra directamente con RSA

RSA-OAEP admite mensajes cortos; resulta más eficiente usar RSA para proteger una clave AES aleatoria, y AES-GCM para cifrar el texto de la boleta. La autoridad necesita la clave privada RSA solo al contar.

## Propiedades demostradas y propiedades NO demostradas

**Demostradas por pruebas:** reversibilidad para autoridad autorizada, detección de modificación del texto cifrado, bloqueo de doble voto por cuenta, detección de alteración de cadena, firma/verificación de resultados, interoperabilidad JS/Python.

**NO demostradas:** secreto ante autoridad corrupta, coacción, pruebas verificables de conteo correcto, integridad frente a malware y cumplimiento de requisitos electorales legales.

## Integridad del registro

`receipt = SHA256(JSON_canónico(election_id, wrapped_key, nonce, ciphertext))`.

`H_0 = 0000...0000` (64 caracteres hexadecimales).

`H_i = SHA256(H_{i-1} || ':' || i || ':' || receipt_i)`.

La firma final Ed25519 ancla el hash final; si alguien modifica después los registros, la comparación con el manifiesto firmado permite detectar el cambio, siempre que el público conserve el manifiesto original y la clave pública correcta.
