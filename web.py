import streamlit as st
import main
import clean

st.title("Price Crawler")
url= st.text_input("Enter the URL of the product page:")

if st.button("Get Price"):
    st.write("Fetching price...")
    result = main.scrape(url)
    bodyContent = clean.extractBody(result)
    cleanedHtml = clean.cleanHtml(bodyContent)
    
    if result:
        urltxt = clean.cleanUrl(url)
        st.write("Fetched successfully!")
        st.write("HTML content saved to:", urltxt+".html")
        st.write("Download the HTML file:")
        with open(urltxt+".html", "r", encoding="utf-8") as f:
            html_content = f.read()
        st.download_button("Download HTML", html_content, file_name=urltxt+".html")
    else:
        st.write("Failed to fetch")
    
    st.session_state.html_content = cleanedHtml
    
    with st.expander("Show Cleaned HTML"):
        st.text_area("Cleaned HTML", cleanedHtml, height=300)
        