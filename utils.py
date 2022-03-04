import os
import re
import random
import base64
import logging
import string
import requests
from os.path import exists
from wsgiref import validate

from decouple import config

'''
    Global variables
'''
#allowed_image_formats = ['.jpg', '.png', '.bmp']
#valid_tokens = ['secure_token']


'''
    Validate API request token header
'''
def token_is_valid(request_headers):
    try:
        token = request_headers.get('X-Vocinity-Token')
        logging.debug(token)
    except:
        return "Token is missing"
    if( not token ):
        return 'Missing token'
    if token in config("VOCINITY_API_TOKENS"):
        return True
    return "Invalid token"
    
'''
    Generate Unique video id
'''
def gen_uniq_video_id():
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(20))

'''
   Validate hexadecimal background color
'''
def background_color_validation(color):
    if( re.match(r'^#(\d|\w){6}$', color)):
        pass
    elif( re.match(r'^(\d|\w){6}$', color)):
        color=f"#{color}"
    else:
        color=config("DEFAULT_BACKGROUND_COLOR")
    return color.replace(r"#","0x")

'''
   Validate if image format is allowed
'''
def allowed_image(url):
    for item in config("ALLOWED_IMAGE_FORMATS").split(','):
        if( re.search( item, url.lower() ) ):
            return True
    return False

'''
    If image is aun url, download it, if overlay exists on overlays_dir use it, otherwise return default overlay 
'''
def get_overlay_image(src_image):
    print(f'[get_overlay_image] start')
    if( not re.match("http", src_image) ):
        print(f'[get_overlay_image] is not a url')
        if( exists(f'{config("OVERLAYS_DIR")}/{src_image}') ):
            print(f'[get_overlay_image] image already exists, using it {config("OVERLAYS_DIR")}/{src_image}')
            return {config("OVERLAYS_DIR")}/{src_image}
        else:
            print(f'[get_overlay_image] image {src_image} doesnt exists, using default {config("OVERLAYS_DIR")}/{config("DEFAULT_OVERLAY")} ')
            return f'{config("OVERLAYS_DIR")}/{config("DEFAULT_OVERLAY")}'

    if( not allowed_image(src_image) ):
        print(f'[get_overlay_image] {src_image} invalid format')
        return f"{config('OVERLAYS_DIR')}/{config('DEFAULT_OVERLAY')}"
        
    image_name = re.search(r"(?!.*\/).+", src_image).group(0)
    print(f'[get_overlay_image] image name: {image_name}')
    r = requests.get(src_image, stream = True)
    logging.debug(f'[download overlay] Status code: {r.status_code}')
    if( r.status_code == 200 ):
        open(f'{config("DOWNLOAD_DIR")}/{image_name}', 'wb').write(r.content)
        logging.debug(f"[download overlay] Image downloaded: {config('DOWNLOAD_DIR')}/{image_name}")
        return f'{config("DOWNLOAD_DIR")}/{image_name}'
    else:
        logging.debug("[download overlay] Error downloading image")
    print(f'[get_overlay_image] using default image: {config("OVERLAYS_DIR")}/{config("DEFAULT_OVERLAY")}')
    return f'{config("OVERLAYS_DIR")}/{config("DEFAULT_OVERLAY")}'

'''
    Validate hook is a valid url format
'''
def hook_url_validation(hook_url):
    if( re.search(r'^(http:|https:)\/\/(\w+)\.(\w+)\/',hook_url) ):
        return True
    return False

'''
    Removing spaces, commas, punctuations etc from title text
'''
def text_cleaner(text):
    replace_chars = " ,;:\/'?!@#$%^&*(){}[]`+.><"
    for char in replace_chars:
        text = text.replace(char, "")
    return text

'''
    Hashing title text
'''
def text_hash(text):
    return str(abs(hash(text)))

'''
    file exists?
'''
def file_exits(file):
    return os.path.isfile(file)

'''
    get avatar / last avatar status
'''
def get_last_avatar_status(avatar_id):
    #path=config("AVATARS_DIR") 
    #file = f"avatar_{avatar_id}.webm"
    filename = f'{config("AVATARS_DIR")}/avatar_{avatar_id}.webm'
    if( file_exits(filename) ):
        logging.debug(f"File: {filename} exits")
        avatar=open(filename,"rb")
        logging.debug(avatar)
        b64 = base64.b64encode(avatar.read())
        return {"code": "200", "status":"Avatar is ready", "avatar":b64.decode('utf-8')}
    else: 
        logging.debug(f"File: {filename} doesnt exists")

    path = config("TMP_DIR") 
    file_name_pattern = f"step.*_{avatar_id}.*"
    try:
        tmp_videos = os.listdir(path)
        last_avatar_video = False
        for item in os.listdir(path):
            if ( re.match(file_name_pattern,item) ):
                last_avatar_video = item
        
        if( not last_avatar_video ):
            return {"code": "400", "status": f"Any video for this avatar_id {avatar_id}, not found"}    

        logging.debug(f"Last avatar status: {last_avatar_video} ")
        step = (re.search(r"^step([\d])_.*$", last_avatar_video)).group(1)
        logging.debug(step)
        mapping = {
            "3": "Cropping video",
            "4": "Adding background",
            "5": "Enhacing video",
            "6": "Adding overlay",
            "7": "Finishing avatar"
        }
        
        return {"code": "200", "status":mapping.get(step, "Cant find last status"), "avatar":""}
    except:
        pass
    return {"code": "401", "status": f"Any video for this avatar_id {avatar_id}, not found"}
