from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Carregar variáveis de ambiente do .env
try:
    from dotenv import load_dotenv
    # Procurar o arquivo .env na raiz do projeto
    env_path = Path(__file__).parent.parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    # Se python-dotenv não estiver instalado, continuar sem carregar
    pass

# Para desenvolvimento local: localhost, para Docker: nome do service
default_db_url = "postgresql://postgres:postgres@localhost:5432/consorcio_db"
DATABASE_URL = os.getenv("DATABASE_URL", default_db_url)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
