import json
import chromadb
from chromadb.utils import embedding_functions

# 1️⃣ PersistentClient kullan (in-memory değil!)
client = chromadb.PersistentClient(path="./chroma_db")  # ✅ BUNU KULLAN

# 2️⃣ Ollama embedding fonksiyonu
embedding_fn = embedding_functions.OllamaEmbeddingFunction(
    model_name="nomic-embed-text",
    url="http://localhost:11434/api/embeddings"
)

# 3️⃣ Koleksiyonu sil ve yeniden oluştur
collection_name = "courses"

try:
    client.delete_collection(name=collection_name)
    print(f"✅ Eski koleksiyon silindi")
except:
    print(f"⚠️ Koleksiyon zaten yoktu")

# Embedding fonksiyonu ile koleksiyon oluştur
collection = client.create_collection(
    name=collection_name,
    embedding_function=embedding_fn
)

print("✅ Ollama embedding fonksiyonu başarıyla oluşturuldu")

# 4️⃣ JSON dosyasını yükle
with open("courses_full.json", "r", encoding="utf-8") as f:
    courses = json.load(f)

# 5️⃣ Her kursu ChromaDB'ye ekle
for idx, course in enumerate(courses):
    doc_text = f"{course['course_name']}. {course['description']}"
    
    collection.add(
        documents=[doc_text],
        metadatas=[course],
        ids=[str(idx)]
    )
    
    if (idx + 1) % 10 == 0:
        print(f"İşlenen kurs: {idx + 1}/{len(courses)}")

print(f"\n✅ {len(courses)} kurs './chroma_db' dizinine kaydedildi")
print(f"📂 Veritabanı yolu: ./chroma_db/chroma.sqlite3")

# 6️⃣ Test sorgusu
print("\n--- Test Sorgusu ---")
results = collection.query(
    query_texts=["python programming"],
    n_results=3
)

print(f"Bulunan sonuç sayısı: {len(results['documents'][0])}")

for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"\n{i+1}. Kurs: {metadata['course_name']}")
    print(f"   Platform: {metadata.get('platform', 'N/A')}")
    print(f"   Açıklama: {doc[:100]}...")

print(f"\n✅ Koleksiyon toplam döküman sayısı: {collection.count()}")