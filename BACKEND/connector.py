#####################################################################
#This file serves to provide the backend access to the supporting	#
#database management system (MySQL).								#
#																	#
#All iteractions between MySQL and the backend architecture shall be# 
#facilitated by the use of resources defined within this script.    # 
#####################################################################
import mysql.connector
import hashlib
from http.cookies import SimpleCookie
from datetime import datetime, timedelta

#define a init function
def init():
    
    #connect to mysql
    db = mysql.connector.connect(
    
        host="localhost",
        user="root",
        password="mysql"
       
    )
    
    #open a database cursor
    cursor = db.cursor()
    
    #create a medlocator database should it not exist
    cursor.execute('CREATE DATABASE IF NOT EXISTS medlocator')
    
    #switch the connection to the medlocator database
    cursor.execute('USE medlocator')
    
    #create a location database should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS locations(
    
        locationID INT AUTO_INCREMENT PRIMARY KEY,
        address VARCHAR(64) NOT NULL,
        latitude VARCHAR(64) NOT NULL,
        longitude VARCHAR(64) NOT NULL
    
    )""")
    
    #create a clinics table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS clinics(
    
        clinicID INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(64) NOT NULL,
        locationID INT,
        FOREIGN KEY (locationID) REFERENCES locations(locationID)
        
    )""")
    
    #create a user table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    
        userID INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(64) NOT NULL UNIQUE,
        password VARCHAR(64) NOT NULL 
    
    )""")
    
    #create a patient table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS patients(
    
        patientID INT AUTO_INCREMENT PRIMARY KEY,
        userID INT,
        FOREIGN KEY (userID) REFERENCES users(userID),
        name VARCHAR(64) NOT NULL,
        dateOfBirth DATE NOT NULL
    
    )""")
    
    #create a medical history table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS medicalHistory(
    recordID INT AUTO_INCREMENT PRIMARY KEY,
        
        patientID INT,
        FOREIGN KEY (patientID) REFERENCES patients(patientID),
        description TEXT NOT NULL,
        date DATE NOT NULL 
    
    )""")
    
    #create an appointment table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS appointments(

        appointmentID INT AUTO_INCREMENT PRIMARY KEY,
        patientID INT,
        FOREIGN KEY (patientID) REFERENCES patients(patientID),
        clinicID INT,
        FOREIGN KEY (clinicID) REFERENCES clinics(clinicID),
        status VARCHAR(255) NOT NULL,  # Assuming VARCHAR(255), adjust as necessary
        dateTime DATETIME NOT NULL
        
    )""")
    
    #create a feedback table should it not exists
    cursor.execute("""CREATE TABLE IF NOT EXISTS feedback(

        feedbackID INT AUTO_INCREMENT PRIMARY KEY,
        userID INT,
        FOREIGN KEY (userID) REFERENCES users(userID),  # Added missing comma here
        clinicID INT,
        FOREIGN KEY (clinicID) REFERENCES clinics(clinicID),
        rating INT NOT NULL,
        comment TEXT NOT NULL
        
    )""")
    
    #close the cursor
    cursor.close()
    
    #return the data base connection
    return db
    
#define a query form handler function
def handle(con, form, sessions):

    #detect a sign in form
    if form['type'] == 'sign in':
    
        #hash the provided password
        passwordHash = hashlib.sha256(form['data'][1].encode()).hexdigest()
        
        #create a cursor
        cursor = con.cursor()
        
        #search for the user's table entry
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password_hash = %s", 
            (
                form['data'][0], 
                passwordHash
            )
        )
        
        #fetch the search results
        user = cursor.fetchone()
        
        #close the cursor
        cursor.close()
        
        #handle invalid credentials
        if user == None:
            
            #report an invalid email password combo
            return 'failure: invalid email/password'
        
        #perform the sign in routine
        else:
        
            #check if the user is already signed in
            if authenticate(form, sessions, con) != None:
            
                #report that the user is already signed in
                return 'failure: user already signed in'
            
            #sign the user in 
            else: 
            
                #package the userID and IP
                session = createCookie(user)
            
                #add the userID to the users list
                sessions.append(session)
                
                #return the session cookie
                return session

    #detect a creation form
    elif form['type'] == 'create':
    
        #detect an account creation act
        if form['act'] == 'user':
        
            #hash the provided password
            passwordHash = hashlib.sha256(form['data'][1].encode()).hexdigest()
        
            #create a cursor
            cursor = con.cursor()

            #check if the provided email
            #is already in use
            if vacant(form['data'][0], cursor):

                #insert the new user
                cursor.execute(
                    'INSERT INTO users (email, password) VALUES (%s, %s)', 
                    (
                        #email
                        form['data'][0], 
                        
                        #password
                        passwordHash
                    )
                )
            
                #fetch the user
                cursor.execute('SELECT * FROM users WHERE email = %s', (form['data'][0],))
                user = cursor.fetchone()
            
                #create a new patient entry
                cursor.execute(
                    'INSERT INTO patients (userID, name, dateOfBirth) VALUES (%s, %s, %s)', 
                    (
                        #userID
                        user[0],
                        
                        #name
                        form['data'][2],
                        
                        #dateOfBirth
                        form['data'][3],
                    )    
                )
           
                #close the cursor
                cursor.close()
           
                #report a success
                return 'success: user created'
            
            #detect invalid form data
            else:

                #report
                return 'failure: username already taken'
           
        #detect an appointment creation request
        elif form['act'] == 'appointment':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid form credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid form credentials'
                
            #begin the appointment 
            #creation routine
            else:
            
                #create a cursor
                cursor = con.cursor()
                
                #fetch the user's patient entry
                cursor.execute('SELECT * FROM patients WHERE userID = %s', (user[0],))
                patient = cursor.fetchone()

                #detect an invalid date format
                if not validDatetime(form['data'][2]):
                    return 'failure: invalid datetime'
                
                #insert the appointment
                cursor.execute(
                    'INSERT INTO appointments (patientID, clinicID, status, dateTime) VALUES (%s, %s, %s, %s)',
                    (
                        #patientID
                        patient[0],
                        
                        #clinicID
                        form['data'][0],
                        
                        #status
                        form['data'][1],
                        
                        #date time
                        form['data'][2]
                    )
                )
                
                #close the cursor
                cursor.close()
                
                #report a success
                return 'success: created appointment'

        #detect a feedback creation request
        if form['act'] == 'feedback':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid form credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid credentials'
                
            #begin the feedback 
            #creation routine
            else:
        
                #create a cursor
                cursor = con.cursor()          
                    
                #insert the feedback
                cursor.execute(
                    'INSERT INTO feedback (userID, clinicID, rating, comment) VALUES (%s, %s, %s, %s)',
                    (
                        #userID
                        user[0],
                        
                        #clinicID
                        form['data'][0],
                        
                        #rating
                        form['data'][1],
                        
                        #comment
                        form['data'][2]
                    )
                )
                
                #close the cursor
                cursor.close()
                
                #report a success
                return 'success: created feedback'
            
        #detect an invalid act
        else:
        
            #report invalid act
            return 'failure: invalid act'
        
    #detect a retrieval form
    elif form['type'] == 'retrieve':
    
        #detect a user data request
        if form['act'] == 'user':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid form credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid form credentials'
                
            #begin the user 
            #retrieval routine 
            else:
            
                #return the user
                return user    
        
        #detect an appointment request
        elif form['act'] == 'appointment':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid form credentials
            if user == None:
                
                #report invalid credentials
                return 'failure: invalid credentials'
                
            #begin appointment data retrieval
            else: 
            
                #create a cursor
                cursor = con.cursor()
                
                #fetch the user's patient entry
                #from the patient table
                cursor.execute('SELECT * FROM patients WHERE userID = %s', (user[0],))
                patient = cursor.fetchone()
                
                #query the patient's appointments
                cursor.execute('SELECT * FROM appointments WHERE  patientID = %s', (patient[0],))
                
                #handle the query results
                appointments = []
                appointment = cursor.fetchone()
                while appointment != None:
                
                    #add the result to the
                    #appointments array
                    appointments.append(appointment)
                    
                    #fetch the next appointment
                    appointment = cursor.fetchone()
                    
                #close the cursor
                cursor.close()

                #return the appointments
                return tuple(appointments)

        #detect a feedback data request
        elif form['act'] == 'feedback':
           
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid credentials
            if user == None:
            
                #report invalid form credentials
                return 'failure: invalid credentials'
                
            #begin feedback retrieval
            else:
            
                #create a cursor
                cursor = con.cursor()
            
                #query the feedback table
                cursor.execute('SELECT * FROM feedback WHERE feedbackID = %s', (form['data'][0],))
                
                #fetch the query results
                feedbackEntries = []
                feedback = cursor.fetchone()
                while feedback != None:
                
                    #add the result to the
                    #feedbackEntries array
                    feedbackEntries.append(feedback)
                    
                    #fetch the next feedback
                    feedback = cursor.fetchone()
                    
                #close the cursor
                cursor.close()

                #return the feedback
                return tuple(feedbackEntries)
                
        #detect an invalid act
        else:
        
            #report invalid act
            return 'failure: invalid act'
    
    #detect an update form
    elif form['type'] == 'update':
    
        #detect an account update request
        if form['act'] == 'user':
            
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid credentials'
            
            #perform the user update 
            else: 
                
                #create a cursor
                cursor = con.cursor()

                #check that the user does
                #not already exist
                if vacant(form['data'][0], cursor):
                
                    #make the table update
                    cursor.execute(
                        
                        #query the update into the user's row
                        'UPDATE users SET email = %s, password = %s WHERE userID = %s', 
                        (
                            #email
                            form['data'][0],
                        
                            #password
                            passwordHash,
                        
                            #userID
                            user[0]
                        )  
                    )
                    
                    #close the cursor
                    cursor.close()
                    
                    #report the update
                    return 'success: updated user'
                
                #detect invalid form data
                else:

                    #close the cursor
                    cursor.close()

                    #report the failure
                    return 'failure: email already taken'

        #detect an appointment update request
        elif form['act'] == 'appointment':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid credentials'
                
            #perform the update
            else:
            
                #create a cursor
                cursor = con.cursor()
            
                #fetch the user's patient entry
                cursor.execute('SELECT * FROM patients WHERE userID = %s', (user[0],))
                patient = cursor.fetchone()
                
                #make the appointment data update
                cursor.execute(
                
                    #query the update into the appointment row
                    'UPDATE appointments SET clinicID = %s, status = %s WHERE appointmentID = %s AND patientID = %s', 
                    (
                        #clinicID
                        form['data'][0],
                    
                        #status
                        form['data'][1],
                    
                        #appointmentID
                        form['data'][2],
                        
                        #patientID
                        patient[0]
                    )
                )
                
                #close the cursor
                cursor.close()
                
                #report the update
                return 'success: updated appointment'
        
        #detect a feedback update request
        elif form['act'] == 'feedback':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid credentials
            if user == None:

                #report invalid credentials
                return 'failure: invalid credentials'
            
            #perform the update
            else: 
                
                #create a cursor
                cursor = con.cursor()
                
                #make the update
                cursor.execute(
                    
                    #query the update into the feedback table
                    'UPDATE feedback SET clinicID = %s, rating = %s, comment = %s WHERE userID = %s',
                    (
                        #clinicID
                        form['data'][0],
                    
                        #rating
                        form['data'][1],
                    
                        #comment
                        form['data'][2],
                    
                        #userID
                        user[0]
                    ) 
                )
                
                #close the cursor
                cursor.close()
                
                #report the update
                return 'success: feedback updated'

        #detect an invalid act
        else:
        
            #report invalid act
            return 'failure: invalid act'
            
    #detect a deletion form
    elif form['type'] == 'delete':
    
        #detect an account deletion request
        if form['act'] == 'user':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
        
            #detect invalid credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid credentials'
                
            #begin user deletion
            else:
            
                #end the user's session
                endSession(user, sessions)
                
                #make a cursor
                cursor = con.cursor()
            
                #make the user deletion
                cursor.execute('DELETE FROM users WHERE userID = %s', (user[0],))
                
                #close the cursor
                cursor.close()
                
                #report the deletion
                return 'success: user deleted'
                
        #detect an appointment deletion request
        elif form['act'] == 'appointment':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
        
            #detect invalid credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid credentials'
                
            #perform the deletion
            else:
            
                #create a cursor
                cursor = con.cursor()
                
                #fetch the user's patient entry
                cursor.execute('SELECT * FROM patients WHERE userID = %s', (user[0],))
                patient = cursor.fetchone()
                
                #delete the appointment
                cursor.execute(
                    
                    #query the deletion
                    'DELETE FROM appointments WHERE appointmentID = %s AND patientID = %s',
                    (
                        #appointmentID
                        form['data'][0],
                        
                        #patientID
                        patient[0]
                    )
                )
                
                #close the cursor
                cursor.close()
   
                #report the deletion
                return 'success: appointment deleted'
 
        
        #detect a feedback deletion request
        elif form['act'] == 'feedback':
        
            #authenticate the form credentials
            #against open sessions
            user = authenticate(form, sessions, con)
            
            #detect invalid credentials
            if user == None:
            
                #report invalid credentials
                return 'failure: invalid credentials'
                
            #perform the deletion
            else:
            
                #create a cursor
                cursor = con.cursor()
                
                #delete the appointment
                cursor.execute(
                
                    'DELETE FROM feedbackID WHERE feedbackID = %s AND userID = %s',
                    (
                        #feedbackID
                        form['data'][0],
                        
                        #userID
                        user[0]
                    )
                    
                )
                
                #close the cursor
                cursor.close()
                
                #report the deletion
                return 'success: feedback deleted'
                
        #detect an invalid act
        else:
        
            #report invalid act
            return 'failure: invalid act'

    #report error
    else:
    
        return 'failure: invalid request type'

#define a user authentication function
def authenticate(form, sessions, con):

    #check that the form cookie 
    #represents a valid session
    if form['cookie'] in sessions:
        
        #create a cursor
        cursor = con.cursor()
        
        #query the user entry
        cursor.execute('SELECT * FROM users WHERE userID = %s', (form['cookie'],))
        
        #fetch the result 
        user = cursor.fetchone()
        
        #close the cursor
        cursor.close()
        
        #return the fetched user
        return user
        
    #detect invalid form cookie
    else:
    
        #return none
        return None
    
#define a cookie generation function
def createCookie(user):

    #create an instance of SimpleCookie
    cookie = SimpleCookie()
    
    #get the current date and time
    now = datetime.now()

    #create a timedelta of 30 minutes
    delta = timedelta(minutes=30)

    #calculate the new time, 30 minutes from now
    futureTime = now + delta
    
    #format the futureTime variable for the expires attribute
    expiry = futureTime.strftime("%a, %d-%b-%Y %H:%M:%S GMT")
    
    #define a session cookie
    cookie['session'] = user[0]
    cookie['session']['path'] = '/'
    cookie['session']['expires'] = expiry
    cookie['session']['httponly'] = True
    
    #return the cookie
    return cookie

#define an endSession function
def endSession(user, sessions):

    #scan the sessions list for the
    #user's cookie
    for cookie in sessions:

        #check the cookie's value
        if cookie['session'].value() == user[0]:

            #remove the cookie 
            #from the session list
            sessions.remove(cookie)

    #return
    return

#define a vacancy detection function
def vacant(username, cursor):

    #query the database for the username         
    cursor.execute('SELECT * FROM users WHERE email = %s', (username,))

    #process the result
    result = cursor.fetchone()
    if result != None:
        return False
    else: 
        return True
    
#define a datetime validator function
def validDatetime(dateString):

    #attempt to parse the string 
    #using the desired format
    try:
        datetime.strptime(dateString, '%Y-%m-%d %H:%M:%S')
        return True
    
    #if parsing fails, the 
    #format does not match
    except ValueError:
        return False