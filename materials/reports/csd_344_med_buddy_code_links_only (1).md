CSD 344 – MedBuddy RAG Project
Code Links and Code Blocks Only

1. Streamlit Basic App Example
Source: https://docs.streamlit.io/library/get-started/create-an-app

```python
import streamlit as st

st.title("My First Streamlit App")
st.write("Hello, world!")
```

2. Streamlit File Uploader Example
Source: https://docs.streamlit.io/library/api-reference/widgets/st.file_uploader

```python
import streamlit as st

uploaded_file = st.file_uploader("Choose a file")
if uploaded_file is not None:
    st.write("Filename:", uploaded_file.name)
```

3. Python File Write Example
Source: https://docs.python.org/3/library/functions.html#open

```python
with open("example.txt", "wb") as f:
    f.write(b"Hello World")
```

4. Install Libraries Example
Source: https://pip.pypa.io/en/stable/cli/pip_install/

```bash
pip install streamlit
pip install llama-index
pip install google-generativeai
pip install pypdf
```

5. LlamaIndex Document Loader Example
Source: https://docs.llamaindex.ai/en/stable/examples/data_connectors/DocReader/

```python
from llama_index.core import SimpleDirectoryReader

documents = SimpleDirectoryReader("data").load_data()
```

6. LlamaIndex Vector Store Index Example
Source: https://docs.llamaindex.ai/en/stable/module_guides/indexing/vector_store_index/

```python
from llama_index.core import VectorStoreIndex

index = VectorStoreIndex.from_documents(documents)
```

7. Gemini Python SDK Example
Source: https://ai.google.dev/gemini-api/docs/python

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
model = genai.GenerativeModel("gemini-pro")
response = model.generate_content("Explain how AI works")
print(response.text)
```

8. LlamaIndex Query Engine Example
Source: https://docs.llamaindex.ai/en/stable/module_guides/querying/query_engine/

```python
query_engine = index.as_query_engine()
response = query_engine.query("What is AI?")
print(response)
```

9. Streamlit Text Input Example
Source: https://docs.streamlit.io/library/api-reference/widgets/st.text_input

```python
import streamlit as st

name = st.text_input("Enter your name")
if name:
    st.write("Hello", name)
```

