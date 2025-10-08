#!/usr/bin/env python3
"""
Chat API - Flask API for RAG-powered chat using OpenRouter
"""

import os
import json
from typing import List, Dict, Any

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from openai import OpenAI

from rag_processor import RAGProcessor


app = Flask(__name__, static_folder='../docs')
CORS(app)

# Initialize RAG
rag = RAGProcessor()

# Initialize OpenRouter client
openrouter_key = os.getenv('OPENROUTER_API_KEY')
if not openrouter_key:
    print("⚠️  OPENROUTER_API_KEY not set - chat will not work")

client = OpenAI(
    api_key=openrouter_key or "dummy",
    base_url="https://openrouter.ai/api/v1"
)

MODEL = os.getenv('LLM_MODEL', 'anthropic/claude-3.5-sonnet')


@app.route('/')
def index():
    """Serve main page"""
    return send_from_directory('../docs', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('../docs', path)


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint with RAG
    
    Request body:
    {
        "message": "user message",
        "history": [{"role": "user", "content": "..."}, ...]
    }
    """
    try:
        data = request.json
        message = data.get('message', '')
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Search for relevant context
        search_results = rag.search(message, top_k=5)
        
        # Build context from search results
        context_parts = []
        for result in search_results:
            chunk = result['chunk']
            score = result['score']
            filename = chunk['metadata']['filename']
            text = chunk['text']
            
            context_parts.append(f"[From {filename}, relevance: {score:.2f}]\n{text}")
        
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."
        
        # Build prompt
        system_prompt = f"""You are a helpful assistant that answers questions about Department of Defense appropriations and reprogramming documents.

Use the following context from the documents to answer the user's question. If the context doesn't contain relevant information, say so.

CONTEXT:
{context}

Instructions:
- Answer based on the provided context
- Cite specific documents when possible
- If the context doesn't have the answer, say "I don't have enough information in the documents to answer that."
- Be concise but thorough
- Use specific numbers and details from the documents"""

        # Build messages
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add history (last 5 messages)
        messages.extend(history[-5:])
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        # Call OpenRouter
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        answer = response.choices[0].message.content
        
        # Return response with sources
        return jsonify({
            'answer': answer,
            'sources': [
                {
                    'filename': r['chunk']['metadata']['filename'],
                    'score': r['score'],
                    'text': r['chunk']['text'][:200] + '...'
                }
                for r in search_results[:3]
            ]
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def stats():
    """Get RAG statistics"""
    return jsonify({
        'total_chunks': len(rag.chunks),
        'total_documents': len(set(c['metadata']['filename'] for c in rag.chunks)),
        'model': MODEL,
        'ready': len(rag.chunks) > 0
    })


@app.route('/api/documents', methods=['GET'])
def documents():
    """List available documents"""
    docs = {}
    for chunk in rag.chunks:
        filename = chunk['metadata']['filename']
        if filename not in docs:
            docs[filename] = {
                'filename': filename,
                'pages': chunk['metadata'].get('pages', 0),
                'chunks': 0
            }
        docs[filename]['chunks'] += 1
    
    return jsonify({
        'documents': list(docs.values()),
        'total': len(docs)
    })


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run chat API server')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if len(rag.chunks) == 0:
        print("⚠️  No embeddings found. Run: python src/rag_processor.py --rebuild")
        print("   (This will process all PDFs and create embeddings)")
    
    print(f"\n🚀 Starting chat API server...")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Chat UI: http://{args.host}:{args.port}/chat.html")
    print(f"   Chunks loaded: {len(rag.chunks)}")
    print(f"   Model: {MODEL}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
