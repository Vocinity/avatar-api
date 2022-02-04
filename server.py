
'''
pip3 install requests
pip3 install flask flask_cors
pip3 install python-decouple
'''


'''
Dependencies
'''
import json
import time
import requests
import subprocess
from queue import Queue
from decouple import config
from threading import Thread
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

'''
Config Vars
'''
valid_tokens = ['secure_token']
downloads='C:/tmp_avatar_api/downloads'
tmp='C:/tmp_avatar_api/videos_tmp'
avatars='C:/tmp_avatar_api/avatars'
overlays="C:/tmp_avatar_api/overlays"
synthesia_uri = config("SYNTHESIA_URI")
synthesia_key = config("SYNTHESIA_TOKEN")


'''
Init
'''
app = Flask(__name__)
CORS(app)

'''
General functions
'''

'''
def token_is_valid(token):
    if( token == valid_tokens[0] ):
        return True
    return False
'''

def token_is_valid(request_headers):
    try:
        token = request_headers.get('X-Vocinity-Token')
        print(token)
    except:
        return "Token is missing"
    if( not token ):
        return 'Missing token'
    if( token == valid_tokens[0] ):
        return True
    return "Invalid token"
    

def gen_uniq_video_id():
    # todo. random uniq key to lable each video
    avatar_video_id = 'a1s2d3f4g5h6kj78l9'
    return avatar_video_id

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

    print(request_data)
    print(request_headers)

    resp = requests.post(
        synthesia_uri,
        headers=request_headers,
        json=request_data
    )
    print("6----------------------------------")
    syn_json_resp = json.loads(resp.text)
    print(syn_json_resp)
    #print(syn_json_resp["id"])
    #print(syn_json_resp["status"])
    
    return {"status":"ok", "synthesia_id": syn_json_resp["id"], "synthesia_status": syn_json_resp["status"] }

    '''
    print(response.id) # synthesia_id
    return response
    '''

'''
Step2 Pull video from synthesia
'''
def get_video_from_synthesia(synthesia_id):
    request_headers = { 'Authorization' : synthesia_key }
    resp = requests.get(
        f"{synthesia_uri}/{synthesia_id}",
        headers=request_headers,
    )
    #print(resp)
    return resp


'''
Step3 Crop video
'''
def crop_video(avatar_video_id):
    #cmd_rm = f"rm {downloads}/syn_{avatar_video_id}.mp4"
    #cmd_rm_result = subprocess.run(cmd_rm,stdout=subprocess.PIPE)
    cmd = f'ffmpeg -i {downloads}/syn_{avatar_video_id}.mp4 -filter:v crop=608:1080:656:0 {tmp}/step3_{avatar_video_id}.mp4'
    cmd = cmd.split()
    print(cmd)
    cmd_result = subprocess.run(cmd,stdout=subprocess.PIPE)
    #print(cmd_result)
    return cmd_result

'''
Step4 Add background
'''
def add_bg_color(avatar_video_id):
    cmd = f'ffmpeg -i {tmp}/step3_{avatar_video_id}.mp4 -i {overlays}/background.png -f lavfi -i color=0xadd8e6:s=608x1080 -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {tmp}/step4_{avatar_video_id}.mp4'
    cmd = cmd.split()
    print(cmd)
    cmd_result = subprocess.run(cmd,stdout=subprocess.PIPE)
    #print(cmd_result)
    return cmd_result


'''
Step5 Enhace Video
'''
def enhhace_video(avatar_video_id):
    cmd=f"veai.exe --input {tmp}/step4_{avatar_video_id}.mp4 -m alq-12 -f mp4 --output {tmp}/step5_{avatar_video_id}.mp4"
    cmd = cmd.split()
    print(cmd)
    cmd_result = subprocess.run(cmd,stdout=subprocess.PIPE)
    print(cmd_result)
    return cmd_result

'''
Step6 Add Overley
'''
def adding_overlay(avatar_video_id, overlay_image):
    cmd = f'ffmpeg -i {tmp}/step4_{avatar_video_id}.mp4 -i {overlays}/{overlay_image} -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {tmp}/step6_{avatar_video_id}.mp4'
    #cmd = f'ffmpeg -i {tmp}/step5_{avatar_video_id}.mp4 -i {overlays}/{overlay_image} -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {tmp}/step5_{avatar_video_id}.mp4'
    cmd = cmd.split()
    print(cmd)
    cmd_result = subprocess.run(cmd,stdout=subprocess.PIPE)
    print(cmd_result)
    return cmd_result


'''
Step7 Convert to WebM
'''
def convert_to_webm(avatar_video_id):
    cmd = f'ffmpeg -i {tmp}/step6_{avatar_video_id}.mp4 -c:v libvpx -quality best -auto-alt-ref 0 -g 24 -qmin 0 -qmax 12 -crf 5 -b:v 2M -bufsize 6000 -rc_init_occupancy 200 -threads 7 -acodec opus -strict -2 {tmp}/step7_{avatar_video_id}.webm'
    cmd = cmd.split()
    print(cmd)
    cmd_result = subprocess.run(cmd,stdout=subprocess.PIPE)
    print(cmd_result)
    return cmd_result

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
    print(cmd)
    cmd_result = subprocess.run(cmd,stdout=subprocess.PIPE)
    print(cmd_result)
    return cmd_result

'''
Step9 Push video to CallBack API
'''
def pusch_to_callback(uri):
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
    token_status = token_is_valid(request.headers)
    if( not token_status == True ):
        return token_status
    print(token_status)
    
    print(request)
    try:
        #json_request = json.loads(request.json)
        json_request = request.json
        text    = json_request["scriptText"]
        avatar  = json_request['avatar']
        bg      = json_request['background']
        overlay = json_request['overlayImage']
    except:
        return {"status_code":"404", "status":"error", "msg": "Missing parameters"}

    avatar_video_id = gen_uniq_video_id()
    print(f'Avatar video id: {avatar_video_id}')

    th1.start()
    payload = {
        "avatar_video_id": avatar_video_id, 
        "text": text, 
        "avatar": avatar, 
        "bg": bg, 
        "overlay": overlay,
    }
    mqueue.put(payload)

    return Response(
        mimetype='application/json',
        status=200, 
        #response = json.dumps(synthesia_result),
        response = json.dumps({"id": avatar_video_id}),
    )
    #return json_request
    #return create_result


'''
 Daemon avatar creation process
'''
def avatar_daemon(q, thread_id):
    while True: 
        payload = q.get()
        if payload is None:
            break
        sleep_time = 2
        print(f"go to sleep {sleep_time}")
        time.sleep(sleep_time)
        print(payload["avatar_video_id"]+" | "+payload["text"]+" | "+payload["avatar"]+" | "+payload["bg"])
        print("[daemon] Step 1/9 | Create synthesia video")
        synthesia_result = create_video_on_synthesia(payload["text"], payload["avatar"], payload["bg"])
        print(synthesia_result)
        synthesia_id = synthesia_result["synthesia_id"]
        time.sleep(15)
        print("[daemon] Step 2/9 | Pull synthesia video")
        loop = True
        while loop:
            get_video_res = get_video_from_synthesia(synthesia_id)
            print("-------------")
            print(get_video_res)
            print(get_video_res.text)
            syn_json_resp = json.loads(get_video_res.text)
            #dst_file = downloads+"/syn_"+synthesia_id+".mp4"
            dst_file = downloads+"/syn_"+payload["avatar_video_id"]+".mp4"
            if( syn_json_resp["status"] == 'complete' ):
                r = requests.get(syn_json_resp["download"], allow_redirects=True)
                open(dst_file, 'wb').write(r.content)
                loop = False
            if( syn_json_resp["status"] == 'in_progress' ):
                print('Sleeping 15s')
                time.sleep(15)

            if( not syn_json_resp["status"] == 'in_progress' and not syn_json_resp["status"] == 'complete'):
                loop = False
                print("Unkown status: "+syn_json_resp["status"])


            #{"createdAt":1641340208,"id":"871c7a6e-72a3-400d-bf2e-57440c7aeb93","lastUpdatedAt":1641340208,"status":"in_progress","visibility":"private"}
        print("-------------")
        print("[daemon] Step 3/9 | Crop video")
        crop_res = crop_video(payload["avatar_video_id"])
        print(crop_res)
        print("[daemon] Step 4/9 | Add background")
        bg_res = add_bg_color(payload["avatar_video_id"])
        print(bg_res)
        print("[daemon] Step 5/9 | Enhace Video")
        print("[daemon] Step 6/9 | Add Overlay")
        overlay_res = adding_overlay(payload["avatar_video_id"], payload["overlay"])
        print(overlay_res)
        print("[daemon] Step 7/9 | Convert to WebM")
        overlay_res = convert_to_webm(payload["avatar_video_id"])
        print(overlay_res)
        print("[daemon] Step 8/9 | Add Title")
        overlay_res = add_title(payload["avatar_video_id"],payload["text"])
        print(overlay_res)
        print("[daemon] Step 9/9 | Callback / Move video to folder")
        print("[daemon] Process finished")


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


'''
@app.route("/tokenisvalid", methods = ['GET'])
def token_is_valid():
    try:
        token = request.headers.get('X-Vocinity-Token')
        if( not token_is_valid(token) ):
            return "Invalid token"
    except:
        return "Token is missing"
    return "Token is valid"
'''

@app.route("/tokenisvalid", methods = ['GET'])
def token_validation():
    token_status = token_is_valid(request.headers)
    print(token_status)
    if( not token_status == True ):
        return token_status
    return "Token is valid"



    #return "Error, invalid or empty token"

@app.route("/", methods = ['GET'])
@app.route("/ping", methods = ['GET'])
def ping():
    return "pong"


'''
MAIN
'''
if __name__ == "__main__":
    mqueue = Queue(5)
    th1 = Thread( target=avatar_daemon, args=(mqueue, 1) )
    app.run(host='0.0.0.0', port=8080, debug=True)


#'''
#install vscode
#install python3 desde vscode (microsoft store)
#PS C:\Users\user\Documents\PythonScripts> python3.exe .\get-pip.py
#PS C:\Users\user\Documents\PythonScripts> python.exe -m pip install --upgrade pip
#PS C:\Users\user\Documents\PythonScripts> pip3.exe install flask
#'''


'''
import subprocess
res = subprocess.run(["ffmpeg", "-version"])
print(res)


# test01 ping alive
curl http://127.0.0.1:8080/ping


# test02 Valid token header
curl http://127.0.0.1:8080/tokenisvalid -H "X-Vocinity-Token: secure_token"


# test3 create a new avatar
curl http://127.0.0.1:8080/avatar -X POST -d '{"scriptText": "You have a friend on me", "avatar": "anna_costume1_cameraA", "background": "green_screen", "overlayImage": "vocinity.png"}' -H "X-Vocinity-Token: secure_token" -H "Content-Type: application/json"
{
  "avatar": "anna_costume1_cameraA", 
  "background": "green_screen", 
  "overlayImage": "vocinity.png", 
  "scriptText": "You have a friend on me"
}

# test4 validate if avatar is ready
curl http://127.0.0.1:8080/avatar/1234556767 -H "X-Vocinity-Token: secure_token"
{
  "avatar": "", 
  "msg": "Your avatar is not ready yet", 
  "status": "in progress"
}

'''