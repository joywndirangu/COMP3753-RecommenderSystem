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

#declare a global 
#pipe connection
childConn = None

#define a server
#initialization
#function
def init():

    #declare the global
    #child connection
    global childConn

    #define a pipe connection
    parentConn, childConn = Pipe()

    #define a server process
    server = Process(target=run, args=())
    
    #start the server process
    server.start()
    
    #return the parent connection
    return parentConn

class HTTPRequestHandler(BaseHTTPRequestHandler):

    #declare the global
    #child connection
    global childConn

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
        childConn.send(form)

        #receive the result from the backend
        result = childConn.recv()
        
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

        #end
        return


#define a run function to facilitate server operation
def run(serverClass=HTTPServer, handlerClass=HTTPRequestHandler, port=4443):

    #define the server address
    serverAddress = ('localhost', port)
    httpd = serverClass(serverAddress, handlerClass)
    
    #wrap the HTTPServer socket with SSL
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain('cert.pem', 'key.pem')
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    
    #notify admin of server status
    print(f"Starting HTTPS server on port {port}...")
    
    #begin serving
    httpd.serve_forever()

    #end
    return
