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
    
    #create a clinics database should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS clinics(
    
        clinic_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(64) NOT NULL,
        address VARCHAR(64) NOT NULL
    
    )""")
    
    #create a admins table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS admins(
    
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        clinic_id INT,
        FOREIGN KEY (clinic_id) REFERENCES clinics(clinic_id),
        role VARCHAR(64) NOT NULL,
        name VARCHAR(64) NOT NULL, 
        email VARCHAR(64) UNIQUE NOT NULL,
        password VARCHAR(64) NOT NULL,
        patients TEXT
        
    )""")
    
    #create a patients table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS patients(
    
        patient_id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(64) NOT NULL,
        sex VARCHAR(1) NOT NULL,
        age INT NOT NULL,
        emerg_contact VARCHAR(64) NOT NULL,
        healthcard_no INT NOT NULL,
        address VARCHAR(64) NOT NULL
    
    )""")
    
    #create a records table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS medical_records(
    
        record_id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        FOREIGN KEY (patient_id) REFERENCES patient (patient_id),
        diagnoses TEXT,
        med_hist TEXT,
        medication TEXT
    
    )""")
    
    #create an appointments table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS appointments(

        appt_id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        appt_type VARCHAR(64) NOT NULL,
        appt_status VARCHAR(64) NOT NULL,
        appt_datetime DATETIME NOT NULL
    
    )""")
    
    #close the cursor
    cursor.close()

    #make a commit
    db.commit()
    
    #return the data base connection
    return db
    
#define a query form handler function
def handle(form, sessions, con):

    #identify the form user
    user = authenticate(form, sessions, con)

    #if the user does not have an open
    #session, allow them to create an 
    #account or sign in
    if user == None:

        #detect a creation request
        if form['type'] == 'create':

            #detect a admin creation request
            if form['act'] == 'user':

                #try to hash the provided password
                try: 
                    form['data'][4] = hashlib.sha256(form['data'][4].encode()).hexdigest()
                except Exception as e:
                    print(e)
                    return 'Cfailure@127 - password hashing failure'

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@126 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 6:

                        #validate the clinic_id type
                        if not isinstance(data[0], int):
                            return 'Cfailure@142 - invalid clinic_id data type'
                        
                        #validate the role type
                        if not isinstance(data[1], str) or len(data[1]) > 64:
                            return 'Cfailure@146 - invalid role data type/length'
                        
                        #validate name type
                        if not isinstance(data[2], str) or len(data[2]) > 64:
                            return 'Cfailure@150 - invalid name data type/length'

                        #validate email type
                        if not isinstance(data[3], str) or len(data[3]) > 64:
                            return 'Cfailure@154 - invalid email data type/length'
                        
                        #validate password type
                        if not isinstance(data[4], str) or len(data[4]) > 64:
                            return 'Cfailure@158 - invalid password data type/length'
                        
                        #validate patients type
                        if not isinstance(data[5], str):
                            return 'Cfailure@162 - invalid patients data type'
                
                        #create a cursor
                        cursor = con.cursor()

                        #check if the provided email
                        #is already in use
                        if not vacant(data[3], cursor):
                            return 'Cfailure@170 - provided email already in use'
                        
                        #insert the user
                        cursor.execute("""(     
                            INSERT INTO admins (
                                clinic_id, 
                                role, 
                                name, 
                                email, 
                                password, 
                                patients
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                        )""", data)

                        #report to the front end
                        return 'success - admin created'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@189 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@189 - invalid data format'
                
            #detect an invalid act
            else:
                return 'Cfailure@197 - invalid act, no credentials'
        
        #detect a sign in attempt
        elif form['type'] == 'sign in':

            #try to hash the provided password
            try: 
                form['data'][1] = hashlib.sha256(form['data'][1].encode()).hexdigest()
            except Exception as e:
                print(e)
                return 'Cfailure@208 - password hashing failure'

            #try to package the 
            #recieved form data
            data = None
            try: 
                data = tuple(form['data'])
            except Exception as e:
                print(e)
                return 'Cfailure@217 - packaging failure'
            
            #check that data has been properly initialized
            if data != None:

                #check that the proper number
                #of parameters have been sent
                if len(data) == 2:

                    #validate the email type
                    if not isinstance(data[0], str):
                        return 'Cfailure@228 - invalid email data type'

                    #validate the password type
                    if not isinstance(data[1], str):
                        return 'Cfailure@232 - invalid password data type'
                    
                    #create a cursor
                    cursor = con.cursor()
                    
                    #search for the user's table entry
                    cursor.execute(
                        "SELECT * FROM admins WHERE email = %s AND password = %s", 
                        (
                            data[0], 
                            data[1]
                        )
                    )
                    
                    #fetch the search results
                    user = cursor.fetchone()
                    
                    #close the cursor
                    cursor.close()
                    
                    #handle invalid credentials
                    if user == None:
                        
                        #report an invalid email password combo
                        return 'Cfailure@256 - invalid email/password'
                    
                    #perform the sign in routine
                    else:
                    
                        #check if the user is already signed in
                        signee = authenticate(form, sessions, con)
                        if signee != None:
                        
                            #report that the user is already signed in
                            return 'Cfailure@266: user already signed in'
                        
                        #sign the user in 
                        else: 
                        
                            #create a cookie
                            cookie = createCookie(user)
                        
                            #add the userID to the users list
                            sessions.append(cookie['session'].value)
                            print(sessions)
                            
                            #return the session cookie
                            return cookie
                        
                #detect invalid data format
                else:
                    return 'Cfailure@189 - invalid data format'
                
            #detect invalid data format
            else:
                return 'Cfailure@189 - invalid data format'
            
        #detect an invalid format
        else:
            return 'Cfailure@189 - invalid data format'
        
    #detect an accredited admin
    #request, perform the specified
    #CRUD operation
    else:

        #detect a creation form
        if form['type'] == 'create':

            #detect an appointment act
            if form['act'] == 'appointment':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@311 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 4:

                        #validate the patient id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@322 - invalid patient_id data type'
                        
                        #validate the appt type type
                        if not isinstance(data[1], str) or len(data[1]) > 64:
                            return 'Cfailure@326 - invalid appt_type data type/length'
                        
                        #validate the appt status type
                        if not isinstance(data[2], str) or len(data[2]) > 16:
                            return 'Cfailure@330 - invalid appt_status data type/length'
                        
                        #validate the appt datetime
                        if not validDatetime(data[3]):
                            return 'Cfailure@334 - invalid appt_date format, expected YYYY-MM-DD-Hrs-Min'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #insert the appointment
                        cursor.execute("""(     
                            INSERT INTO admins (
                                patient_id, 
                                appt_type, 
                                appt_status, 
                                appt_datetime
                            ) VALUES (%s, %s, %s, %s)
                        )""", data)

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front
                        return 'success - appointment created'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@189 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@189 - invalid data format'

            #detect a patient act
            elif form['act'] == 'patient':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@362 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 6:

                        #validate the patient name type
                        if not isinstance(data[0], str) or len(data[0]) > 64:
                            return 'Cfailure@373 - invalid patient_name data type/length'
                        
                        #validate the sex type
                        if not isinstance(data[1], str) or len(data[1]) > 1:
                            return 'Cfailure@377 - invalid sex data type/length'
                        
                        #validate the age type
                        if not isinstance(data[2], int):
                            return 'Cfailure@381 - invalid age data type'

                        #validate the emergency contact type
                        if not isinstance(data[3], str) or len(data[3]) > 64:
                            return 'Cfailure@385 - invalid emergency contact data type/length'
                        
                        #validate the healthcard number type
                        if not isinstance(data[4], int):
                            return 'Cfailure@389 - invalid healthcard number data type'
                        
                        #validate the patient's address
                        if not isinstance(data[5], str) or len(data[5]) > 64:
                            return 'Cfailure@393 - invalid address data type/length'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #make the insertion
                        cursor.execute("""INSERT INTO patients(
                            patient_name,
                            sex,
                            age,
                            emerg_contact,
                            healthcard_no,
                            address
                        ) VALUES (%s, %s, %s, %s, %s, %s)""", data)

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - patient created'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@189 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@189 - invalid data format'

            #detect a medical record act
            elif form['act'] == 'medical_record':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@126 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 4:

                        #validate the patient_id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@460 - invalid patient_id data type'
                        
                        #validate the diagnoses type
                        if not isinstance(data[1], str):
                            return 'Cfailure@464 - invalid diagnoses data type'
                        
                        #validate the med_hist type
                        if not isinstance(data[2], str):
                            return 'Cfailure@468 - invalid med_hist data type'
                        
                        #validate the medication type
                        if not isinstance(data[3], str): 
                            return 'Cfailure@472 - invalid medication data type'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #make the insertion
                        cursor.execute("""INSERT INTO medical_records(
                            patient_id,
                            diagnoses,
                            med_hist,
                            medication
                        ) VALUES (%s, %s, %s, %s)""", data)

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - created medical record'

                    #detect invalid data format
                    else:
                        return 'Cfailure@189 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@189 - invalid data format'

            #detect an invalid act
            else:
                return 'Cfailure - invalid act'
            
        #detect a retrieval form
        elif form['type'] == 'retrieve':

            #detect an admin act
            if form['act'] == 'admin':

            #detect an appointment act
            elif form['act'] == 'appointment':

            #detect a patient act
            elif form['act'] == 'patient':

            #detect a medical record act
            elif form['act'] == 'medical_record':

            #detect an invalid act
            else:
                return 'Cfailure - invalid act'
            
        #detect an update form
        elif form['type'] == 'update':

            #detect an admin act
            if form['act'] == 'admin':

            #detect an appointment act
            elif form['act'] == 'appointment':

            #detect a patient act
            elif form['act'] == 'patient':

            #detect a medical record act
            elif form['act'] == 'medical_record':

            #detect an invalid act
            else:
                return 'Cfailure - invalid act'
            
        #detect a delete form
        elif form['type'] == 'delete':

            #detect an admin act
            if form['act'] == 'admin':

            #detect an appointment act
            elif form['act'] == 'appointment':

            #detect a patient act
            elif form['act'] == 'patient':

            #detect a medical record act
            elif form['act'] == 'medical_record':

            #detect an invalid act
            else:
                return 'Cfailure - invalid act'
            
        #detect an invalid type
        else:
            return 'Cfailure - invalid type'

#define a user authentication function
def authenticate(form, sessions, con):

    #check that the form cookie 
    #represents a valid session
    if form['cookie'] in sessions:

        #create a cursor
        cursor = con.cursor()
        
        #query the user entry
        cursor.execute('SELECT * FROM admins WHERE user_id = %s', (form['cookie'],))
        
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
    cookie['session'] = str(user[0])
    cookie['session']['path'] = '/'
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
    
#define a row absence detection function
def notin(row_name, row_val, table, con):
    
    #create a cursor
    cursor = con.cursor()

    #search the table for the row_id
    cursor.execute(f'SELECT * FROM {table} WHERE {row_name} = %s', (row_val,))
    row = cursor.fetchone()

    #close the cursor
    cursor.close()

    #return whether or not the row exist
    if row != None:
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
    
#define a date validator function
def validDate(dateString):

    #attempt to parse the date string 
    #using the expected MySQL date format
    try:
        datetime.strptime(dateString, '%Y-%m-%d')
        return True
    
    #parsing failed, the 
    #format is incorrect
    except ValueError:
        return False