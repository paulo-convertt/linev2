import os
import glob
import re
from typing import List, Dict
from pymilvus import MilvusClient, connections
from pymilvus import FieldSchema, CollectionSchema, DataType, Collection
from openai import OpenAI
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

# Load environment variables
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=api_key)

# Connect to Milvus
milvus_uri = os.getenv('MILVUS_URI')
milvus_token = os.getenv('MILVUS_TOKEN')

if not milvus_uri:
    raise ValueError("MILVUS_URI environment variable is required")
if not milvus_token:
    raise ValueError("MILVUS_TOKEN environment variable is required")

# Establish connection using connections module
connections.connect(
    alias="default",
    uri=milvus_uri,
    token=milvus_token
)

# Also create MilvusClient for additional operations if needed
milvus_client = MilvusClient(uri=milvus_uri, token=milvus_token)
print(f"Connected to Milvus successfully")

# Define collection schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),  # OpenAI embedding size
    FieldSchema(name="q", dtype=DataType.VARCHAR, max_length=2048),
    FieldSchema(name="sq", dtype=DataType.VARCHAR, max_length=4096),
    FieldSchema(name="a", dtype=DataType.VARCHAR, max_length=8192),
    FieldSchema(name="t", dtype=DataType.VARCHAR, max_length=2048),
    FieldSchema(name="tags", dtype=DataType.VARCHAR, max_length=1024),
    FieldSchema(name="source_file", dtype=DataType.VARCHAR, max_length=512)
]

schema = CollectionSchema(fields, description="FAQ collection for chatbot")

# Create or get collection
collection_name = "faq_collection"
try:
    collection = Collection(name=collection_name, schema=schema)
    print(f"Collection '{collection_name}' created successfully")
except Exception as e:
    print(f"Collection might already exist: {e}")
    collection = Collection(name=collection_name)

def get_embedding(text: str) -> List[float]:
    """Generate embedding for given text using OpenAI API"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def parse_faq_file(file_path: str) -> List[Dict]:
    """Parse a single FAQ file and return list of FAQ entries"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split content by '---' separator
    entries = content.split('---')
    faq_entries = []

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        # Parse each field using regex
        q_match = re.search(r'q:\s*(.*?)(?=\n\n|\nsq:|$)', entry, re.DOTALL)
        sq_match = re.search(r'sq:\s*(.*?)(?=\n\n|\na:|$)', entry, re.DOTALL)
        a_match = re.search(r'a:\s*(.*?)(?=\n\n|\nt:|$)', entry, re.DOTALL)
        t_match = re.search(r't:\s*(.*?)(?=\n\n|\ntags:|$)', entry, re.DOTALL)
        tags_match = re.search(r'tags:\s*(.*?)(?=\n\n|$)', entry, re.DOTALL)

        if q_match and a_match:  # At minimum, we need question and answer
            faq_entry = {
                'q': q_match.group(1).strip() if q_match else '',
                'sq': sq_match.group(1).strip() if sq_match else '',
                'a': a_match.group(1).strip() if a_match else '',
                't': t_match.group(1).strip() if t_match else '',
                'tags': tags_match.group(1).strip() if tags_match else '',
                'source_file': os.path.basename(file_path)
            }
            faq_entries.append(faq_entry)

    return faq_entries

def load_all_faqs(faqs_folder: str) -> List[Dict]:
    """Load and parse all FAQ files from the faqs folder"""
    all_faqs = []

    # Get all .txt files from the faqs folder
    faq_files = glob.glob(os.path.join(faqs_folder, "*.txt"))

    print(f"Found {len(faq_files)} FAQ files:")
    for file_path in faq_files:
        print(f"  - {os.path.basename(file_path)}")

    for file_path in faq_files:
        try:
            faqs = parse_faq_file(file_path)
            all_faqs.extend(faqs)
            print(f"Loaded {len(faqs)} FAQs from {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    return all_faqs

def index_faqs_to_milvus(faq_entries: List[Dict]):
    """Index FAQ entries to Milvus collection"""
    if not faq_entries:
        print("No FAQ entries to index")
        return

    print(f"Indexing {len(faq_entries)} FAQ entries...")

    # Prepare data lists for each field
    embeddings = []
    questions = []
    sub_questions = []
    answers = []
    text_refs = []
    tags_list = []
    source_files = []

    for i, entry in enumerate(faq_entries):
        try:
            # Create text for embedding (combine question and sub-questions)
            text_for_embedding = f"{entry['q']} {entry['sq']}"
            embedding = get_embedding(text_for_embedding)

            embeddings.append(embedding)
            questions.append(entry['q'])
            sub_questions.append(entry['sq'])
            answers.append(entry['a'])
            text_refs.append(entry['t'])
            tags_list.append(entry['tags'])
            source_files.append(entry['source_file'])

            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(faq_entries)} entries...")

        except Exception as e:
            print(f"Error processing entry {i}: {e}")
            continue

    if embeddings:
        try:
            # Prepare data in the format Milvus expects (by columns)
            data_to_insert = [
                embeddings,
                questions,
                sub_questions,
                answers,
                text_refs,
                tags_list,
                source_files
            ]

            # Insert data into collection
            collection.insert(data_to_insert)
            collection.flush()
            print(f"Successfully indexed {len(embeddings)} FAQ entries to Milvus")

            # Create index for better search performance
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 128}
            }
            collection.create_index(field_name="embedding", index_params=index_params)
            print("Index created successfully")

        except Exception as e:
            print(f"Error inserting data to Milvus: {e}")

if __name__ == "__main__":
    # Define the path to the FAQs folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    faqs_folder = os.path.join(os.path.dirname(current_dir), "faqs")

    print(f"Loading FAQs from: {faqs_folder}")

    # Load all FAQ entries
    faq_entries = load_all_faqs(faqs_folder)
    print(f"Total FAQ entries loaded: {len(faq_entries)}")

    if faq_entries:
        # Index to Milvus
        index_faqs_to_milvus(faq_entries)
    else:
        print("No FAQ entries found to index")
