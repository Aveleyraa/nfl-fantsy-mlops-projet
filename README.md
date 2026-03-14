# NFL Stats Dashboard

Dashboard de estadísticas NFL con FastAPI + Streamlit, usando `nflreadpy` para obtener datos de nflverse.

## Estructura del proyecto

```
nfl-stats/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings (env vars)
│   ├── routers/
│   │   ├── players.py       # GET /players/
│   │   ├── stats.py         # GET /stats/compare
│   │   └── predict.py       # GET /predict/{id}/yards
│   └── services/
│       └── nfl_service.py   # nflreadpy + caché
├── frontend/
│   ├── app.py               # Streamlit dashboard
│   ├── api_client.py        # HTTP client para FastAPI
│   └── charts.py            # Gráficas Plotly
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
└── requirements.txt
```

## Correr en local

### Opción A — sin Docker (más rápido para desarrollo)

```bash
# 1. Clonar e instalar
pip install -r requirements.txt

# 2. Copiar .env
cp .env.example .env

# 3. Terminal 1: backend
python -m backend.main

# 4. Terminal 2: frontend
streamlit run frontend/app.py
```

- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:8501

### Opción B — con Docker Compose

```bash
docker-compose up --build
```

La primera vez que selecciones una temporada, `nflreadpy` descargará
los datos desde nflverse (~30-80MB por temporada). Las siguientes
cargas serán instantáneas gracias al caché en disco (volumen Docker).

---

## Endpoints de la API

| Método | Path | Descripción |
|--------|------|-------------|
| GET | `/players/teams?season=2024` | Lista de equipos |
| GET | `/players/?team=KC&position_group=QB` | Lista de jugadores |
| GET | `/players/{player_id}?season=2024` | Stats de un jugador |
| GET | `/stats/compare?player_a=X&player_b=Y` | Comparativa |
| GET | `/predict/{player_id}/yards?season=2024` | Predicción ML |
| GET | `/docs` | Swagger UI |

---

## Deploy en AWS

### Pre-requisitos
- AWS CLI configurado
- ECR repository creado para `nfl-backend` y `nfl-frontend`

### Pasos

```bash
# 1. Build y push a ECR
AWS_ACCOUNT=123456789012
AWS_REGION=us-east-1

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -f docker/Dockerfile.backend -t nfl-backend .
docker tag nfl-backend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/nfl-backend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/nfl-backend:latest

docker build -f docker/Dockerfile.frontend -t nfl-frontend .
docker tag nfl-frontend:latest $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/nfl-frontend:latest
docker push $AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/nfl-frontend:latest
```

### Infraestructura recomendada (mínima)
- **ECS Fargate**: 2 servicios (backend + frontend), 0.5 vCPU / 1GB RAM cada uno
- **ALB**: HTTP listener → target group Streamlit (port 8501)
- **EFS**: volumen compartido para caché nflreadpy y modelos ML
- **S3** (opcional): backup del caché para no re-descargar en cada deploy

### Variable de entorno en ECS
El contenedor de frontend necesita:
```
API_BASE_URL=http://<backend-internal-alb-dns>:8000
```

---

## Módulo de predicción ML

El endpoint `/predict/{player_id}/yards` ya está conectado.
Para activar el modelo real:

```python
# Entrenar y guardar
from sklearn.ensemble import GradientBoostingRegressor
import joblib

model = GradientBoostingRegressor(n_estimators=200)
model.fit(X_train, y_train)

joblib.dump(model, "ml_models/model_qb_yards.pkl")
# También: model_rb_yards.pkl, model_wr_yards.pkl
```

El router `predict.py` detecta automáticamente el `.pkl` y lo usa.
Si no existe, devuelve una estimación heurística con la misma estructura de respuesta.