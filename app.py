import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template
from langchain.llms import HuggingFaceHub


def get_pdf_texts(pdf_docs):
    '''
    Extratc Text from the PDFs
    '''
    text = ""
    for pdf in pdf_docs:
        #Creater PDF objects with pages; pages contains the text
        pdf_reader = PdfReader(pdf)
        #Loop through each page and extract the text and append it to text object
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(raw_text):
    '''
    Split the text into chunks of 1000 characters
    '''
    text_splitter = CharacterTextSplitter(
        separator = "\n",
        chunk_size = 1000,
        chunk_overlap=200,
        length_function = len
    )
    chunks = text_splitter.split_text(raw_text)
    return chunks

def get_vector_store(text_chunks):
    '''
    Generate Embedding for the text and store in the vector store.
    '''
    # OpenAI Embeddings
    embeddings = OpenAIEmbeddings()
    
    # Hugging Face Embeddings
    # embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")

    vector_store = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vector_store

def get_conversation_chain(vector_store):

    '''
    Retrieve the conversation chain from the vector store and store in memory
    '''
    # Open AI LLM
    llm = ChatOpenAI()

    # Huggingface LLM
    # llm = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature":0.5, "max_length":512})

    # HuggingFace Falcon 7b Instruct
    # llm = HuggingFaceHub(repo_id="tiiuae/falcon-7b-instruct", model_kwargs={"temperature":0.5})

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm = llm,
        retriever = vector_store.as_retriever(),
        memory = memory
    )
    return conversation_chain

def handle_user_input(user_question):
    '''
    Get the user input. It is going to be odd and bot response is going to be even. SO use the CSS for the same
    '''
    response = st.session_state.conversation({'question': user_question})
    st.session_state.chat_history = response['chat_history']

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)



def main():
    load_dotenv()
    st.set_page_config(page_title="Chat with your PDFs", page_icon=":books:")

    # CSS
    st.write(css, unsafe_allow_html=True)


    if "conversation" not in st.session_state:
        st.session_state.conversation= None

    if "chat_history" not in st.session_state:
        st.session_state.chat_history= None


    st.header("Chat about your PDFs :book:")

    user_question = st.text_input("Ask a Question about your document:")
    if user_question:
        handle_user_input(user_question)


    # # User and Bot template
    # st.write(user_template.replace("{{MSG}}", "Hello Bot"), unsafe_allow_html=True)
    # st.write(bot_template.replace("{{MSG}}", "Hello Human"), unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Your Documents")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on Process.", accept_multiple_files=True)
        
        if st.button("Process"):
            with st.spinner("Processing"):
                # Get PDF Text
                raw_text = get_pdf_texts(pdf_docs)

                # Get the Chunks
                text_chunks = get_text_chunks(raw_text)
                # st.write(text_chunks)

                # Create Vector store
                vector_store = get_vector_store(text_chunks)

                # Create conversation chain
                st.session_state.conversation = get_conversation_chain(vector_store)

# st.session_state.conversation


if __name__ == '__main__':
    main()
