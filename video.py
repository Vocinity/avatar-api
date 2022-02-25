import logging
import json
import requests
import subprocess
import datetime
import utils
from decouple import config

'''
    Step1 Create video on synthesia
'''
def create_video_on_synthesia(text,avatar,voice):
    request_headers = {
        'Authorization' : config("SYNTHESIA_TOKEN"),
        'Content-Type': 'application/json'
    }
    request_data = {
        'test': "true", 
        'input': [
            {
                "scriptText": text, 
                "avatar": avatar,
                "background": "green_screen",
                "avatarSettings": {
                    "voice": voice,
                    "style": "rectangular",
                },                
            }
        ]
    }
    logging.debug(request_data)
    logging.debug(request_headers)
    try:
        resp = requests.post( config("SYNTHESIA_URI"), headers=request_headers, json=request_data )
        logging.debug(resp)
    except:
        return {"status": "error", "msg": "Synthesia request error"}
    
    if( resp.status_code == 201):
        logging.debug(resp.text)
        syn_json_resp = json.loads(resp.text)
        logging.debug(syn_json_resp)    
    else:
        return {"status": "error", "msg": "Synthesia response error: "+str(resp.text)}
    return {"status":"ok", "synthesia_id": syn_json_resp["id"], "synthesia_status": syn_json_resp["status"] }


'''
Step2 Pull video from synthesia
'''
def get_video_from_synthesia(synthesia_id):
    request_headers = { 'Authorization' : config("SYNTHESIA_TOKEN") }
    resp = requests.get(
        f'{config("SYNTHESIA_URI")}/{synthesia_id}',
        headers=request_headers,
    )
    return resp


'''
Step3 Crop video
'''
def crop_video(avatar_video_id):
    cmd = (f'ffmpeg -i {config("DOWNLOAD_DIR")}/syn_{avatar_video_id}.mp4 -filter:v crop=608:1080:656:0 {config("TMP_DIR")}/step3_{avatar_video_id}.mp4').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step4 Add background
'''
def add_bg_color(avatar_video_id, color):
    #blue  color=0xadd8e6
    #green color chroma =0x2fc98b
    color = utils.background_color_validation(color)
    #cmd = (f'ffmpeg -i {config("TMP_DIR")}/step3_{avatar_video_id}.mp4 -i {config("OVERLAYS_DIR"]}/background.png -f lavfi -i color=0xadd8e6:s=608x1080 -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {config("TMP_DIR")}/step4_{avatar_video_id}.mp4').split()
    cmd = (f'ffmpeg -i {config("TMP_DIR")}/step3_{avatar_video_id}.mp4 -i {config("OVERLAYS_DIR")}/background.png -f lavfi -i color=0x{color}:s=608x1080 -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {config("TMP_DIR")}/step4_{avatar_video_id}.mp4').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step5 Enhace Video
'''
def enhhace_video(avatar_video_id):
    cmd = (f'{config("TOPAZ_AI_DIR")}veai.exe -i {config("TMP_DIR")}/step4_{avatar_video_id}.mp4 -m alq-12 -f mp4 --width:height 608:1080 --output {config("TMP_DIR")}/step5_{avatar_video_id}.mp4').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step6 Add Overley
'''
def adding_overlay(avatar_video_id, overlay_image):
    image = utils.get_overlay_image(overlay_image)
    cmd = (f'ffmpeg -i {config("TMP_DIR")}/step5_{avatar_video_id}.mp4 -i {image} -filter_complex [0:v]colorkey=0x2fc98b:0.01:0.5[ckout];[1:v][ckout]overlay[despill];[despill]despill=green[colorspace];[colorspace]format=yuv420p[out] -map [out] -map 0:a:0 {config("TMP_DIR")}/step6_{avatar_video_id}.mp4').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step7 Convert to WebM
'''
def convert_to_webm(avatar_video_id):
    cmd = (f'ffmpeg -i {config("TMP_DIR")}/step6_{avatar_video_id}.mp4 -c:v libvpx -quality best -auto-alt-ref 0 -g 24 -qmin 0 -qmax 12 -crf 5 -b:v 2M -bufsize 6000 -rc_init_occupancy 200 -threads 7 -acodec opus -strict -2 {config("TMP_DIR")}/step7_{avatar_video_id}.webm').split()
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step8 Add Title
'''
def add_title(avatar_video_id, title_txt):
    cmd = [
        "ffmpeg", 
        "-i", f"{config('TMP_DIR')}/step7_{avatar_video_id}.webm",
        "-metadata", f"title={utils.text_cleaner(title_txt)}",
        "-metadata", f"description={title_txt}",
        "-metadata", f"comments='hash {utils.text_hash(title_txt)}'",
        "-metadata", f"artist={config('VIDEO_META_ARTIST')}",
        "-metadata", f"album={config('VIDEO_META_ALBUM')}",
        "-metadata", f"year={datetime.datetime.now().year}",
        "-codec", "copy", f'{config("AVATARS_DIR")}/avatar_{avatar_video_id}.webm'
    ]
    logging.debug(cmd)
    return subprocess.run(cmd,stdout=subprocess.PIPE)

'''
Step9 Push video to CallBack API
'''
def push_video_to_callback(url):
    if( not utils.hook_url_validation(url) ):
        logging.debug(f"invalid callback url: {url}")
        return False
    logging.debug(f"pushing video to callback uri: {url} (comming soon)")
    #utils.push_video_to_callback
    return True
