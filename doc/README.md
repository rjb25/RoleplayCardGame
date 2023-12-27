# README.dm

## TL;DR Instructions:

    python3 basic.py

## Code Prep:

0. Read this whole page.

1. Install [Git](https://bfy.tw/Qwym)

2. Install [Python](https://bfy.tw/Qwyq)

3. Open a Terminal (ctrl+alt+T on most Linux, cmd+space and search for Terminal on Mac, Winblow$... winkey+R, then enter cmd)

4. "Clone" the code to your local device

    git clone git@github.com:rjb25/5e-dm-assistant.git

5. Change Directory (`cd`) to the new directory created by the `git clone` operation:

    cd 5e-dm-assistant

6. Virtual Environment Prep (if you want [venv](https://bfy.tw/Qwyh) goodness):

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

## CLI Instructions

To run the app interactively in a terminal, just invoke it through that terminal.

    python3 basic.py

You'll then get prompted for a command, and shown the characters in play.

## Web App Instructions

These are the Web App Instructions for using the functionality in `web_app.py`.

Step 1: Run the Web App in the background.

    source dm-env/bin/activate
    pip install -r requirements.txt
    python3 web_app.py

NOTE: You can also run it with the following `gunicorn`
invocation: 

    source dm-env/bin/activate
    pip install -r requirements.txt
    gunicorn -w 1 -t 0 --reload web_app:dmapp

You might not get all of the logs, though. Not sure why.

Step 2: Open a browser and visit the new page

[DM Assistant Web Page at http://127.0.0.1:8000/](http://127.0.0.1:8000/)

There, you can try entering updates and see them appear in the update log.

NOTE: You can also run it from `ngrok`:

    ngrok http 8000

If successful, it will display a URL like 
`https://8feeb7deadff.ngrok.io` that anybody
can visit. If you want it less stupid-looking
you can pay for an account. Worth it if
it helps you impress people who can pay you, I
guess.

But before you do that, you have to download ngrok, 
sign up at ngrok.com, and get a free auth token.

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

    5e-dm-assistant[main !?]$ source dm-env/bin/activate
    (dm-env) 5e-dm-assistant1[develop-nathan !?]$ python3 web_app.py 
    2021-05-18 00:50:30,958 itty3 INFO itty3 1.1.1: Now serving requests at http://127.0.0.1:8000...
    initiative name type hp/max_hp
    22 giant-rat giant-rat 3/3
    16 rat rat 1/1
    12 sahuagin#1 sahuagin 11/11
    9 goblin goblin 9/9
    3 druid druid 23/23
    2021-05-18 00:50:34,180 itty3 INFO ['22 giant-rat giant-rat 3/3', '16 rat rat 1/1', '12 sahuagin#1 sahuagin 11/11', '9 goblin goblin 9/9', '3 druid druid 23/23']
    2021-05-18 00:50:34,181 itty3 INFO <li>22 giant-rat giant-rat 3/3</li><li>16 rat rat 1/1</li><li>12 sahuagin#1 sahuagin 11/11</li><li>9 goblin goblin 9/9</li><li>3 druid druid 23/23</li>
    2021-05-18 00:50:34,181 itty3 INFO "GET / HTTP/1.1" 200
    2021-05-18 01:02:01,021 itty3 INFO Command List is as follows: action giant-rat Bite goblin
    1d20
    1d4+2
    2021-05-18 01:02:01,021 itty3 INFO "POST /update_cmd/ HTTP/1.1" 302
    initiative name type hp/max_hp
    22 giant-rat giant-rat 3/3
    16 rat rat 1/1
    12 sahuagin#1 sahuagin 11/11
    9 goblin goblin 6/9
    3 druid druid 23/23
    2021-05-18 01:02:01,222 itty3 INFO ['22 giant-rat giant-rat 3/3', '16 rat rat 1/1', '12 sahuagin#1 sahuagin 11/11', '9 goblin goblin 6/9', '3 druid druid 23/23']
    2021-05-18 01:02:01,222 itty3 INFO <li>22 giant-rat giant-rat 3/3</li><li>16 rat rat 1/1</li><li>12 sahuagin#1 sahuagin 11/11</li><li>9 goblin goblin 6/9</li><li>3 druid druid 23/23</li>
    2021-05-18 01:02:01,222 itty3 INFO "GET / HTTP/1.1" 200


## Vagrant Instructions

If you want to use Vagrant as a virtual development environment,
you can download it, and Virtualbox, from vagrantup.com
and virtualbox.org, respectively.

After you've installed them, simply navigate to the root of this
repo using the `cd` command in a terminal, and run the following: 

    vagrant up # Wait for a while, here.
    vagrant ssh # Your prompt should change.
    cd /vagrant
    ls # You should see all of the files from this repo here.
    python3 -m venv dm-env-vagrant
    source dm-env-vagrant/bin/activate
    pip install -r requirements.txt
    python3 web_app.py # or python3 basic.py

You can use `curl` to interact with the server at 127.0.0.1:8000
or use the CLI as usual and documented in earlier instruction
sections.

Or, if you [update the host address for the server](https://itty3.readthedocs.io/en/latest/troubleshooting.html#my-server-isn-t-responding-to-traffic), 
you can navigate to http://192.168.33.10:8000/ to see the page
in your browser.
