
'''
Dependencies
'''
import os
import json
import time
import random
import string
import logging
import requests
import subprocess

from queue import Queue
from decouple import config
from threading import Thread
from flask_cors import CORS
from flask import Flask, request, jsonify, Response

'''
    Config Vars
'''
valid_tokens = ['secure_token']
downloads='C:/Vocinity/avatar-api/downloads'
tmp='C:/Vocinity/avatar-api/videos_tmp'
avatars='C:/Vocinity/avatar-api/avatars'
overlays="C:/Vocinity/avatar-api/overlays"
topaz_ai_path="C:/Program Files/Topaz Labs LLC/Topaz Video Enhance AI/"
synthesia_uri = config("SYNTHESIA_URI")
synthesia_key = config("SYNTHESIA_TOKEN")

logging.basicConfig(
    level=config("LOG_LEVEL"),
    format="%(asctime)s %(levelname)s %(message)s",
)



'''
    Init flask app
'''
app = Flask(__name__)
app.secret_key = os.urandom(42)
CORS(app)



'''
    General functions
'''

'''
    Validate token
'''
def token_is_valid(request_headers):
    try:
        token = request_headers.get('X-Vocinity-Token')
        logging.debug(token)
    except:
        return "Token is missing"
    if( not token ):
        return 'Missing token'
    if( token == valid_tokens[0] ):
        return True
    return "Invalid token"
    

def gen_uniq_video_id():
    return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(20))

'''
    Step1 Create video on synthesia
'''
def create_video_on_synthesia(text,avatar,background):
    request_headers = {
        'Authorization' : synthesia_key,
        'Content-Type': 'application/json'
    }
    request_data = {
        'test': "true", 
        'input': [
            {
                "scriptText": text, 
                "avatar": avatar, 
                "background": background
            }
        ]
    }
    logging.debug(request_data)
    logging.debug(request_headers)
    try:
        resp = requests.post( synthesia_uri, headers=request_headers, json=request_data )
        logging.debug(resp)
    except:
        return {"status": "Synthesia request error"}
    
    if( resp.status_code == 201):
        logging.debug(resp.text)
        syn_json_resp = json.loads(resp.text)
        logging.debug(syn_json_resp)    
    else:
        return {"status": "Synthesia response error: "+str(resp.text)}
    return {"status":"ok", "synthesia_id": syn_json_resp["id"], "synthesia_status": syn_json_resp["status"] }


'''
Step2 Pull video from synthesia
'''
def get_video_from_synthesia(synthesia_id):
    request_headers = { 'Authorization' : synthesia_key }
    resp = requests.get(
        f"{synthesia_uri}/{synthesia_id}",
        headers=request_headers,
    )
    return resp


'''
Step3 Crop video
'''
def crop_video(avatar_video_id):
    cmd = (f'ffmpeg -i {downloads}/syn_{avatar_video_id}.mp4 -filter:v crop=608:1080:656:0 {tmp}/step3_{avatar_video_id}.mp4').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step4 Add background
'''
def add_bg_color(avatar_video_id):
    cmd = (f'ffmpeg -i {tmp}/step3_{avatar_video_id}.mp4 -i {overlays}/background.png -f lavfi -i color=0xadd8e6:s=608x1080 -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {tmp}/step4_{avatar_video_id}.mp4').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)


'''
Step5 Enhace Video
'''
def enhhace_video(avatar_video_id):
    cmd = (f"{topaz_ai_path}veai.exe -i {tmp}/step4_{avatar_video_id}.mp4 -m alq-12 -f mp4 --width:height 608:1080 --output {tmp}/step5_{avatar_video_id}.mp4").split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step6 Add Overley
'''
def adding_overlay(avatar_video_id, overlay_image):
    #cmd = f'ffmpeg -i {tmp}/step4_{avatar_video_id}.mp4 -i {overlays}/{overlay_image} -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {tmp}/step6_{avatar_video_id}.mp4'
    cmd = (f'ffmpeg -i {tmp}/step5_{avatar_video_id}.mp4 -i {overlays}/{overlay_image} -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {tmp}/step6_{avatar_video_id}.mp4').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)


'''
Step7 Convert to WebM
'''
def convert_to_webm(avatar_video_id):
    cmd = (f'ffmpeg -i {tmp}/step6_{avatar_video_id}.mp4 -c:v libvpx -quality best -auto-alt-ref 0 -g 24 -qmin 0 -qmax 12 -crf 5 -b:v 2M -bufsize 6000 -rc_init_occupancy 200 -threads 7 -acodec opus -strict -2 {tmp}/step7_{avatar_video_id}.webm').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step8 Add Title
'''
def add_title(avatar_video_id, title_txt):
    #cmd = f'ffmpeg -i {tmp}/step7_{avatar_video_id}.webm -metadata title="{title_txt}" -codec copy {avatars}/avatar_{avatar_video_id}.webm'
    #cmd = cmd.split()
    cmd = [
        "ffmpeg", 
        "-i", f"{tmp}/step7_{avatar_video_id}.webm",
        "-metadata", f"title={title_txt}",
        "-codec", "copy", f"{avatars}/avatar_{avatar_video_id}.webm"
    ]
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step9 Push video to CallBack API
'''
def push_video_to_callback(uri):
    logging.debug("pushing video to callback uri: "+uri)
    return True

'''
API REST Endpoints
'''
from flask import Flask, request
app = Flask(__name__)


'''
 Create a new avatar
'''
@app.route("/avatar", methods = ['POST'])
def create_avatar():
    if( not token_is_valid(request.headers) == True ):
        return {"status_code":"404", "status":"error", "msg": "Invalid token"}
    logging.debug(request)
    try:
        json_request = request.json
        text    = json_request["scriptText"]
        avatar  = json_request['avatar']
        bg      = json_request['background']
        overlay = json_request['overlayImage']
    except:
        return {"status_code":"404", "status":"error", "msg": "Missing parameters"}

    avatar_video_id = gen_uniq_video_id()
    logging.debug(f'Avatar video id: {avatar_video_id}')

    payload = {
        "avatar_video_id": avatar_video_id, 
        "text": text, 
        "avatar": avatar, 
        "bg": bg, 
        "overlay": overlay,
    }
    thread = Thread(target=avatar_daemon, args=(payload,))
    thread.daemon = True
    thread.start()

    return Response(
        mimetype='application/json',
        status=200, 
        response = json.dumps({"avatar_id": avatar_video_id}),
    )


'''
 Daemon avatar creation process
'''
def avatar_daemon(payload):
    if payload is None:
        return False
    sleep_time = 15

    #logging.debug(f"go to sleep {sleep_time}")
    #time.sleep(sleep_time)
    logging.debug(payload["avatar_video_id"]+" | "+payload["text"]+" | "+payload["avatar"]+" | "+payload["bg"])

    logging.debug("[avatar] [step 1/9] creating synthesia video")
    synthesia_result = create_video_on_synthesia(payload["text"], payload["avatar"], payload["bg"])
    logging.debug(synthesia_result)
    synthesia_id = synthesia_result["synthesia_id"]

    time.sleep(sleep_time)
    logging.debug("[avatar] [step 2/9] pull synthesia video")
    loop = True
    while loop:
        get_video_res = get_video_from_synthesia(synthesia_id)
        #logging.debug("-------------")
        #logging.debug(get_video_res)
        #logging.debug(get_video_res.text)
        syn_json_resp = json.loads(get_video_res.text)
        if( syn_json_resp["status"] == 'complete' ):
            r = requests.get(syn_json_resp["download"], allow_redirects=True)
            open(downloads+"/syn_"+payload["avatar_video_id"]+".mp4", 'wb').write(r.content)
            loop = False
        if( syn_json_resp["status"] == 'in_progress' ):
            logging.debug(f'[avatar] [step 2/9] sleeping {sleep_time}s')
            time.sleep(sleep_time)

        if( not syn_json_resp["status"] == 'in_progress' and not syn_json_resp["status"] == 'complete'):
            loop = False
            logging.debug("[avatar] [step 2/9] unkown status: "+syn_json_resp["status"])

    #logging.debug("-------------")
    logging.debug("[avatar] [step 3/9] cropping video")
    try:
        crop_res = crop_video(payload["avatar_video_id"])
        logging.debug(crop_res)
    except:
        logging.info("[avatar] [step 3/9] error while cropping video")
        return

    logging.debug("[avatar] Step 4/9 | Add background")
    try:
        bg_res = add_bg_color(payload["avatar_video_id"])
        logging.debug(bg_res)
    except:
        logging.info("[avatar] [step 4/9] error while adding background")
        return
    
    logging.debug("[avatar] Step 5/9 | Enhace Video")
    try:
        enhace_res = enhhace_video(payload["avatar_video_id"])
        logging.debug(enhace_res)
    except:
        logging.info("[avatar] [step 5/9] error while enhancing video")
        return

    logging.debug("[avatar] Step 6/9 | Add Overlay")
    try:
        overlay_res = adding_overlay(payload["avatar_video_id"], payload["overlay"])
        logging.debug(overlay_res)
    except:
        logging.info("[avatar] [step 6/9] error while adding overlay")
        return
    
    logging.debug("[avatar] Step 7/9 | Convert to WebM")
    try:
        overlay_res = convert_to_webm(payload["avatar_video_id"])
        logging.debug(overlay_res)
    except:
        logging.info("[avatar] [step 7/9] error while adding overlay")
        return

    logging.debug("[avatar] Step 8/9 | Add Title")
    try:
        overlay_res = add_title(payload["avatar_video_id"],payload["text"])
        logging.debug(overlay_res)
    except:
        logging.info("[avatar] [step 8/9] error while cropping video")
        return
                
    logging.debug("[avatar] Step 9/9 | Callback / Move video to folder")
    try:
        pushing_res = push_video_to_callback("")
        logging.debug(pushing_res)
    except:
        logging.info("[avatar] [step 9/9] error while cropping video")
        return

    logging.debug("[avatar] Process finished")


'''
 Get avatar status
'''
@app.route("/avatar/<string:avatar_video_id>", methods = ['GET'])
def get_avatar(avatar_video_id):
    token_status = token_is_valid(request.headers)
    if( not token_status == True ):
        return token_status
    cmd = f'ls {avatars}/{avatar_video_id}.mp4'
    avatar_exists = False
    if( avatar_exists ):
        return {"status":"ready", "msg": "Your avatar is ready", "avatar":"http://127.0.0.1:8080/avatars/{avatar_video_id}"}
    return {"status":"in progress", "msg": "Your avatar is not ready yet", "avatar":""}

'''
Download avatar video
'''
@app.route("/avatar/download/<string:avatar_video_id>", methods = ['GET'])
def download_avatar(avatar_video_id):
    token_status = token_is_valid(request.headers)
    if( not token_status == True ):
        return token_status
    cmd = f'ls {avatars}/{avatar_video_id}.mp4'
    avatar_video_is_ready = False
    if( avatar_video_is_ready ):
        return {"video":"mp4"}
    return {"status":"not ready yet"}


@app.route("/tokenisvalid", methods = ['GET'])
def token_validation():
    token_status = token_is_valid(request.headers)
    logging.debug(token_status)
    if( not token_status == True ):
        return token_status
    return "Token is valid"


@app.route("/", methods = ['GET'])
@app.route("/ping", methods = ['GET'])
def ping():
    return "pong"


'''
MAIN
'''
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
