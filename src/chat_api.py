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


@app.route('/chat')
def chat_page():
    """Serve chat page"""
    return send_from_directory('../docs', 'chat.html')


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('../docs', path)


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint with RAG and context awareness
    
    Request body:
    {
        "message": "user message",
        "history": [{"role": "user", "content": "..."}, ...],
        "context": {
            "page": "browse.html",
            "type": "data_browser",
            "description": "Browse extracted budget data",
            "filters": {"branch": "Army", "category": "Operation and Maintenance"},
            "selectedData": {...}
        }
    }
    """
    try:
        data = request.json
        message = data.get('message', '')
        history = data.get('history', [])
        context = data.get('context', {})
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Enhance search query with context
        enhanced_query = message
        if context:
            context_info = []
            if context.get('type'):
                context_info.append(f"User is on {context.get('description', 'unknown page')}")
            
            if context.get('filters'):
                filters = context['filters']
                active_filters = [f"{k}: {v}" for k, v in filters.items() if v]
                if active_filters:
                    context_info.append(f"Active filters: {', '.join(active_filters)}")
            
            if context.get('visualization'):
                viz = context['visualization']
                viz_info = []
                if viz.get('fiscalYear'): viz_info.append(f"FY {viz['fiscalYear']}")
                if viz.get('minAmount'): viz_info.append(f"Min amount: ${viz['minAmount']}K")
                if viz_info:
                    context_info.append(f"Visualization settings: {', '.join(viz_info)}")
            
            if context_info:
                enhanced_query = f"{message}\n\nContext: {'; '.join(context_info)}"
        
        # Search for relevant context
        search_results = rag.search(enhanced_query, top_k=5)
        
        # Build context from search results
        context_parts = []
        for result in search_results:
            chunk = result['chunk']
            score = result['score']
            filename = chunk['metadata']['filename']
            text = chunk['text']
            
            context_parts.append(f"[From {filename}, relevance: {score:.2f}]\n{text}")
        
        document_context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."
        
        # Build context-aware prompt
        system_prompt = f"""You are a helpful assistant that answers questions about Department of Defense appropriations and reprogramming documents.

You are currently helping a user who is on: {context.get('description', 'an unknown page')}

Use the following context from the documents to answer the user's question. If the context doesn't contain relevant information, say so.

DOCUMENT CONTEXT:
{document_context}

Instructions:
- Answer based on the provided context
- Be aware of the user's current page context: {context.get('description', 'unknown')}
- If the user has active filters, consider them when answering
- Cite specific documents when possible
- If the context doesn't have the answer, say "I don't have enough information in the documents to answer that."
- Be concise but thorough
- Use specific numbers and details from the documents
- If the user is browsing data, help them understand what they're looking at"""

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


@app.route('/api/chat-widget', methods=['POST'])
def chat_widget():
    """
    Chat endpoint for the client-side widget using GitHub Secrets
    
    Request body:
    {
        "message": "user message",
        "context": {...},
        "history": [...]
    }
    """
    try:
        data = request.json
        message = data.get('message', '')
        context = data.get('context', {})
        history = data.get('history', [])
        
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Check if we have OpenRouter API key
        if not openrouter_key or openrouter_key == "dummy":
            return jsonify({
                'error': 'OpenRouter API key not configured',
                'message': 'The chat service is not available. Please contact the administrator.'
            }), 503
        
        # Search for relevant context using RAG
        search_results = rag.search(message, top_k=5)
        
        # Build context from search results
        context_parts = []
        sources = []
        
        for result in search_results:
            chunk = result['chunk']
            score = result['score']
            filename = chunk['metadata']['filename']
            text = chunk['text']
            
            context_parts.append(f"[From {filename}, relevance: {score:.2f}]\n{text}")
            sources.append({
                'filename': filename,
                'score': score,
                'text': text[:200] + '...'
            })
        
        document_context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant documents found."
        
        # Build context-aware prompt
        system_prompt = f"""You are a helpful assistant that answers questions about Department of Defense appropriations and reprogramming documents.

You are currently helping a user who is on: {context.get('description', 'an unknown page')}

Use the following context from the documents to answer the user's question. If the context doesn't contain relevant information, say so.

DOCUMENT CONTEXT:
{document_context}

Instructions:
- Answer based on the provided context
- Be aware of the user's current page context: {context.get('description', 'unknown')}
- If the user has active filters, consider them when answering
- Cite specific documents when possible
- If the context doesn't have the answer, say "I don't have enough information in the documents to answer that."
- Be concise but thorough
- Use specific numbers and details from the documents
- If the user is browsing data, help them understand what they're looking at"""

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
            'sources': sources[:3]  # Top 3 sources
        })
        
    except Exception as e:
        print(f"Error in chat widget endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


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
        print("   Chat will work but without document context.")
    
    print(f"\n🚀 Starting chat API server...")
    print(f"   URL: http://{args.host}:{args.port}")
    print(f"   Chat UI: http://{args.host}:{args.port}/chat.html")
    print(f"   Widget API: http://{args.host}:{args.port}/api/chat-widget")
    print(f"   Chunks loaded: {len(rag.chunks)}")
    print(f"   Model: {MODEL}")
    print(f"   OpenRouter Key: {'✓ Set' if openrouter_key and openrouter_key != 'dummy' else '✗ Not Set'}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == '__main__':
    main()
