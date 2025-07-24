# index_faqs.py - Script para executar APENAS uma vez
import os
import glob
from pathlib import Path

from knowledge.knowledge_base import create_faq_collection, index_structured_faqs_to_chromadb, load_faq_content, setup_chromadb_client

def indexar_todos_faqs():
    """
    Command principal para indexar todos os arquivos FAQ.
    Execute isso UMA VEZ ou quando adicionar novos FAQs.
    """

    print("🚀 INICIANDO INDEXAÇÃO DE TODOS OS FAQs")
    print("="*50)

    # 1. Setup do ChromaDB
    client = setup_chromadb_client()
    collection = create_faq_collection(client)

    # 2. Encontrar todos os arquivos TXT de FAQ
    faq_directory = "./src/faqs/"  # Diretório com seus arquivos
    faq_files = glob.glob(f"{faq_directory}*.txt")

    if not faq_files:
        print("❌ Nenhum arquivo TXT encontrado em", faq_directory)
        return

    print(f"📁 Encontrados {len(faq_files)} arquivos FAQ:")
    for file in faq_files:
        print(f"  - {Path(file).name}")

    # 3. Indexar cada arquivo
    total_faqs = 0

    for faq_file in faq_files:
        print(f"\n📝 Processando: {Path(faq_file).name}")

        try:
            # Parse do arquivo
            faqs = load_faq_content(faq_file)


            result = index_structured_faqs_to_chromadb(faq_file, collection)

            if result["success"]:
                total_faqs += result["indexed_count"]
                print(f"✅ {result['indexed_count']} FAQs indexados")
            else:
                print(f"❌ Erro: {result['error']}")


        except Exception as e:
            print(f"❌ Erro ao processar {faq_file}: {e}")

    print(f"\n🎉 INDEXAÇÃO CONCLUÍDA!")
    print(f"📊 Total de FAQs indexados: {total_faqs}")
    print(f"💾 Base vetorial salva em: ./chroma_db/")

    return collection

# Execute este comando UMA VEZ
if __name__ == "__main__":
    indexar_todos_faqs()
