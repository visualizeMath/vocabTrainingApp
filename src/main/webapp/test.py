import requests

url = "https://twinword-twinword-bundle-v1.p.rapidapi.com/word_example/"

querystring = {"entry":"relative"}

headers = {
	"X-RapidAPI-Key": "2ce7b1c229mshc7c6cce18b2206bp18be91jsnc2aa55607b11",
	"X-RapidAPI-Host": "twinword-twinword-bundle-v1.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())