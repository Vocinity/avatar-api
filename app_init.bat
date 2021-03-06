:: Install Python Dependencies
pip3 install requests
pip3 install flask flask_cors
pip3 install python-decouple

:: Create app directories
mkdir C:\Vocinity\avatar-api\downloads
mkdir C:\Vocinity\avatar-api\videos_tmp
mkdir C:\Vocinity\avatar-api\avatars
mkdir C:\Vocinity\avatar-api\overlays

copy run_avatar_api.bat C:\Vocinity\avatar-api
copy server.py C:\Vocinity\avatar-api
copy utils.py C:\Vocinity\avatar-api
copy video.py C:\Vocinity\avatar-api\
copy overlays/* C:\Vocinity\avatar-api\overlays\
copy env.example C:\Vocinity\avatar-api\.env
copy avatar-api.ico C:\Vocinity\avatar-api\avatar-api.ico

:: Create Desktop simlynk  (run as superadmin is neeeded for this)
::copy avatar-api.lnk Desktop\