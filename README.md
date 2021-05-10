



Instructions: 

    python3 basic.py

Prep (if you want venv goodness):

    python3 -m venv dmslave-env # may need to use just python if you're on Winblow$
    source dmslave-env/bin/activate
    pip install -r requirements.txt


Example usage: 

    (dmslave-env) 5e-dm-assistant[main !?]$ pip install -r requirements.txt
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
    (dmslave-env) 5e-dm-assistant[main !?]$ 
