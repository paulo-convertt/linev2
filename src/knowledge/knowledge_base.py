from pathlib import Path
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer

class ConsorcioKnowledgeBase:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("consorcio_knowledge")
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.load_knowledge_base()

    def load_knowledge_base(self):
      """Carrega base de conhecimento de arquivos de texto"""
      faq_folder = Path("faq")
      if faq_folder.exists():
          for txt_file in faq_folder.glob("*.txt"):
              with open(txt_file, 'r', encoding='utf-8') as f:
                  content = f.read().strip()
                  if content:
                      doc_data = [{
                          "id": f"faq_{txt_file.stem}",
                          "content": content,
                          "metadata": {"source": txt_file.name}
                      }]
                      self._index_documents(doc_data)

    def _index_documents(self, documents: List[Dict]):
        """Indexa documentos na base vetorial"""
        for doc in documents:
            doc_id = doc.get('id', str(len(self.collection.get()['ids'])))
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})

            embedding = self.encoder.encode([content]).tolist()[0]

            self.collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[doc_id]
            )

    def search_knowledge(self, query: str, n_results: int = 3) -> List[Dict]:
        """Busca conhecimento relevante baseado na query"""
        query_embedding = self.encoder.encode([query]).tolist()[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return [
            {
                "content": doc,
                "metadata": meta,
                "score": score
            }
            for doc, meta, score in zip(
                results['documents'][0],
                results['metadatas'][0],
                results['distances'][0]
            )
        ]
