#########################################################################
#This file serves as the main script for the backend architecture of our#
#Project. 															    #
#																		#
#This script remains responsible for the coordination of all backend	#
#processes and resources.												#
#########################################################################
import threading
import connector
import monitor
import atexit

#global flag to control the main loop
running = True

#kill command listener thread
def input_listener():
    global running
    while True:
        user_input = input()
        if user_input.lower() == 'q':
            running = False
            break

#child process kill
#function
def cleanup(server):
    server.terminate()

#define the main function
def main():

    #display the admin CLI header
    print('******************************************')
    print('*   MEDLOCATOR BACKEND ADMIN INTERFACE   *')
    print('******************************************')
    
    #start the database connection process
    con = connector.init()
    
    #start the query monitor process
    mon, server = monitor.init()

    #register cleanup function
    atexit.register(cleanup, server=server)

    #start the input listener thread
    listener_thread = threading.Thread(target=input_listener)
    listener_thread.start()
    
    #initialize the session list
    sessions = []
    
    #start the main application loop
    while running == True:

        #listen for incoming requests
        if mon.poll():
            form = mon.recv()
            print(f'\nmain - {form} - {sessions}\n')
   
            #handle the query forms with con
            #and respond using mon
            mon.send(connector.handle(form, sessions, con))

    #join with the listener thread
    listener_thread.join()

#start the backend
if __name__ == "__main__":
    main()