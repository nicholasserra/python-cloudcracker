import urllib2
import mimetypes
import mimetools
import codecs
from io import BytesIO

try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        from django.utils import simplejson as json

writer = codecs.lookup('utf-8')[3]
__version__ = '0.0.3'

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def iter_fields(fields):
    """
    Iterate over fields.

    Supports list of (k, v) tuples and dicts.
    """
    if isinstance(fields, dict):
        return ((k, v) for k, v in fields.iteritems())

    return ((k, v) for k, v in fields)

class CloudCrackerError(Exception):
    pass

class CloudCrackerConnection(object):
    def __init__(self):
        '''
        Cloud Cracker API class
        '''
        self.api_url = 'https://cloudcracker.com/api/'
        self.status_codes = {
            0: 'The job has been submitted, but valid payment has not yet been received.',
            1: 'The job has been submitted and valid payment has been received.',
            2: 'The job has started running.',
            3: 'The job has completed.'
        }

    def grab_dictionaries(self, format):
        """Grab dictionary options"""

        url = '%s%s/dictionaries' % (self.api_url, format)
        r = urllib2.Request(url)
        response = self.call(r)
        content = response.read()
        response.close()

        parsed = json.loads(content)
        return parsed
        
    def submit_job(self, format, email, dictionary, size, uploaded_file, essid=None):
        """
        Submit your cracking job.
        Format can be: ['wpa', 'ntlm']
        """

        url = '%s%s/job' % (self.api_url, format)

        params = {
            'email': email,
            'dictionary': dictionary,
            'size': size
        }

        if format == 'wpa':
            params['pcap'] = (uploaded_file.name, uploaded_file.read())
        elif format == 'ntlm':
            params['ntlm'] = (uploaded_file.name, uploaded_file.read())
        else:
            raise AttributeError('Specify a valid format.')

        if essid:
            params['essid'] = essid

        body, content_type = self.encode_multipart_formdata(params)
        headers = {'Content-Type': content_type, 'Content-Length': str(len(body))}
        r = urllib2.Request(url, body, headers)
        response = self.call(r)
        content = response.read()
        response.close()

        parsed = json.loads(content)
        return parsed['reference']

    def grab_job_status(self, format, job_reference):
        """Grab status of job. Returns status code and message."""

        url = '%s%s/job/%s' % (self.api_url, format, job_reference)
        r = urllib2.Request(url)
        response = self.call(r)
        content = response.read()
        response.close()

        parsed = json.loads(content)
        return parsed['status'], self.status_codes[parsed['status']]

    def grab_bitcoin_payment_info(self, format, job_reference):
        """Returns info to pay via Bitcoin"""

        url = '%s%s/payment/%s' % (self.api_url, format, job_reference)
        r = urllib2.Request(url)
        response = self.call(r)
        content = response.read()
        response.close()

        return json.loads(content)
        
    def send_stripe_payment(self, format, job_reference, token):
        """Sends your stripe token to pay for a cracking job"""
        url = '%s%s/payment/%s' % (self.api_url, format, job_reference)

        params = {'stripeToken': token}
        body, content_type = self.encode_multipart_formdata(params)
        headers = {'Content-Type': content_type}
        r = urllib2.Request(url, body, headers)
        response = self.call(r)

        #api returns blank 200 on success
        response.close()
        
    def call(self, r):
        try:
            response = urllib2.urlopen(r)
        except urllib2.URLError, e:
            try:
                error = json.loads(e.read())
                raise CloudCrackerError(error['error'])
            except ValueError:
                raise CloudCrackerError
        return response

    #thank you shazow https://github.com/shazow/urllib3
    def encode_multipart_formdata(self, fields, boundary=None):
        """
        Encode a dictionary of ``fields`` using the multipart/form-data mime format.

        :param fields:
            Dictionary of fields or list of (key, value) field tuples.  The key is
            treated as the field name, and the value as the body of the form-data
            bytes. If the value is a tuple of two elements, then the first element
            is treated as the filename of the form-data section.

            Field names and filenames must be unicode.

        :param boundary:
            If not specified, then a random boundary will be generated using
            :func:`mimetools.choose_boundary`.
        """
        body = BytesIO()
        if boundary is None:
            boundary = mimetools.choose_boundary()

        for fieldname, value in iter_fields(fields):
            body.write('--%s\r\n' % (boundary))

            if isinstance(value, tuple):
                filename, data = value
                writer(body).write('Content-Disposition: form-data; name="%s"; '
                                   'filename="%s"\r\n' % (fieldname, filename))
                body.write('Content-Type: %s\r\n\r\n' %
                           (get_content_type(filename)))
            else:
                data = value
                writer(body).write('Content-Disposition: form-data; name="%s"\r\n'
                                   % (fieldname))
                body.write(b'Content-Type: text/plain\r\n\r\n')

            if isinstance(data, int):
                data = str(data)  # Backwards compatibility

            if isinstance(data, unicode):
                writer(body).write(data)
            else:
                body.write(data)

            body.write(b'\r\n')

        body.write('--%s--\r\n' % (boundary))

        content_type = 'multipart/form-data; boundary=%s' % boundary

        return body.getvalue(), content_type
