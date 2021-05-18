



Instructions:

    python3 basic.py

Code Prep:

0. Read this whole page.

1. Install [Git](https://bfy.tw/Qwym)

2. Install [Python](https://bfy.tw/Qwyq)

3. Open a Terminal (ctrl+alt+T on most Linux, cmd+space and search for Terminal on Mac, Winblow$... winkey+R, then enter cmd)

4. "Clone" the code to your local device

    git clone git@github.com:rjb25/5e-dm-assistant.git

5. Change Directory (`cd`) to the new directory created by the `git clone` operation:

    cd 5e-dm-assistant

Virtual Environment Prep (if you want [venv](https://bfy.tw/Qwyh) goodness):

    #LINUX
    python3 -m venv dm-env
    source dm-env/bin/activate
    pip install -r requirements.txt
    
    #WINDOWS
    py -m venv dm-env
    dm-env\Scripts\activate.bat
    pip install -r requirements.txt

You may see your command prompt change.

Note: Future instructions will include `source dm-env/bin/activate`, and assume
that you've already done this preparatory step. If you get a lot of errors,
try just deleting your -env folders and remaking the environment,
or ignoring the whole `venv` thing and any activation of it entirely.

Web App Instructions for using the functionality in `web_app.py`:

Step 1: Run the Web App in the background.

    source dm-env/bin/activate
    pip install -r requirements.txt
    python3 web_app.py

Step 2: Open a browser and visit the new page

[DM Assistant Web Page at http://127.0.0.1:8000/](http://127.0.0.1:8000/)

There, you can try entering updates and see them appear in the update log.

Example usage for the basic.py CLI:

    5e-dm-assistant[main !?]$ source dm-env/bin/activate
    (dm-env) 5e-dm-assistant[main !?]$ pip install -r requirements.txt
    Collecting requests==2.25.1
      Downloading requests-2.25.1-py2.py3-none-any.whl (61 kB)
         |████████████████████████████████| 61 kB 2.8 MB/s 
    Collecting urllib3<1.27,>=1.21.1
      Downloading urllib3-1.26.4-py2.py3-none-any.whl (153 kB)
         |████████████████████████████████| 153 kB 9.2 MB/s 
    Collecting idna<3,>=2.5
      Using cached idna-2.10-py2.py3-none-any.whl (58 kB)
    Collecting chardet<5,>=3.0.2
      Downloading chardet-4.0.0-py2.py3-none-any.whl (178 kB)
         |████████████████████████████████| 178 kB 33.1 MB/s 
    Collecting certifi>=2017.4.17
      Using cached certifi-2020.12.5-py2.py3-none-any.whl (147 kB)
    Installing collected packages: urllib3, idna, chardet, certifi, requests
    Successfully installed certifi-2020.12.5 chardet-4.0.0 idna-2.10 requests-2.25.1 urllib3-1.26.4
    (dm-env) 5e-dm-assistant[main !?]$ 

Example usage for the Web Application: 

    (dmslave-env) 5e-dm-assistant1[main !?]$ python web_app.py 
    2021-05-17 18:27:14,604 itty3 INFO itty3 1.1.1: Now serving requests at http://127.0.0.1:8000...
    2021-05-17 18:27:17,235 itty3 INFO "GET / HTTP/1.1" 200
    2021-05-17 18:27:28,366 itty3 INFO "POST /update_cmd/ HTTP/1.1" 302
    2021-05-17 18:27:28,569 itty3 INFO "GET / HTTP/1.1" 200
