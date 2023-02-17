# keas.kmi

This package provides a NIST SP 800-57 compliant Key Management Infrastructure
(KMI).

## Installation for Ubuntu 22.04 / Debian 11

For local installation do the following steps:

* install a python virtualenv and activate virtualenv
* install zc.buildout within virtualenv
* source checkout keas.kmi
* buildout

```
~$ python3 -m venv kmi
~$ cd kmi
~/kmi$ source bin activate 
(kmi)~/kmi$ pip install zc.buildout
(kmi)~/kmi$ git clone https://github.com/zopefoundation/keas.kmi.git
(kmi)~/kmi$ cd keas.kmi
(kmi)~/kmi/keas.kmi$ buildout
```

## Start and stop the server

To start the serverprocess in foreground run one of the following commands:

```
(kmi)~/kmi/keas.kmi$ ./bin/runserver 
[2023-02-17 14:17:34 +0100] [13268] [INFO] Starting gunicorn 20.1.0
[2023-02-17 14:17:34 +0100] [13268] [INFO] Listening at: http://127.0.0.1:8000 (13268)
[2023-02-17 14:17:34 +0100] [13268] [INFO] Using worker: sync
[2023-02-17 14:17:34 +0100] [13269] [INFO] Booting worker with pid: 13269
```

or:

```
(kmi)~/kmi/keas.kmi$ ./bin/gunicorn --paste server.ini
[2023-02-17 14:19:27 +0100] [13279] [INFO] Starting gunicorn 20.1.0
[2023-02-17 14:19:27 +0100] [13279] [INFO] Listening at: http://127.0.0.1:8000 (13279)
[2023-02-17 14:19:27 +0100] [13279] [INFO] Using worker: sync
[2023-02-17 14:19:27 +0100] [13280] [INFO] Booting worker with pid: 13280
```

The server will come up on port 8000. To stop the server press CTRL-C

## Try it out

You can create a new key encrypting key using:

```
(kmi)~/kmi/keas.kmi$ wget http://localhost:8000/new -O kek.dat --ca-certificate sample.crt --post-data=""
```

or, if you want a more convenient tool:

```
(kmi)~/kmi/keas.kmi$ ./bin/testclient http://localhost:8000 -n > kek.dat
```

The data encryption key can now be retrieved by posting the KEK to another
URL:

```
(kmi)~/kmi/keas.kmi$ wget http://localhost:8000/key --header 'Content-Type: text/plain' --post-file kek.dat -O datakey.dat --ca-certificate sample.crt
```

or:

```
(kmi)~/kmi/keas.kmi$ ./bin/testclient http://localhost:8000 -g kek.dat > datakey.dat
``` 

**Note: To be compliant, for production purposes the server must use an encrypted communication c
hannel of course.  The ``--ca-certificate`` tells wget to trust the sample self-signed
certificate included in the keas.kmi distribution; you'll want to generate a
new SSL certificate for production use.**
