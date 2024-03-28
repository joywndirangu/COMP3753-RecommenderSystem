####################################################################
#This file serves to provide the backend architecture access to the#
#front end.														   #
#																   #
#All communication with the project front end shall occur through  #
#the http API defined within this file.						       #
####################################################################
from http.server import HTTPServer, BaseHTTPRequestHandler
from multiprocessing import Process, Pipe
from http.cookies import SimpleCookie
import mimetypes
import json
import ssl
import os

#define a server
#initialization
#function
def init():

    #define a pipe connection
    parentConn, childConn = Pipe()

    #define a server process
    server = Process(target=run, args=(childConn,))
    
    #start the server process
    server.start()
    
    #return the parent connection
    return parentConn

#handler class factory function
def makeHTTPRequestHandler(childConn):

    #modified handler class
    class CustomHTTPRequestHandler(BaseHTTPRequestHandler):

        #add an initializer to accept and store childConn
        def __init__(self, *args, **kwargs):

            #store childConn as an instance variable
            self.childConn = childConn

            #initialize the base class (important!)
            super().__init__(*args, **kwargs)

        #define a handlePost function 
        #that correctly parses the incoming JSON
        def handlePost(self):
            contentLength = int(self.headers['Content-Length'])
            postData = self.rfile.read(contentLength)
            postDataStr = postData.decode('utf-8')
            try:
                data = json.loads(postDataStr)
            except json.JSONDecodeError as e:
                self._set_headers('text/plain')
                response = "Invalid JSON format: {}".format(e)
                self.wfile.write(response.encode('utf-8'))
                return None
            return data

        #define a set headers function
        def _set_headers(self, content_type='text/plain'):

            #set CORS headers
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', 'https://localhost:4443/')
            self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.send_header('Access-Control-Allow-Credentials', 'true')
            self.end_headers()

        #define a do options function
        def do_OPTIONS(self):

            #respond to preflight requests
            self._set_headers()

        #define a function to
        #handle incoming 
        #post requests 
        def do_POST(self):

            #handle the POST request
            form = self.handlePost()

            #attempt to retrieve the 'Cookie' header from the request
            cookie_header = self.headers.get('Cookie')
            cookie_value = None

            #parse the Cookie header using SimpleCookie
            if cookie_header:
                cookie = SimpleCookie(cookie_header)
                if 'session' in cookie:
                    cookie_value = cookie['session'].value

            #set the form cookie
            form['cookie'] = cookie_value
            
            #send the form to the backend
            self.childConn.send(form)

            #receive the result from the backend
            result = self.childConn.recv()
            
            #if the result is a string, indicating success or failure
            if isinstance(result, str):

                #send the result string to the client
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                
                #ensure result is a byte-like object before sending
                result = result.encode()
                self.wfile.write(result)
            
            #if the result is a tuple, send it as JSON
            elif isinstance(result, tuple):

                #convert the tuple to JSON
                json_result = json.dumps(result)
                
                #send the JSON string to the client
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', 'https://localhost:4443/')
                self.send_header('Access-Control-Allow-Credentials', 'true')
                self.end_headers()
                self.wfile.write(json_result.encode())
            
            #if the result is a cookie
            elif isinstance(result, SimpleCookie):

                #send the HTTP status code and headers
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')


                #convert the SimpleCookie object to a 
                #string and include it in the Set-Cookie header
                for morsel in result.values():
                    self.send_header('Set-Cookie', morsel.OutputString())
                self.end_headers()
                
                #write any additional response body content if necessary
                response_body = "success - cookie set successfully"
                self.wfile.write(response_body.encode())

        #define a get handler function
        #to server files
        def do_GET(self):

            #find the current working path
            cwd = os.getcwd()

            #serve html page requests
            if self.path == '/test.html':
                serve(self, 'SITE/test.html', cwd)
            elif self.path == '/home.html':
                serve(self, 'SITE/home.html', cwd)
            elif self.path == '/signIn.html':
                serve(self, 'SITE/signIn.html', cwd)
            elif self.path == '/patientDB.html':
                serve(self, 'SITE/patientDB.html', cwd)
            elif self.path == '/map.html':
                serve(self, 'SITE/map.html', cwd)
            elif self.path == '/contactForm.html':
                serve(self, 'SITE/contactForm.html', cwd)

            #serve style requests
            elif self.path == '/home.css':
                serve(self, 'SITE/home.css', cwd)
            elif self.path == '/main.css':
                serve(self, 'SITE/main.css', cwd)
            elif self.path == '/sign.css':
                serve(self, 'SITE/sign.css', cwd)

            #serve image requests
            elif self.path == '/home_bckimg.jpeg':
                serve(self, 'SITE/home_bckimg.jpeg', cwd)
            elif self.path == '/home_image.jpeg':
                serve(self, 'SITE/home_image.jpeg', cwd)
            elif self.path == '/logo.png':
                serve(self, 'SITE/logo.png', cwd)
            elif self.path == '/map.jpeg':
                serve(self, 'SITE/map.jpeg', cwd)
            elif self.path == '/miniHeader.png':
                serve(self, 'SITE/miniHeader.png', cwd)
            elif self.path == '/RSLogo.png':
                serve(self, 'SITE/RSLogo.png', cwd)
                
            #for other paths, serve a 404 response
            else:
                self.send_response(404) 
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'404 Not Found')
    
    #return the custom handler class
    return CustomHTTPRequestHandler

#define a file serve routine
def serve(self, rel_path, cwd):

    #generate the absolute file path
    file_path = os.path.join(cwd, rel_path)

    #determine the MIME type of the file
    mime_type, _ = mimetypes.guess_type(file_path)

    #fallback to 'application/octet-stream' if MIME type is not determined
    if mime_type is None:
        mime_type = 'application/octet-stream'

    #check if the file exists
    if os.path.exists(file_path):

        #open the file for reading in binary mode
        with open(file_path, 'rb') as file:

            #set HTTP response headers
            self.send_response(200)
            self.send_header('Content-Type', mime_type)
            self.end_headers()
            
            #send the content of the file to the client
            self.wfile.write(file.read())

    #serve a 404 response if the file does not exist
    else:
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 Not Found')

#define a run function to facilitate server operation
def run(childConn, serverClass=HTTPServer, port=4443):

    #define the server address
    serverAddress = ('localhost', port)

    #create a custom handler class using the factory function
    CustomHandler = makeHTTPRequestHandler(childConn)

    #initialize HTTPServer with the custom handler class
    httpd = serverClass(serverAddress, CustomHandler)
    
    #SSL setup
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('SECURITY/cert.pem', 'SECURITY/key.pem')
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    #notify the admin of the server starting
    print(f"Starting HTTPS server on port {port}...")
    httpd.serve_forever()