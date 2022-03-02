
'''
Dependencies
'''
import os
import json
import time
import logging
import requests
import utils
import video

from queue import Queue
from decouple import config
from threading import Thread
from flask_cors import CORS
from flask import Flask, request, jsonify, Response


'''
    Logging
'''
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
    Daemon avatar background threaded creation process
'''
def avatar_daemon(payload):
    if payload is None:
        return False
    sleep_time = 15

    logging.debug("[avatar] [step 1/9] creating synthesia video")
    synthesia_result = video.create_video_on_synthesia(payload["script_text"], payload["avatar"], payload["voice"], payload["test"])
    logging.debug(synthesia_result)
    if(synthesia_result['status'] == "error"):
        return synthesia_result
    synthesia_id = synthesia_result["synthesia_id"]

    time.sleep(sleep_time)
    logging.debug("[avatar] [step 2/9] pull synthesia video")
    loop = True
    while loop:
        get_video_res = video.get_video_from_synthesia(synthesia_id)
        syn_json_resp = json.loads(get_video_res.text)
        if( syn_json_resp["status"] == 'complete' ):
            r = requests.get(syn_json_resp["download"], allow_redirects=True)
            open(config("DOWNLOAD_DIR")+"/syn_"+payload["avatar_video_id"]+".mp4", 'wb').write(r.content)
            loop = False
        if( syn_json_resp["status"] == 'in_progress' ):
            logging.debug(f'[avatar] [step 2/9] sleeping {sleep_time}s')
            time.sleep(sleep_time)

        if( not syn_json_resp["status"] == 'in_progress' and not syn_json_resp["status"] == 'complete'):
            loop = False
            logging.debug("[avatar] [step 2/9] unkown status: "+syn_json_resp["status"])

    logging.debug("[avatar] [step 3/9] cropping video")
    try:
        crop_res = video.crop_video(payload["avatar_video_id"])
        logging.debug(crop_res)
    except:
        logging.info("[avatar] [step 3/9] error while cropping video")
        return

    logging.debug("[avatar] Step 4/9 | Add background")
    try:
        bg_res = video.add_bg_color(payload["avatar_video_id"], "#add8e6")
        logging.debug(bg_res)
    except:
        logging.info("[avatar] [step 4/9] error while adding background")
        return
    
    logging.debug("[avatar] Step 5/9 | Enhace Video")
    try:
        enhace_res = video.enhhace_video(payload["avatar_video_id"])
        logging.debug(enhace_res)
    except:
        logging.info("[avatar] [step 5/9] error while enhancing video")
        return

    logging.debug("[avatar] Step 6/9 | Add Overlay")
    try:
        overlay_res = video.adding_overlay(payload["avatar_video_id"], payload["overlay_image"])
        logging.debug(overlay_res)
    except:
        logging.info("[avatar] [step 6/9] error while adding overlay")
        return
    
    logging.debug("[avatar] Step 7/9 | Convert to WebM")
    try:
        overlay_res = video.convert_to_webm(payload["avatar_video_id"])
        logging.debug(overlay_res)
    except:
        logging.info("[avatar] [step 7/9] error while adding overlay")
        return

    logging.debug("[avatar] Step 8/9 | Add Title")
    try:
        overlay_res = video.add_title(payload["avatar_video_id"],payload["script_text"])
        logging.debug(overlay_res)
    except:
        logging.info("[avatar] [step 8/9] error while cropping video")
        return
                
    logging.debug("[avatar] Step 9/9 | Callback / Move video to folder")
    try:
        pushing_res = video.push_video_to_callback(payload["hook_url"])
        logging.debug(pushing_res)
    except:
        logging.info("[avatar] [step 9/9] error pushing back the video")
        return

    logging.debug("[avatar] Process finished")


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
    if( not utils.token_is_valid(request.headers) == True ):
        return {"status_code":"404", "status":"error", "msg": "Invalid token"}
    logging.debug(request)

    avatar_video_id = utils.gen_uniq_video_id()
    logging.debug(f'Avatar video id: {avatar_video_id}')

    try:
        json_request    = request.json
        payload = {
            "avatar_video_id": avatar_video_id, 
            "avatar": json_request['avatar'], 
            "voice": json_request['voice'], 
            "script_text": json_request["script_text"], 
            "background": json_request['background_color'], 
            "overlay_image": json_request['overlay_image'],
            "hook_url": json_request['hook_url'],
        }
    except:
        return {"status_code":"404", "status":"error", "msg": "Missing parameters"}

    try:
        if( json_request["test"] ):
            payload["test"] = "true"
        else:
            payload["test"] = "false"
    except:
        payload["test"] = "false"

    logging.debug(f"Payload: {payload}")
    thread = Thread(target=avatar_daemon, args=(payload,))
    thread.daemon = True
    thread.start()

    return Response(
        mimetype='application/json',
        status=200, 
        response = json.dumps({"avatar_id": avatar_video_id}),
    )

'''
    Get avatar status
'''
@app.route("/avatar/<string:avatar_video_id>", methods = ['GET'])
def get_avatar(avatar_video_id):
    token_status = utils.token_is_valid(request.headers)
    if( not token_status == True ):
        return token_status
    return utils.get_last_avatar_status(avatar_video_id)

'''
    Download avatar video
'''
@app.route("/avatar/download/<string:avatar_video_id>", methods = ['GET'])
def download_avatar(avatar_video_id):
    token_status = utils.token_is_valid(request.headers)
    if( not token_status == True ):
        return token_status
    cmd = f'ls {config("AVATARS_DIR")}/{avatar_video_id}.mp4'
    avatar_video_is_ready = False
    if( avatar_video_is_ready ):
        return {"video":"mp4"}
    return {"status":"not ready yet"}

'''
    Validate token endpoint
'''
@app.route("/tokenisvalid", methods = ['GET'])
def token_validation():
    token_status = utils.token_is_valid(request.headers)
    logging.debug(token_status)
    if( not token_status == True ):
        return token_status
    return "Token is valid"

'''
    ping / index endpoint (service is up)
'''
@app.route("/", methods = ['GET'])
@app.route("/ping", methods = ['GET'])
def ping():
    return "pong"


'''
    Main
'''
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
