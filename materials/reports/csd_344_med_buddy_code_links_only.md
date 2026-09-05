CSD 344 

1. Streamlit Basic App
Source: https://docs.streamlit.io/library/get-started/create-an-app

```python
import streamlit as st
st.title("MedBuddy - Medical RAG Chatbot")
st.write("Upload a medical PDF and ask questions based only on the document.")
```

2. Streamlit File Uploader
Source: https://docs.streamlit.io/library/api-reference/widgets/st.file_uploader

```python
uploaded_file = st.file_uploader("Upload Medical Textbook (PDF)", type="pdf")
if uploaded_file is not None:
    st.success("PDF uploaded successfully")
```

3. Save Uploaded File
Source: https://docs.python.org/3/library/functions.html#open

```python
if uploaded_file is not None:
    with open("uploaded_book.pdf", "wb") as f:
        f.write(uploaded_file.read())
```

4. Install Required Libraries
Sources: https://docs.llamaindex.ai/ , https://ai.google.dev/gemini-api/docs

```bash
pip install streamlit
pip install llama-index
pip install google-generativeai
pip install pypdf
```

5. Load PDF Using LlamaIndex
Source: https://docs.llamaindex.ai/en/stable/examples/data_connectors/DocReader/

```python
from llama_index.core import SimpleDirectoryReader
loader = SimpleDirectoryReader(input_files=["uploaded_book.pdf"])
documents = loader.load_data()
```

6. Create Vector Store Index
Source: https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/

```python
from llama_index.core import VectorStoreIndex
index = VectorStoreIndex.from_documents(documents)
```

7. Configure Gemini API
Source: https://ai.google.dev/gemini-api/docs/python

```python
import google.generativeai as genai
genai.configure(api_key="YOUR_GEMINI_API_KEY")
model = genai.GenerativeModel("gemini-pro")
```

8. LlamaIndex Gemini Integration
Source: https://docs.llamaindex.ai/en/stable/module_guides/models/llms/

```python
from llama_index.llms.gemini import Gemini
llm = Gemini(model="models/gemini-pro", api_key="YOUR_GEMINI_API_KEY")
```

9. Create Query Engine
Source: https://docs.llamaindex.ai/en/stable/module_guides/querying/query_engine/

```python
query_engine = index.as_query_engine(llm=llm)
```

10. Question Input and Response
Source: https://docs.streamlit.io/library/api-reference/widgets/st.text_input

```python
user_question = st.text_input("Ask your medical question:")
if user_question:
    response = query_engine.query(user_question)
    st.write(response.response)
```

11. Strict Grounded Prompt

```python
strict_prompt = "Answer ONLY from the uploaded medical textbook. If answer not found, say 'Answer not available in the document.'"
response = query_engine.query(strict_prompt + user_question)
```

