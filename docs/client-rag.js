/**
 * Client-side RAG implementation for browser
 * Loads embeddings and provides search functionality
 */

class ClientRAG {
    constructor() {
        this.chunks = [];
        this.embeddings = null;
        this.model = null;
        this.initialized = false;
    }

    /**
     * Initialize the RAG system
     */
    async initialize() {
        try {
            console.log('Initializing client-side RAG...');
            
            // Try to load chunks data
            const chunksResponse = await fetch('data/embeddings/chunks.json');
            if (!chunksResponse.ok) {
                console.warn('Chunks file not found, trying alternative paths...');
                // Try alternative paths for different deployments
                const altPaths = [
                    'data/embeddings/chunks.json',
                    './data/embeddings/chunks.json',
                    '/data/embeddings/chunks.json'
                ];
                
                let chunksLoaded = false;
                for (const path of altPaths) {
                    try {
                        const response = await fetch(path);
                        if (response.ok) {
                            this.chunks = await response.json();
                            chunksLoaded = true;
                            break;
                        }
                    } catch (e) {
                        continue;
                    }
                }
                
                if (!chunksLoaded) {
                    throw new Error('Chunks file not found in any expected location');
                }
            } else {
                this.chunks = await chunksResponse.json();
            }
            
            // Try to load embeddings
            const embeddingsResponse = await fetch('data/embeddings/embeddings.npy');
            if (!embeddingsResponse.ok) {
                console.warn('Embeddings file not found, trying alternative paths...');
                // Try alternative paths for different deployments
                const altPaths = [
                    'data/embeddings/embeddings.npy',
                    './data/embeddings/embeddings.npy',
                    '/data/embeddings/embeddings.npy'
                ];
                
                let embeddingsLoaded = false;
                for (const path of altPaths) {
                    try {
                        const response = await fetch(path);
                        if (response.ok) {
                            const embeddingsBuffer = await response.arrayBuffer();
                            this.embeddings = this.parseNumpyArray(embeddingsBuffer);
                            embeddingsLoaded = true;
                            break;
                        }
                    } catch (e) {
                        continue;
                    }
                }
                
                if (!embeddingsLoaded) {
                    throw new Error('Embeddings file not found in any expected location');
                }
            } else {
                // Convert numpy array to JavaScript array
                const embeddingsBuffer = await embeddingsResponse.arrayBuffer();
                this.embeddings = this.parseNumpyArray(embeddingsBuffer);
            }
            
            // Load sentence transformer model
            await this.loadModel();
            
            this.initialized = true;
            console.log(`✅ RAG initialized with ${this.chunks.length} chunks`);
            
        } catch (error) {
            console.error('Failed to initialize RAG:', error);
            this.initialized = false;
            throw error; // Re-throw so the widget can handle it
        }
    }

    /**
     * Load sentence transformer model (using a lightweight model)
     */
    async loadModel() {
        try {
            // Use a simple text similarity approach for now
            // In a real implementation, you'd load a proper sentence transformer
            this.model = {
                encode: (texts) => {
                    // Simple TF-IDF-like encoding for demo
                    return texts.map(text => this.simpleEncode(text));
                }
            };
        } catch (error) {
            console.error('Failed to load model:', error);
            throw error;
        }
    }

    /**
     * Simple text encoding (placeholder for proper sentence transformer)
     */
    simpleEncode(text) {
        // This is a very basic encoding - in production you'd use a proper model
        const words = text.toLowerCase().split(/\s+/);
        const vector = new Array(384).fill(0); // Standard embedding size
        
        // Simple word frequency encoding
        words.forEach(word => {
            const hash = this.simpleHash(word) % 384;
            vector[hash] += 1;
        });
        
        // Normalize
        const norm = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
        return vector.map(val => norm > 0 ? val / norm : 0);
    }

    /**
     * Simple hash function
     */
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return Math.abs(hash);
    }

    /**
     * Parse numpy array from buffer
     */
    parseNumpyArray(buffer) {
        // This is a simplified parser - in production you'd use a proper numpy parser
        const view = new DataView(buffer);
        const shape = [this.chunks.length, 384]; // Assuming 384-dimensional embeddings
        
        const result = [];
        for (let i = 0; i < shape[0]; i++) {
            const row = [];
            for (let j = 0; j < shape[1]; j++) {
                // Read as float32 (4 bytes each)
                const offset = i * shape[1] * 4 + j * 4;
                if (offset + 4 <= buffer.byteLength) {
                    row.push(view.getFloat32(offset, true));
                } else {
                    row.push(0);
                }
            }
            result.push(row);
        }
        
        return result;
    }

    /**
     * Search for relevant chunks
     */
    search(query, topK = 5) {
        if (!this.initialized || !this.embeddings || this.chunks.length === 0) {
            console.warn('RAG not initialized or no data available');
            return [];
        }

        try {
            // Encode query
            const queryEmbedding = this.model.encode([query])[0];
            
            // Calculate cosine similarity
            const similarities = this.calculateSimilarities(queryEmbedding);
            
            // Get top k results
            const topIndices = this.getTopK(similarities, topK);
            
            const results = [];
            for (const idx of topIndices) {
                results.push({
                    chunk: this.chunks[idx],
                    score: similarities[idx]
                });
            }
            
            return results;
            
        } catch (error) {
            console.error('Search error:', error);
            return [];
        }
    }

    /**
     * Calculate cosine similarities
     */
    calculateSimilarities(queryEmbedding) {
        const similarities = [];
        
        for (let i = 0; i < this.embeddings.length; i++) {
            const embedding = this.embeddings[i];
            
            // Calculate cosine similarity
            let dotProduct = 0;
            let normA = 0;
            let normB = 0;
            
            for (let j = 0; j < embedding.length; j++) {
                dotProduct += queryEmbedding[j] * embedding[j];
                normA += queryEmbedding[j] * queryEmbedding[j];
                normB += embedding[j] * embedding[j];
            }
            
            const similarity = dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
            similarities.push(similarity);
        }
        
        return similarities;
    }

    /**
     * Get top K indices
     */
    getTopK(similarities, k) {
        const indexed = similarities.map((score, index) => ({ score, index }));
        indexed.sort((a, b) => b.score - a.score);
        return indexed.slice(0, k).map(item => item.index);
    }

    /**
     * Get statistics
     */
    getStats() {
        return {
            initialized: this.initialized,
            totalChunks: this.chunks.length,
            hasEmbeddings: this.embeddings !== null,
            modelLoaded: this.model !== null
        };
    }
}

// Export for use
window.ClientRAG = ClientRAG;