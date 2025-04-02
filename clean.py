from bs4 import BeautifulSoup

def cleanUrl(url):
    
    urlnew=url.replace("https://", "").replace("/", "_").replace(":", "_").replace("?", "_").replace(".", "_")

    return urlnew

def extractBody(html):
    soup = BeautifulSoup(html, 'html.parser')
    body_content= soup.body
    if body_content:
        return str(body_content)
    return ""



def cleanHtml(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    for script_or_style in soup(['script', 'style']):
        script_or_style.extract() 
    
    cleaned_html= soup.get_text(separator="/n")
    cleaned_html= "/n".join(
        [line.strip() for line in cleaned_html.splitlines() if line.strip()]
        )
    return cleaned_html

def splitHtml(html,max_length=5000):
    return [
        html[i:i + max_length] for i in range(0, len(html), max_length)
    ]