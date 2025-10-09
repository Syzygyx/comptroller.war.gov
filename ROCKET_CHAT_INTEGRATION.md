# Rocket.Chat Widget Integration

This document describes the Rocket.Chat widget integration that has been added to all pages of the Comptroller War Gov application.

## Overview

The Rocket.Chat widget provides context-sensitive chat functionality across all pages of the application. It uses client-side RAG (Retrieval-Augmented Generation) with OpenRouter to provide intelligent responses about the budget data without requiring a local server.

## Features

### 🎯 Context Awareness
- **Page Detection**: Automatically detects which page the user is on
- **Filter Awareness**: Understands active filters on the browse page
- **Visualization Context**: Knows about Sankey diagram settings
- **Data Selection**: Can detect selected table rows or chart elements

### 💬 Smart Chat Interface
- **Floating Widget**: Always accessible chat button in bottom-right corner
- **Context Display**: Shows current page context in the chat panel
- **Message History**: Maintains conversation history within the session
- **Source Citations**: Provides document sources for answers

### 🔧 Technical Features
- **Client-Side RAG**: Runs entirely in the browser using JavaScript
- **OpenRouter Integration**: Direct API calls to OpenRouter for LLM responses
- **Context Enhancement**: Enhances search queries with page context
- **Responsive Design**: Works on desktop and mobile devices
- **Minimizable**: Can be minimized to save screen space
- **No Server Required**: Works on GitHub Pages and static hosting

## Implementation

### Files Added/Modified

1. **`docs/rocket-chat-widget.js`** - Main widget JavaScript file with OpenRouter integration
2. **`docs/client-rag.js`** - Client-side RAG implementation
3. **`src/chat_api.py`** - Updated to handle context-aware requests (optional, for local dev)
4. **All HTML pages** - Updated to include the widget and RAG system

### Context Detection

The widget automatically detects:

- **Page Type**: Dashboard, data browser, chat interface, etc.
- **Active Filters**: Branch, category, search terms on browse page
- **Visualization Settings**: Fiscal year, minimum amount, flow type
- **Selected Data**: Table rows, chart elements (when available)

### Client-Side RAG Integration

The widget uses client-side RAG to search through document embeddings:

1. **Load Embeddings**: Loads pre-computed embeddings from `data/embeddings/`
2. **Search Documents**: Uses cosine similarity to find relevant document chunks
3. **OpenRouter API**: Sends enhanced queries with context to OpenRouter
4. **Context-Aware Responses**: Provides responses based on page context and document content

### Required Data Files

The widget requires these files to be present in the `data/embeddings/` directory:
- `chunks.json` - Document chunks with metadata
- `embeddings.npy` - Pre-computed embeddings (numpy format)

## Usage

### Using the Widget

1. **Open any page** in your browser:
   - **GitHub Actions Deployment**: `https://syzygyx.github.io/DD1414/`
   - **Local development**: `http://localhost:5000/` (with `python src/chat_api.py`)

2. **No API Key Required**:
   - The widget uses GitHub Secrets for the OpenRouter API key
   - No user input required - fully automated
   - Secure server-side API key management

3. **Click the chat button** (💬) in the bottom-right corner

4. **Ask questions** about the budget data!

### Using the Chat

1. **Ask questions** about the data you're viewing
2. **Get context-aware answers** based on your current page
3. **View source citations** for document references
4. **Minimize/close** the chat as needed

### Example Interactions

**On Dashboard Page**:
- "What's the processing status?"
- "How many files have been processed?"
- "Show me recent activity"

**On Browse Page (with Army filter)**:
- "What Army budget data is available?"
- "Tell me about Operation and Maintenance funding"
- "What are the largest Army programs?"

**On Sankey Page (FY 2025)**:
- "What does this visualization show?"
- "Which branch has the most funding?"
- "Explain the budget flow"

## Testing

Run the test script to verify everything is working:

```bash
python test_rocket_chat.py
```

This will test:
- Widget file presence and format
- API connectivity and context handling
- Chat functionality with different contexts

## Customization

### Styling
The widget styles are defined in `rocket-chat-widget.js`. You can modify:
- Colors and gradients
- Size and positioning
- Animation effects
- Mobile responsiveness

### Context Detection
Add new context detection by modifying the `detectContext()` method in the widget.

### API Responses
Customize the chat responses by modifying the system prompt in `chat_api.py`.

## Troubleshooting

### Widget Not Appearing
- Check that `rocket-chat-widget.js` is loaded
- Verify no JavaScript errors in browser console
- Ensure the widget is not blocked by other elements

### API Not Responding
- Verify the API server is running: `python src/chat_api.py`
- Check API logs for errors
- Ensure OpenRouter API key is set

### Context Not Detected
- Check that page elements exist (filters, controls)
- Verify context detection logic in widget
- Test with browser developer tools

## Future Enhancements

- **Real-time Updates**: Update context when filters change
- **Chart Integration**: Better Plotly selection detection
- **User Preferences**: Remember chat settings
- **Multi-language Support**: Internationalization
- **Advanced Context**: More sophisticated context detection

## Support

For issues or questions:
1. Check the test script output
2. Review browser console for errors
3. Verify API server logs
4. Test with different page contexts