import faiss
import pickle
import os

index_path = r"c:\Users\aravi\Desktop\project\smart_retail\rag\faiss_index"

try:
    index = faiss.read_index(os.path.join(index_path, "index.faiss"))
    with open(os.path.join(index_path, "index.pkl"), "rb") as f:
        metadata = pickle.load(f)
    
    print(f"Index size: {index.ntotal}")
    print(f"Metadata type: {type(metadata)}")
    print(f"Metadata length: {len(metadata)}")
    print(f"First element: {metadata[0] if len(metadata) > 0 else 'N/A'}")
except Exception as e:
    print(f"Error: {e}")
