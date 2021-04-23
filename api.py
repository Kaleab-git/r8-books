import requests
isbn = '0446679097'
def search_api(isbn):
    url = f"https://www.googleapis.com/books/v1/volumes/zyTCAlFPjgYC?key=AIzaSyAyNQ4uim767INfNoBLkYUspa2ioxbAJCY"
    results = requests.get(url=url)
    return results
print (search_api(isbn))