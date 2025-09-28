"""
RAG Retrieval Module using TF-IDF/BM25 with document chunking.
Handles document retrieval from markdown documentation files.
"""

import os
import re
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    content: str
    source_file: str
    chunk_id: int
    start_line: int
    end_line: int
    title: str = ""
    section: str = ""


class DocumentChunker:
    """Handles chunking of markdown documents into retrievable pieces."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
    
    def chunk_document(self, content: str, file_path: str) -> List[DocumentChunk]:
        """Chunk a document into overlapping pieces."""
        lines = content.split('\n')
        chunks = []
        chunk_id = 0
        
        # Extract title from filename
        title = Path(file_path).stem.replace('_', ' ').title()
        
        i = 0
        while i < len(lines):
            # Collect lines for this chunk
            chunk_lines = []
            char_count = 0
            start_line = i
            
            # Find current section header if any
            current_section = self._find_current_section(lines, i)
            
            while i < len(lines) and char_count < self.chunk_size:
                line = lines[i].strip()
                if line:
                    chunk_lines.append(line)
                    char_count += len(line) + 1  # +1 for newline
                i += 1
            
            if chunk_lines:
                chunk_content = '\n'.join(chunk_lines)
                chunk = DocumentChunk(
                    content=chunk_content,
                    source_file=file_path,
                    chunk_id=chunk_id,
                    start_line=start_line,
                    end_line=i - 1,
                    title=title,
                    section=current_section
                )
                chunks.append(chunk)
                chunk_id += 1
            
            # Backtrack for overlap
            if self.overlap > 0 and i < len(lines):
                overlap_chars = 0
                backtrack = 0
                while backtrack < len(chunk_lines) and overlap_chars < self.overlap:
                    overlap_chars += len(chunk_lines[-(backtrack + 1)])
                    backtrack += 1
                i -= backtrack
        
        return chunks
    
    def _find_current_section(self, lines: List[str], current_line: int) -> str:
        """Find the current section header."""
        for i in range(current_line, -1, -1):
            line = lines[i].strip()
            if line.startswith('#'):
                return line.lstrip('#').strip()
        return ""


class HybridRetriever:
    """Hybrid retrieval system using both TF-IDF and BM25."""
    
    def __init__(self, docs_path: str):
        self.docs_path = docs_path
        self.chunks: List[DocumentChunk] = []
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.bm25 = None
        self.tfidf_matrix = None
        self.chunker = DocumentChunker()
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        
        self._load_and_index_documents()
    
    def _load_and_index_documents(self):
        """Load and index all markdown documents."""
        print(f"Loading documents from {self.docs_path}")
        
        # Load all markdown files
        for file_path in Path(self.docs_path).glob("*.md"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Chunk the document
                doc_chunks = self.chunker.chunk_document(content, str(file_path))
                self.chunks.extend(doc_chunks)
                print(f"Loaded {len(doc_chunks)} chunks from {file_path.name}")
                
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        if not self.chunks:
            print("Warning: No documents loaded!")
            return
        
        # Prepare texts for indexing
        chunk_texts = [chunk.content for chunk in self.chunks]
        
        # Build TF-IDF index
        self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(chunk_texts)
        
        # Build BM25 index
        tokenized_chunks = [self._preprocess_text(text) for text in chunk_texts]
        self.bm25 = BM25Okapi(tokenized_chunks)
        
        print(f"Indexed {len(self.chunks)} chunks total")
    
    def _preprocess_text(self, text: str) -> List[str]:
        """Preprocess text for BM25 indexing."""
        # Remove markdown formatting
        text = re.sub(r'[#*_`]', '', text)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Remove links
        
        # Tokenize and clean
        tokens = word_tokenize(text.lower())
        tokens = [self.stemmer.stem(token) for token in tokens 
                 if token.isalnum() and token not in self.stop_words]
        
        return tokens
    
    def retrieve(self, query: str, top_k: int = 5, alpha: float = 0.5) -> List[DocumentChunk]:
        """Retrieve relevant chunks using hybrid TF-IDF + BM25 scoring."""
        if not self.chunks:
            return []
        
        # Preprocess query
        processed_query = self._preprocess_text(query)
        
        # Get BM25 scores
        bm25_scores = self.bm25.get_scores(processed_query)
        
        # Get TF-IDF scores
        query_vector = self.tfidf_vectorizer.transform([query])
        tfidf_scores = cosine_similarity(query_vector, self.tfidf_matrix).flatten()
        
        # Normalize scores
        bm25_scores = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min() + 1e-10)
        tfidf_scores = (tfidf_scores - tfidf_scores.min()) / (tfidf_scores.max() - tfidf_scores.min() + 1e-10)
        
        # Combine scores
        hybrid_scores = alpha * tfidf_scores + (1 - alpha) * bm25_scores
        
        # Get top k chunks
        top_indices = np.argsort(hybrid_scores)[::-1][:top_k]
        
        return [self.chunks[i] for i in top_indices if hybrid_scores[i] > 0.1]


# Global retriever instance
_retriever = None


def get_retriever(docs_path: str) -> HybridRetriever:
    """Get or create the global retriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = HybridRetriever(docs_path)
    return _retriever


def retrieve_context(query: str, docs_path: str, top_k: int = 3) -> tuple[List[str], List[str]]:
    """Retrieve relevant context and chunk IDs for a query."""
    retriever = get_retriever(docs_path)
    relevant_chunks = retriever.retrieve(query, top_k=top_k)
    
    # Format context with source information and collect chunk IDs
    context_list = []
    chunk_ids = []
    for i, chunk in enumerate(relevant_chunks):
        filename = Path(chunk.source_file).stem
        chunk_id = f"{filename}::chunk{chunk.chunk_id}"
        chunk_ids.append(chunk_id)
        
        context_text = f"From {chunk.title}"
        if chunk.section:
            context_text += f" - {chunk.section}"
        context_text += f":\n{chunk.content}"
        context_list.append(context_text)
    
    return context_list, chunk_ids


def search_documents(query: str, docs_path: str, top_k: int = 5) -> List[Dict]:
    """Search documents and return structured results."""
    retriever = get_retriever(docs_path)
    relevant_chunks = retriever.retrieve(query, top_k=top_k)
    
    results = []
    for chunk in relevant_chunks:
        result = {
            'content': chunk.content,
            'source': chunk.source_file,
            'title': chunk.title,
            'section': chunk.section,
            'chunk_id': chunk.chunk_id,
            'lines': f"{chunk.start_line}-{chunk.end_line}"
        }
        results.append(result)
    
    return results


# Utility functions for document analysis
def extract_key_terms(text: str, top_k: int = 10) -> List[Tuple[str, float]]:
    """Extract key terms from text using TF-IDF."""
    vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform([text])
        feature_names = vectorizer.get_feature_names_out()
        scores = tfidf_matrix.toarray()[0]
        
        term_scores = list(zip(feature_names, scores))
        term_scores.sort(key=lambda x: x[1], reverse=True)
        
        return term_scores[:top_k]
    except:
        return []


def get_document_summary(docs_path: str) -> Dict[str, Any]:
    """Get a summary of all documents in the collection."""
    retriever = get_retriever(docs_path)
    
    summary = {
        'total_chunks': len(retriever.chunks),
        'files': {},
        'sections': set(),
        'total_words': 0
    }
    
    for chunk in retriever.chunks:
        filename = Path(chunk.source_file).name
        if filename not in summary['files']:
            summary['files'][filename] = {
                'chunks': 0,
                'title': chunk.title
            }
        
        summary['files'][filename]['chunks'] += 1
        if chunk.section:
            summary['sections'].add(chunk.section)
        
        summary['total_words'] += len(chunk.content.split())
    
    summary['sections'] = list(summary['sections'])
    return summary
