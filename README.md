
# AVATAR API

This api creates a custom avatar taking a script text, background color and overlay image from a json request.

<br />

## **3rd party dependencies**

To use this api you need the following

### **A Synthesia API KEY**

https://docs.synthesia.io/docs  

### **Enhace AI**
Install a licenced Topaz Labs LLC Video Enhace AI program  
https://www.topazlabs.com/video-enhance-ai  


### **ffmpeg**
- Download: https://www.gyan.dev/ffmpeg/builds/ffmpeg-git-full.7z
- unzip to:  C:\ffmpeg
- System properties -> Advanced tab -> Enviroment Variables
- Select Path variable, then Edit button
- Add new entry to: C:\ffmpeg\bin
- click Ok
- click Ok

<br />
<br />

# Install python3 on windows
- Download https://python.org/downloads/realease/python-3102/
- Download https://www.python.org/ftp/python/3.10.2/python-3.10.2-amd64.exe

1 run python installer
2 check add Python to Path
3 install now

## AVATAR API installation
> app_init.sh 


<br/>

## **Vocinity API token HTTP header**
|Header|Value|
|:---|:---|
|x-vocinity-token|string|

<br />
<br />

# API endpoints
This is a list for available API endpoints
- **POST /avatar**  <i>create a new avatar</i>
- **GET /avatar/:avatar_id** <i>get avatar status</i>
- **GET /avatar/download/:avatar_id** <i>download avatar video</i>
- **GET /tokenisvalid** <i>just check if X-Vocinity token is valid </i>
- **GET /ping** <i>send pong back</i>
- **GET /** <i>send pong back</i>

<br/>

## **Create avatar**

|Parameter|Description|
|:---|:---|
|avatar|Synthesia avatar id|
|voice|Synthesia voice id|
|background_color| avatar background color (hexadecimal)|
|overlay_image|file name / image url (valid formats jpg, png) in 608 x 1080 pixels|
|script_text| text message for avatar speak|
|hook_url| url where avatar video will be sent when creation process finish|
|test| values \[true\|false\] if true watermark is showed on avatar video, any charge applied|

## **Example:**
> curl -H "X-Vocinity-Token: secure_token" http://windows-gpu1:8080/avatar \
> { \
	"avatar": "anna_costume1_cameraA", \
	"voice":"18625cf6-e9ac-4680-931a-7efdac4a1a25", \
	"background_color": "#add822", \
	"overlay_image": "https://cdn.wallpapersafari.com/32/44/tLDHdw.jpg", \
	"script_text": "Tech No logic, Daft Punk", \
	"hook_url":"http://{your_api_ip}:8085/avatar", \
	"test": false \
}

<br/>
<br/>


## **Download video avatar Example:**

> curl -H "X-Vocinity-Token: secure_token"  "http://windows-gpu1:8080/avatar/download/a3TUbzDHT9cJ62Ge4jrk" --output video.webm

<br/>
<br/>

# References
- https://ffmpeg.org/download.html
- https://www.gyan.dev/ffmpeg/builds/


<br/>
<br/>

# Features
- avatar
- backgroundColor
- backgroundImage
- overlayImage

<br/>
<br/>

# Additional Documentation
- Synthesia: https://docs.synthesia.io/docs

<br/>
<br/>

# Color reference
- add8e6	Vocinity blue
- 2fc98b	Chrome key green