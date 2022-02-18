#!/usr/bin/python3
import sys
import requests

try:
    file = sys.argv[1]
except:
    print(f"Howto use:\n  {sys.argv[0]} video.mp4")
    file = False
if( not file ):
    quit()

upload_response = requests.post(
    'http://127.0.0.1:8085/avatar', 
    files = { 
        'file': open(file,'rb')
    }
)
print(f"Uploading file: "+file)
print(f"Upload response status: {upload_response}")
print(f"Upload response: {upload_response.json()}")