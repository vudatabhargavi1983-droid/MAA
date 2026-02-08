1. 📂 MODEL PATH (Where the files LIVE)
C:\Users\shahi\OneDrive\Documents\Mental_Health_App_Backend\models (Do not move them. The server reads from here.)

2. 🚀 ML SERVER COMMAND (Run this FIRST)
Path: C:\Users\shahi\OneDrive\Documents\Mental_Health_App_Backend\start_ml_server.bat

Command to run in Terminal:

powershell
cd ml_inference_server
venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
3. 🌐 BACKEND COMMAND (Run this SECOND)
Path: C:\Users\shahi\OneDrive\Documents\Mental_Health_App_Backend\manage.py

Command to run in Terminal:


powershell
python manage.py runserver

flutter build apk --release
& "C:\Users\shahi\AppData\Local\Android\Sdk\platform-tools\adb.exe" install -r "build\app\outputs\flutter-apk\app-release.apk"


python manage.py runserver 0.0.0.0:8000