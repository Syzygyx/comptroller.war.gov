#!/usr/bin/env python3
"""
RAG Processor - Processes PDFs and creates vector embeddings for retrieval
"""

import os
import json
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from sentence_transformers import SentenceTransformer


class RAGProcessor:
    """Processes documents for RAG system"""
    
    def __init__(self, 
                 embeddings_dir: str = "data/embeddings",
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG processor
        
        Args:
            embeddings_dir: Directory to store embeddings
            model_name: Sentence transformer model to use
        """
        self.embeddings_dir = Path(embeddings_dir)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        self.chunks_file = self.embeddings_dir / "chunks.json"
        self.embeddings_file = self.embeddings_dir / "embeddings.npy"
        
        self.chunks = []
        self.embeddings = None
        
        # Load existing if available
        self._load_existing()
    
    def _load_existing(self):
        """Load existing chunks and embeddings"""
        if self.chunks_file.exists() and self.embeddings_file.exists():
            print("Loading existing embeddings...")
            with open(self.chunks_file, 'r') as f:
                self.chunks = json.load(f)
            self.embeddings = np.load(self.embeddings_file)
            print(f"Loaded {len(self.chunks)} chunks with embeddings")
    
    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 128) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size in characters
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        words = text.split()
        
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                # Keep overlap
                overlap_words = int(len(current_chunk) * (overlap / chunk_size))
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_size = sum(len(w) + 1 for w in current_chunk)
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def process_document(self, text: str, metadata: Dict[str, Any]) -> int:
        """
        Process a document and add to index
        
        Args:
            text: Document text
            metadata: Document metadata (filename, page, etc.)
            
        Returns:
            Number of chunks created
        """
        # Create chunks
        text_chunks = self.chunk_text(text)
        
        # Create chunk objects with metadata
        doc_chunks = []
        for i, chunk in enumerate(text_chunks):
            doc_chunks.append({
                'text': chunk,
                'metadata': {
                    **metadata,
                    'chunk_id': i,
                    'total_chunks': len(text_chunks)
                }
            })
        
        # Generate embeddings
        chunk_texts = [c['text'] for c in doc_chunks]
        new_embeddings = self.model.encode(chunk_texts, show_progress_bar=True)
        
        # Add to collection
        self.chunks.extend(doc_chunks)
        
        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])
        
        return len(doc_chunks)
    
    def process_ocr_results(self, ocr_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Process multiple OCR results
        
        Args:
            ocr_results: List of OCR result dictionaries
            
        Returns:
            Processing statistics
        """
        stats = {
            'documents_processed': 0,
            'total_chunks': 0,
            'failed': 0
        }
        
        for result in ocr_results:
            if 'error' in result:
                stats['failed'] += 1
                continue
            
            try:
                text = result.get('text', '')
                metadata = {
                    'filename': result.get('file', 'unknown'),
                    'pages': result.get('pages_processed', 0),
                    'engine': result.get('engine', 'unknown')
                }
                
                chunks_created = self.process_document(text, metadata)
                stats['total_chunks'] += chunks_created
                stats['documents_processed'] += 1
                
            except Exception as e:
                print(f"Error processing {result.get('file', 'unknown')}: {e}")
                stats['failed'] += 1
        
        return stats
    
    def save(self):
        """Save chunks and embeddings to disk"""
        print("Saving embeddings...")
        with open(self.chunks_file, 'w') as f:
            json.dump(self.chunks, f, indent=2)
        
        if self.embeddings is not None:
            np.save(self.embeddings_file, self.embeddings)
        
        print(f"✓ Saved {len(self.chunks)} chunks")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant chunks with scores
        """
        if self.embeddings is None or len(self.chunks) == 0:
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])[0]
        
        # Calculate cosine similarity
        similarities = np.dot(self.embeddings, query_embedding) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
        )
        
        # Get top k
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'chunk': self.chunks[idx],
                'score': float(similarities[idx])
            })
        
        return results


def main():
    """Main entry point for testing"""
    import argparse
    from ocr_processor import OCRProcessor
    
    parser = argparse.ArgumentParser(description='Process PDFs for RAG')
    parser.add_argument('--pdf-dir', default='data/pdfs', help='PDF directory')
    parser.add_argument('--rebuild', action='store_true', help='Rebuild embeddings from scratch')
    
    args = parser.parse_args()
    
    # Initialize
    rag = RAGProcessor()
    
    if args.rebuild or len(rag.chunks) == 0:
        print("Building embeddings from PDFs...")
        
        # Get all PDFs
        pdf_dir = Path(args.pdf_dir)
        pdf_files = list(pdf_dir.glob('*.pdf'))
        
        if not pdf_files:
            print("No PDFs found!")
            return 1
        
        print(f"Found {len(pdf_files)} PDFs")
        
        # Process with OCR
        processor = OCRProcessor()
        ocr_results = processor.batch_process([str(pdf) for pdf in pdf_files], use_ocr=True)
        
        # Build embeddings
        stats = rag.process_ocr_results(ocr_results)
        
        print(f"\n✅ Processing complete:")
        print(f"   Documents: {stats['documents_processed']}")
        print(f"   Chunks: {stats['total_chunks']}")
        print(f"   Failed: {stats['failed']}")
        
        # Save
        rag.save()
    
    # Test search
    print("\nTesting search...")
    results = rag.search("military appropriations", top_k=3)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Score: {result['score']:.3f}")
        print(f"   File: {result['chunk']['metadata']['filename']}")
        print(f"   Text: {result['chunk']['text'][:200]}...")
    
    return 0


if __name__ == '__main__':
    exit(main())
