from app.db import engine
from app.models.base import Base

# Garantizar registro de los modelos (incluyendo Sequence)
from app.models import __init__

print("Creando tablas faltantes en PostgreSQL (Certia FastAPI DB)...")
Base.metadata.create_all(bind=engine)
print("Migración completada exitosamente!")
