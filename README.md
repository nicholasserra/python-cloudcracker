#Overview
A python class to interface with the [Cloud Cracker API](https://www.cloudcracker.com/developers.html).
#Usage

###Init
```python
import cloudcracker
c = cloudcracker.CloudCrackerConnection()
```

###Grab dictionaries
format can be 'wpa', 'ntlm', 'cryptsha512', or 'cryptmd5'

```python
c.grab_dictionaries('wpa')
```

###Submit a job
* format: 'wpa', 'ntlm', 'cryptsha512', or 'cryptmd5'
* email: email to deliver results to
* dictionary: dictionary you would like to use (from dictionaries call)
* size: size of dictionary (from dictionaries call)
* uploaded_file: pcap file to crack

```python
c.submit_job('wpa', 'nicks@ydekproductions.com', 'english', 604, uploaded_file)
```

###Check job status
```python
c.grab_job_status('wpa', 'abcdefghijklmnopqrstuvwxyzaejeil')
```