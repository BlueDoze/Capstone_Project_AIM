import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from vector_db import initialize_vector_db, get_vector_db
from pdf_data_processor import process_custom_pdfs

load_dotenv()

# The 'templates' folder is the default for Flask, so we just need to tell it where the static files are.
app = Flask(__name__, static_folder='static')

# Initialize vector database
print("🚀 Initializing vector database...")
vector_db = initialize_vector_db()

# Clear existing vector database and populate with map.pdf data
print("🗑️ Clearing existing vector database...")
vector_db.clear_collection()

# Populate vector database with map.pdf data
print("📄 Populating vector database with map.pdf data...")
try:
    from pdf_data_processor import process_custom_pdfs
    
    # Process the map.pdf file specifically
    map_pdf_path = "images/map.pdf"
    if os.path.exists(map_pdf_path):
        pdf_data = process_custom_pdfs(
            pdf_paths=[map_pdf_path],
            descriptions=["Fanshawe College campus map with building layouts, corridors, and spatial relationships"],
            categories=["map"]
        )
        
        if pdf_data['embeddings']:
            vector_db.add_documents(
                documents=pdf_data['documents'],
                metadatas=pdf_data['metadatas'],
                ids=pdf_data['ids'],
                embeddings=pdf_data['embeddings']
            )
            print(f"✅ Vector database populated with {len(pdf_data['documents'])} map.pdf chunks")
        else:
            print("⚠️ No embeddings generated from map.pdf")
    else:
        print(f"❌ Map PDF not found at {map_pdf_path}")
except Exception as e:
    print(f"❌ Error populating map.pdf data: {e}")

# Configure the generative AI model
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise KeyError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
except KeyError as e:
    print(e)
    model = None

# Map information will now come from the vector database (map.pdf embeddings)

@app.route("/")
def index():
    # Use render_template to serve the HTML file from the 'templates' directory
    return render_template('index.html')

@app.route("/debug/vector-db")
def debug_vector_db():
    """Debug endpoint to check vector database status"""
    try:
        info = vector_db.get_collection_info()
        return jsonify({
            "status": "success",
            "vector_db_info": info,
            "message": "Vector database is working correctly"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Vector database error: {e}"
        }), 500

@app.route("/search/pdf", methods=['POST'])
def search_pdf():
    """Search PDF documents"""
    try:
        query = request.json.get("query", "")
        if not query:
            return jsonify({"error": "Please provide a search query"}), 400
        
        # Search for PDF documents
        results = vector_db.search(query, n_results=5)
        
        # Filter for PDF documents
        pdf_results = {
            'documents': [],
            'metadatas': [],
            'distances': [],
            'ids': []
        }
        
        for i, metadata in enumerate(results['metadatas']):
            if metadata.get('type') == 'pdf_text':
                pdf_results['documents'].append(results['documents'][i])
                pdf_results['metadatas'].append(metadata)
                pdf_results['distances'].append(results['distances'][i])
                pdf_results['ids'].append(results['ids'][i])
        
        return jsonify({
            "query": query,
            "results": pdf_results,
            "total_found": len(pdf_results['documents'])
        })
        
    except Exception as e:
        return jsonify({"error": f"PDF search failed: {e}"}), 500

@app.route("/chat", methods=['POST'])
def chat():
    if model is None:
        return jsonify({"reply": "The AI model is not configured. Please set the GEMINI_API_KEY environment variable."}), 500

    user_message = request.json.get("message")
    if not user_message:
        return jsonify({"reply": "Please provide a message."}), 400

    try:
        # Search for relevant map information using vector search
        print(f"🔍 Searching for relevant information for: {user_message}")
        search_results = vector_db.search(user_message, n_results=3)
        
        # Build context from search results
        context_parts = []
        if search_results['documents']:
            for i, doc in enumerate(search_results['documents']):
                context_parts.append(f"Relevant Information {i+1}: {doc}")
                print(f"📄 Found relevant info: {doc[:100]}...")
        
        # Create enhanced prompt with vector search results
        if context_parts:
            context = "\n\n".join(context_parts)
            prompt = f'''You are a campus navigator for Fanshawe College. Provide step-by-step walking directions based on the relevant information below.
Format your response using simple HTML tags for clarity. For example: use <strong> for emphasis, <ul> and <li> for lists, and <br> for line breaks.

RELEVANT CAMPUS INFORMATION:
{context}

User Question: {user_message}

Please provide helpful navigation assistance based on the relevant information above.'''
        else:
            # No relevant information found in vector database
            prompt = f'''You are a campus navigator for Fanshawe College. I don't have specific information about "{user_message}" in my campus map database.

User Question: {user_message}

Please let me know if you need help with navigation to specific buildings, facilities, or areas on the Fanshawe College campus, and I'll do my best to assist you based on the available map information.'''
            print("⚠️ No relevant information found in vector database")

        # Generate a response from the AI model
        response = model.generate_content(prompt)
        return jsonify({"reply": response.text})
        
    except Exception as e:
        print(f"Error generating content: {e}") # Added for debugging
        return jsonify({"reply": f"An error occurred: {e}"}), 500

def main():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

if __name__ == "__main__":
    main()
