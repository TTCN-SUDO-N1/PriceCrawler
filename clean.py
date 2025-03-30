def cleanUrl(url):
    
    urlnew=url.replace("https://", "").replace("/", "_").replace(":", "_").replace("?", "_").replace(".", "_")

    return urlnew