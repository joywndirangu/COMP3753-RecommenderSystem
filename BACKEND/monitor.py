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
                    cookie_value = cookie['exampleCookie'].value

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
                response_body = "cookie set successfully."
                self.wfile.write(response_body.encode())

        #define a get handler function
        #to server files
        def do_GET(self):

            #check the URL path to decide what to serve
            if self.path == '/test.html':

                #path to your index.html file
                file_path = 'C:/Users/natee/OneDrive/Documents/COMP_3753/COMP3753-RecommenderSystem/BACKEND/test.html'
                
                #check if file exists
                if os.path.exists(file_path):

                    #open the file for reading
                    with open(file_path, 'rb') as file:

                        #set HTTP response headers
                        self.send_response(200)
                        self.send_header('Content-Type', 'text/html')
                        self.end_headers()
                        
                        #send the content of the file to the client
                        self.wfile.write(file.read())
                else:

                    #file not found, set 
                    #response code to 404 (Not Found)
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'404 Not Found')
            else:

                #for other paths, serve a 404 response
                self.send_response(404) 
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'404 Not Found')
    
    #return the custom handler class
    return CustomHTTPRequestHandler

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
    context.load_cert_chain('cert.pem', 'key.pem')
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

    #notify the admin of the server starting
    print(f"Starting HTTPS server on port {port}...")
    httpd.serve_forever()