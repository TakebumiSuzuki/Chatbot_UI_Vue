import os
from google.cloud import secretmanager
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv('PROJECT_ID')
LOCATION = os.getenv('LOCATION')

GEMINI_HYDE_MODEL = 'gemini-2.5-flash'
GEMINI_EMBEDDING_MODEL = 'gemini-embedding-001'
GEMINI_QA_MODEL = 'gemini-2.5-flash'
# GEMINI_RERANK_MODEL = 'gemini-2.5-flash'

EMBEDDING_DIMENSIONS = 3072
VECTOR_INDEX_REGION = 'us-central1'
INDEX_ENDPOINT_NAME = "projects/59085630263/locations/us-central1/indexEndpoints/7609185613186596864"
DEPLOYED_INDEX_ID = 'youtube_help'

MAX_INPUT = 200
K = 4

def access_secret_version(project_id, secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    payload = response.payload.data.decode("UTF-8")
    return payload

CLOUDSQL_USER = 'root'
CLOUDSQL_PASSWORD = access_secret_version(PROJECT_ID, 'TrueNorthDataBasePassword')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
CLOUDSQL_DATABASE = 'true-north-db'
INSTANCE_CONNECTION_NAME = 'arvato-developments:europe-west1:true-north'
# DATABASE_URL = ('mysql+pymysql://{user}:{password}@{host}:3306/{database}?charset=utf8mb4').format(
#     user=CLOUDSQL_USER,
#     password=CLOUDSQL_PASSWORD,
#     host=DB_HOST,  # ← ここを '127.0.0.1' から変数に変更
#     database=CLOUDSQL_DATABASE
# )



