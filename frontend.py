import streamlit as st  
import requests 
st.set_page_config(page_title="Text Corrector", layout="centered") 
st.title("AI Grammar & Spelling Corrector") 
text = st.text_area("Enter your paragraph below:", height=200) 
if st.button("Correct Text"): 
    if text.strip(): 
        try: 
            response = requests.post("http://localhost:5000/correct",json={"text": text}) 
            result = response.json() 
            if "corrected_text" in result: 
                st.subheader("Corrected Output:") 
                st.success(result["corrected_text"]) 
            else: 
                st.error(result.get("error", "Something went wrong.")) 
        except Exception as e: 
            st.error(f"Failed to connect to server: {e}") 
    else: 
        st.warning("Please enter some text.")