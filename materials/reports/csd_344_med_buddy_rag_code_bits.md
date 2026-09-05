# CSD 344 Mini Project

# 2. Streamlit – Basic App Layout

Source:
https://docs.streamlit.io/library/get-started/create-an-app

```python
# Import streamlit library to create web app UI
import streamlit as st

# Set the title of the web application
st.title("MedBuddy - Medical RAG Chatbot")

# Display short description for KSERC requirement
st.write("Upload a medical PDF and ask questions based only on the document.")
```

---

# 3. File Upload (PDF Upload Section)

Source:
https://docs.streamlit.io/library/api-reference/widgets/st.file_uploader

```python
# Create a file uploader widget that accepts only PDF files
uploaded_file = st.file_uploader("Upload Medical Textbook (PDF)", type="pdf")

# Check whether user has uploaded a file
if uploaded_file is not None:
    
    # Display confirmation message
    st.success("PDF uploaded successfully")
```

---

# 4. Save Uploaded File Locally

Source:
https://docs.python.org/3/library/functions.html#open

```python
# If a file is uploaded
if uploaded_file is not None:

    # Open a file in write-binary mode
    with open("uploaded_book.pdf", "wb") as f:
        
        # Write uploaded file content into local file
        f.write(uploaded_file.read())
```

---

# 5. Install Required Libraries

Source:
https://docs.llamaindex.ai/
https://ai.google.dev/gemini-api/docs

```bash
# Install streamlit
pip install streamlit

# Install llamaindex
pip install llama-index

# Install Gemini SDK
pip install google-generativeai

# Install PDF reader
pip install pypdf
```

---

# 6. Load PDF Using LlamaIndex

Source:
https://docs.llamaindex.ai/en/stable/examples/data_connectors/DocReader/

```python
# Import SimpleDirectoryReader to read PDF documents
from llama_index.core import SimpleDirectoryReader

# Load the uploaded PDF file
# It reads and converts the PDF into document objects
loader = SimpleDirectoryReader(input_files=["uploaded_book.pdf"])

# Load documents from the file
documents = loader.load_data()
```

---

# 7. Create Vector Store Index (Core RAG Step)

Source:
https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/

```python
# Import VectorStoreIndex
from llama_index.core import VectorStoreIndex

# Create vector index from loaded documents
# This converts text into embeddings and stores for retrieval
index = VectorStoreIndex.from_documents(documents)
```

---

# 8. Configure Gemini LLM

Source:
https://ai.google.dev/gemini-api/docs/python

```python
# Import Gemini SDK
import google.generativeai as genai

# Configure Gemini API key
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Initialize Gemini model
model = genai.GenerativeModel("gemini-pro")
```

---

# 9. Connect Gemini with LlamaIndex

Source:
https://docs.llamaindex.ai/en/stable/module_guides/models/llms/

```python
# Import Gemini wrapper from llamaindex
from llama_index.llms.gemini import Gemini

# Create Gemini LLM instance
llm = Gemini(model="models/gemini-pro", api_key="YOUR_GEMINI_API_KEY")
```

---

# 10. Create Query Engine (RAG Retrieval + Generation)

Source:
https://docs.llamaindex.ai/en/stable/module_guides/querying/query_engine/

```python
# Create query engine using index and Gemini LLM
query_engine = index.as_query_engine(llm=llm)
```

---

# 11. User Question Input

Source:
https://docs.streamlit.io/library/api-reference/widgets/st.text_input

```python
# Create text input field for user question
user_question = st.text_input("Ask your medical question:")

# Check if user entered question
if user_question:
    
    # Send question to RAG system
    response = query_engine.query(user_question)
    
    # Display response
    st.write(response.response)
```

---

# 12. Strict Grounded Prompt (No Hallucination Control)

Concept Derived From Base Paper – Groundedness Section fileciteturn0file0

```python
# Create a system-level instruction to avoid hallucination
strict_prompt = "Answer ONLY from the uploaded medical textbook. If answer not found, say 'Answer not available in the document.'"

# Query using strict instruction
response = query_engine.query(strict_prompt + user_question)
```

---

# 13. Minimal UI Structure (KSERC Focused)

Only Required Sections:

1. Title
2. PDF Upload
3. Question Box
4. Answer Output

No:
- Chat history
- Themes
- Animations
- Metrics dashboard
- Fancy styling

---

# 14. RAG Flow (As per Paper Architecture)

Based on Methodology Section & Fig 1 Architecture fileciteturn0file0

Flow:

1. Upload PDF
2. Convert to text
3. Chunk text
4. Generate embeddings
5. Store in vector index
6. Retrieve relevant chunks
7. Send context + question to Gemini
8. Generate grounded answer
9. Display response

---

# 15. Final Notes

This file contains:
- Individual documented code bits
- Official source URLs
- Fully commented Python
- RAG architecture based on IEEE paper
- Gemini modification based on project brief
- Clean KSERC-focused UI

You will:
- Merge structure yourselves
- Maintain academic integrity
- Demonstrate working system

---

End of Document

