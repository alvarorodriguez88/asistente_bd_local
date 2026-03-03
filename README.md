# Asistente de base de datos local

Sistema completo dockerizado que permite hacer preguntas en lenguaje natural sobre una base de datos de ventas e inventario.

El sistema:

* Genera consultas SQL automáticamente mediante un modelo LLM (Ollama)
* Ejecuta únicamente consultas seguras (SELECT)
* Devuelve una respuesta redactada de forma natural

---

# 1. Arquitectura

El proyecto está compuesto por tres servicios:

* **MySQL** → Base de datos (ventas, productos, inventario)
* **FastAPI** → Backend y orquestador del modelo
* **Ollama** → Modelo LLM que genera SQL y redacta respuestas

Todo corre en contenedores Docker mediante `docker compose`.

---

# 2. Requisitos

* Docker
* Docker Compose

No es necesario tener Python ni MySQL instalados localmente.

---

# 3. Instalación

```bash
git clone https://github.com/TU_USUARIO/TU_REPO.git
cd asistente_bd_local

cp .env.example .env

docker compose up -d --build
```

La primera vez tardará unos minutos mientras se descargan las imágenes base.

---

# 4. Descargar el modelo en Ollama

Este paso solo es necesario la primera vez.

Ejemplo usando `gemma3`:

```bash
docker exec -it ollama_tienda ollama pull gemma3
```

Puedes usar otros modelos si tu equipo tiene menos RAM.

---

# 5. Probar la API

## Swagger UI

Abrir en el navegador:

```
http://localhost:8000/docs
```

---

## Ejemplo con curl

```bash
curl -X POST http://localhost:8000/ask/answer \
  -H "Content-Type: application/json" \
  -d '{"question":"¿Cuál es el producto más vendido?"}'
```

---

# 6. Base de datos

La base de datos se crea automáticamente al iniciar el contenedor por primera vez.

Incluye:

* productos
* inventario
* clientes
* ventas
* venta_lineas

Los scripts SQL se encuentran en:

```
mysql-init/
```

---

# 7. Comandos útiles

## Ver logs

```bash
docker compose logs -f api
docker compose logs -f mysql
docker compose logs -f ollama
```

## Reiniciar servicios

```bash
docker compose restart
```

## Apagar contenedores

```bash
docker compose down
```

## Reset completo (borra datos y modelos)

```bash
docker compose down -v
```

---

# 8. Seguridad

* Solo se permiten consultas `SELECT`
* Se validan tablas permitidas
* Se añade `LIMIT` automáticamente
* No se ejecutan instrucciones destructivas

---

# 9. Ejemplos de preguntas interesantes

* ¿Cuál es el producto más vendido?
* Facturación total de los últimos 7 días
* Productos por debajo del stock mínimo
* Método de pago más utilizado
* Top 5 productos por ingresos
* Clientes con mayor gasto acumulado

---

# 10. Desarrollo

Si modificas el código del backend:

```bash
docker compose up -d --build
```

---

# Álvaro Rodríguez González

Desarrollado como proyecto de experimentación con LLM + SQL + Docker.
