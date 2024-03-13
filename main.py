#########################################################################
#This file serves as the main script for the backend architecture of our#
#Project. 															    #
#																		#
#This script remains responsible for the coordination of all backend	#
#processes and resources.												#
#########################################################################
import connector
import monitor

#define the main function
def main():

    #display the admin CLI header
    print('******************************************')
    print('*   MEDLOCATOR BACKEND ADMIN INTERFACE   *')
    print('******************************************')
    
    #start the database connection process
    con = connector.init()
    
    #start the query monitor process
    mon = monitor.init()
    
    #initialize the session list
    sessions = []
    
    #start the main application loop
    while 1:
        
        #listen for incoming requests
        form = mon.recv()

        #notify the admin of recieved requests
        print('----------- qRequest recieved -----------')
        
        #handle the query forms with con
        #and respond using mon
        mon.send(con.handle(con, form, sessions))
        
        #notify admin of successfully handled form
        print('form handled')
            
        #print a dividing footer 
        #for the admin's ease of use
        print('\n')

#start the backend
if __name__ == "__main__":
    
    #call main
    main()