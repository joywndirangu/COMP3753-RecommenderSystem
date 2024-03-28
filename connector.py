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
import json

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
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
        diagnoses TEXT,
        med_hist TEXT,
        medication TEXT
    
    )""")
    
    #create an appointments table should it not exist
    cursor.execute("""CREATE TABLE IF NOT EXISTS appointments(

        appt_id INT AUTO_INCREMENT PRIMARY KEY,
        patient_id INT,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
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
            if form['act'] == 'admin':

                #try to hash the provided password
                try: 
                    form['data'][4] = hashlib.sha256(form['data'][4].encode()).hexdigest()
                except Exception as e:
                    print(e)
                    return 'Cfailure@124 - password hashing failure'

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@133 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 6:

                        #validate the clinic_id type
                        if not isinstance(data[0], int):
                            return 'Cfailure@144 - invalid clinic_id data type'

                        #validate the role type
                        if not isinstance(data[1], str) or len(data[1]) > 64:
                            return 'Cfailure@148 - invalid role data type/length'
         
                        #validate name type
                        if not isinstance(data[2], str) or len(data[2]) > 64:
                            return 'Cfailure@152 - invalid name data type/length'

                        #validate email type
                        if not isinstance(data[3], str) or len(data[3]) > 64:
                            return 'Cfailure@156 - invalid email data type/length'
                        
                        #validate password type
                        if not isinstance(data[4], str) or len(data[4]) > 64:
                            return 'Cfailure@160 - invalid password data type/length'
                        
                        #validate patients type
                        if not isinstance(data[5], str) or data[5] != '[]':
                            return 'Cfailure@164 - invalid patients data type'
                
                        #create a cursor
                        cursor = con.cursor()

                        #check if the provided email
                        #is already in use
                        if not vacant(data[3], cursor):
                            return 'Cfailure@172 - provided email already in use'
                        
                        #insert the admin
                        cursor.execute("""     
                            INSERT INTO admins (
                                clinic_id, 
                                role, 
                                name, 
                                email, 
                                password, 
                                patients
                                ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, data)

                        #close the cursor 
                        cursor.close()

                        #commit the changes 
                        con.commit()

                        #report to the front end 
                        return 'success - admin created'
                    
                    #detect invalid data format 
                    else:
                        return 'Cfailure@191 - invalid data format'
                    
                #detect invalid data format 
                else:
                    return 'Cfailure@195 - invalid data format'
                
            #detect an invalid act 
            else:
                return 'Cfailure@199 - invalid act, no credentials'
        
        #detect a sign in attempt 
        elif form['type'] == 'sign in':

            #try to hash the provided password
            try: 
                form['data'][1] = hashlib.sha256(form['data'][1].encode()).hexdigest()
            except Exception as e:
                print(e)
                return 'Cfailure@209 - password hashing failure'

            #try to package the 
            #recieved form data
            data = None
            try: 
                data = tuple(form['data'])
            except Exception as e:
                print(e)
                return 'Cfailure@218 - packaging failure'
            
            #check that data has been properly initialized
            if data != None:

                #check that the proper number
                #of parameters have been sent
                if len(data) == 2:

                    #validate the email type
                    if not isinstance(data[0], str):
                        return 'Cfailure@229 - invalid email data type'

                    #validate the password type
                    if not isinstance(data[1], str):
                        return 'Cfailure@233 - invalid password data type'
                    
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
                        return 'Cfailure@257 - invalid email/password'
                    
                    #perform the sign in routine
                    else:
                    
                        #check if the user is already signed in
                        signee = authenticate(form, sessions, con)
                        if signee != None:
                        
                            #report that the user is already signed in
                            return 'Cfailure@267: user already signed in'
                        
                        #sign the user in 
                        else: 
                        
                            #create a cookie
                            cookie = createCookie(user)
                        
                            #add the userID to the users list
                            sessions.append(cookie['session'].value)
                            
                            #return the session cookie
                            return cookie
                        
                #detect invalid data format
                else:
                    return 'Cfailure@284 - invalid data format'
                
            #detect invalid data format
            else:
                return 'Cfailure@288 - invalid data format'
            
        #detect an invalid type
        else:
            return 'Cfailure@292 - invalid type'
        
    #detect an accredited admin
    #request, perform the specified
    #CRUD operation
    else:

        #parse the admin's patient list
        patient_list = json.loads(user[6])

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
                    return 'Cfailure@315 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@324 - patient not bound to admin'

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 4:

                        #validate the patient id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@332 - invalid patient_id data type'
                        
                        #validate the appt type type
                        if not isinstance(data[1], str) or len(data[1]) > 64:
                            return 'Cfailure@336 - invalid appt_type data type/length'
                        
                        #validate the appt status type
                        if not isinstance(data[2], str) or len(data[2]) > 16:
                            return 'Cfailure@340 - invalid appt_status data type/length'
                        
                        #validate the appt datetime
                        if not validDatetime(data[3]):
                            return 'Cfailure@344 - invalid appt_date format, expected %Y-%m-%d %H:%M:%S'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #insert the appointment
                        cursor.execute("""     
                            INSERT INTO appointments (
                                patient_id, 
                                appt_type, 
                                appt_status, 
                                appt_datetime
                            ) VALUES (%s, %s, %s, %s)""", 
                            data
                        )

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front
                        return 'success - appointment created'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@371 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@375 - invalid data format'

            #detect a patient act
            elif form['act'] == 'patient':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@387 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 6:

                        #validate the patient name type
                        if not isinstance(data[0], str) or len(data[0]) > 64:
                            return 'Cfailure@404 - invalid name data type/length'
                        
                        #validate the sex type
                        if not isinstance(data[1], str) or len(data[1]) > 1:
                            return 'Cfailure@408 - invalid sex data type/length'
                        
                        #validate the age type
                        if not isinstance(data[2], int):
                            return 'Cfailure@412 - invalid age data type'

                        #validate the emergency contact type
                        if not isinstance(data[3], str) or len(data[3]) > 64:
                            return 'Cfailure@416 - invalid emergency contact data type/length'
                        
                        #validate the healthcard number type
                        if not isinstance(data[4], int):
                            return 'Cfailure@420 - invalid healthcard number data type'
                        
                        #validate the patient's address
                        if not isinstance(data[5], str) or len(data[5]) > 64:
                            return 'Cfailure@424 - invalid address data type/length'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #make the insertion
                        cursor.execute(
                            """INSERT INTO patients(
                                name,
                                sex,
                                age,
                                emerg_contact,
                                healthcard_no,
                                address
                            ) VALUES (%s, %s, %s, %s, %s, %s)""", 
                            data
                        )

                        #add the patient_id to
                        #the admins patient list
                        cursor.execute("""SELECT LAST_INSERT_ID()""")
                        patient_list.append(cursor.fetchone()[0])
                        cursor.execute("""
                            UPDATE admins SET
                                patients = %s
                            WHERE user_id = %s
                        """, (str(patient_list), user[0]))

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - patient created'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@458 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@462 - invalid data format'

            #detect a medical record act
            elif form['act'] == 'medical_record':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@474 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 4:

                        #validate the patient_id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@485 - invalid patient_id data type'
                        
                        #validate the diagnoses type
                        if not isinstance(data[1], str):
                            return 'Cfailure@489 - invalid diagnoses data type'
                        
                        #validate the med_hist type
                        if not isinstance(data[2], str):
                            return 'Cfailure@493 - invalid med_hist data type'
                        
                        #validate the medication type
                        if not isinstance(data[3], str): 
                            return 'Cfailure@497 - invalid medication data type'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #make the insertion
                        cursor.execute("""INSERT INTO medical_records(
                            patient_id,
                            diagnoses,
                            med_hist,
                            medication
                            ) VALUES (%s, %s, %s, %s)""", 
                            data
                        )

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - created medical record'

                    #detect invalid data format
                    else:
                        return 'Cfailure@523 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@527 - invalid data format'

            #detect an invalid act
            else:
                return 'Cfailure@531 - invalid act'
            
        #detect a retrieval form
        elif form['type'] == 'retrieve':

            #detect an admin act
            if form['act'] == 'admin':

                #return the admin
                return user

            #detect an appointment act
            elif form['act'] == 'appointment':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@552 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@561 - patient not bound to admin'

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 1: 

                        #validate the patient_id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@569 - invalid patient_id data type'

                        #create a cursor
                        cursor = con.cursor()

                        #fetch all appointments for the patient
                        cursor.execute("""SELECT * FROM appointments WHERE patient_id = %s""", (data[0],))

                        #fetch the found appointments
                        appointments = []
                        appointment = cursor.fetchone()
                        while appointment != None:
                            appointment = list(appointment)
                            appointment[4] = f'{appointment[4].time()}'
                            appointment = tuple(appointment)
                            appointments.append(appointment)
                            appointment = cursor.fetchone()

                        #close the cursor
                        cursor.close()

                        #return the appointments 
                        #to the front end
                        return tuple(appointments)

                    #detect invalid data format
                    else:
                        return 'Cfailure@593 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@597 - invalid data format'

            #detect a patient act
            elif form['act'] == 'patient':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@609 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@618 - patient not bound to admin'                

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 1: 

                        #validate the patient_id type
                        if not isinstance(data[0], int):
                            return 'Cfailure@626 - invalid patient_id data type'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #select the patient entry
                        cursor.execute("""SELECT * FROM patients WHERE patient_id = %s""", (data[0],))

                        #fetch the result
                        patient = cursor.fetchone()

                        #close the cursor
                        cursor.close()
                        
                        #return the result
                        return patient
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@645 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@649 - invalid data format'
                    
            #detect a medical record act
            elif form['act'] == 'medical_record':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@661 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@670 - patient not bound to admin'

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 1: 

                        #validate the patient_id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@678 - invalid patient_id data type'

                        #create a cursor
                        cursor = con.cursor()

                        #select the patient's records
                        cursor.execute("""SELECT * FROM medical_records WHERE patient_id = %s""", (data[0],))

                        #fetch the query results
                        records = []
                        record = cursor.fetchone()
                        while record != None:
                            records.append(record)
                            record = cursor.fetchone()

                        #close the cursor
                        cursor.close()

                        #return the appointments 
                        #to the front end
                        return tuple(records)
                        
                    #detect invalid data format
                    else:
                        return 'Cfailure@702 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@706 - invalid data format'

            #detect an invalid act
            else:
                return 'Cfailure@710 - invalid act'
            
        #detect an update form
        elif form['type'] == 'update':

            #detect an admin act
            if form['act'] == 'admin':

                #try to hash the provided password
                try: 
                    form['data'][4] = hashlib.sha256(form['data'][4].encode()).hexdigest()
                except Exception as e:
                    print(e)
                    return 'Cfailure@723 - password hashing failure'

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@732 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 7:

                        #validate the clinic_id type
                        if not isinstance(data[0], int):
                            return 'Cfailure@743 - invalid clinic_id data type'

                        #validate the role type
                        if not isinstance(data[1], str) or len(data[1]) > 64:
                            return 'Cfailure@747 - invalid role data type/length'
         
                        #validate name type
                        if not isinstance(data[2], str) or len(data[2]) > 64:
                            return 'Cfailure@751 - invalid name data type/length'

                        #validate email type
                        if not isinstance(data[3], str) or len(data[3]) > 64:
                            return 'Cfailure@755 - invalid email data type/length'
                        
                        #validate password type
                        if not isinstance(data[4], str) or len(data[4]) > 64:
                            return 'Cfailure@759 - invalid password data type/length'
                        
                        #validate patients type
                        if not isinstance(data[5], str):
                            return 'Cfailure@763 - invalid patients data type'
                        
                        #validate user_id type
                        if not isinstance(data[6], int) or user[0] != data[6]:
                            return 'Cfailure@767 - invalid user_id type/value'
                
                        #create a cursor
                        cursor = con.cursor()

                        #check if the provided email
                        #is already in use
                        if data[3] != user[4]:
                            if not vacant(data[3], cursor):
                                return 'Cfailure@775 - provided email already in use'
                        
                        #update the admin
                        cursor.execute("""     
                            UPDATE admins SET
                            clinic_id = %s, 
                            role = %s, 
                            name = %s, 
                            email = %s, 
                            password = %s, 
                            patients = %s
                            WHERE user_id = %s""", 
                            data
                        )

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - admin updated'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@798 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@801 - invalid data format'

            #detect an appointment act
            elif form['act'] == 'appointment':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@814 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@823 - patient not bound to admin'

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 5:

                        #validate the patient id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@831 - invalid patient_id data type'
                        
                        #validate the appt type type
                        if not isinstance(data[1], str) or len(data[1]) > 64:
                            return 'Cfailure@835 - invalid appt_type data type/length'
                        
                        #validate the appt status type
                        if not isinstance(data[2], str) or len(data[2]) > 16:
                            return 'Cfailure@839 - invalid appt_status data type/length'
                        
                        #validate the appt datetime
                        if not validDatetime(data[3]):
                            return 'Cfailure@843 - invalid appt_date format, expected YYYY-MM-DD-Hrs-Min'
                        
                        #validate the appt_id type
                        if not isinstance(data[4], int):
                            return 'Cfailure@847 - invalid appt_id data type'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #update the appointment
                        cursor.execute("""     
                            UPDATE appointments SET
                            patient_id = %s, 
                            appt_type = %s, 
                            appt_status = %s, 
                            appt_datetime = %s
                            WHERE appt_id = %s""", 
                            data
                        )

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front
                        return 'success - appointment updated'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@874 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@878 - invalid data format'

            #detect a patient act
            elif form['act'] == 'patient':

                #try to package the 
                #recieved form data
                data = None
                try: 
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@890 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 7:

                        #check that the provided 
                        #patient id is contained within
                        #the admin's patient list
                        if data[6] not in patient_list:
                            return 'Cfailure@899 - patient not bound to admin'

                        #validate the patient name type
                        if not isinstance(data[0], str) or len(data[0]) > 64:
                            return 'Cfailure@907 - invalid patient_name data type/length'
                        
                        #validate the sex type
                        if not isinstance(data[1], str) or len(data[1]) > 1:
                            return 'Cfailure@911 - invalid sex data type/length'
                        
                        #validate the age type
                        if not isinstance(data[2], int):
                            return 'Cfailure@915 - invalid age data type'

                        #validate the emergency contact type
                        if not isinstance(data[3], str) or len(data[3]) > 64:
                            return 'Cfailure@919 - invalid emergency contact data type/length'
                        
                        #validate the healthcard number type
                        if not isinstance(data[4], int):
                            return 'Cfailure@923 - invalid healthcard number data type'
                        
                        #validate the patient's address
                        if not isinstance(data[5], str) or len(data[5]) > 64:
                            return 'Cfailure@927 - invalid address data type/length'
                        
                        #validate the patient_id
                        if not isinstance(data[6], int):
                            return 'Cfailure@931 - invalid patient_id data type'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #make the update
                        cursor.execute("""
                            UPDATE patients SET
                            name = %s,
                            sex = %s,
                            age = %s,
                            emerg_contact = %s,
                            healthcard_no = %s,
                            address = %s
                            WHERE patient_id = %s""", 
                            data
                        )

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - patient updated'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@960 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@964 - invalid data format'

            #detect a medical record act
            elif form['act'] == 'medical_record':

                #try to package the
                #recieved form data
                data = None
                try:
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@976 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 5:

                        #validate the patient_id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@987 - invalid patient_id data type'
                        
                        #validate the diagnoses type
                        if not isinstance(data[1], str):
                            return 'Cfailure@991 - invalid diagnoses data type'
                        
                        #validate the med_hist type
                        if not isinstance(data[2], str):
                            return 'Cfailure@995 - invalid med_hist data type'
                        
                        #validate the medication type
                        if not isinstance(data[3], str): 
                            return 'Cfailure@999 - invalid medication data type'
                        
                        #validate the record_id
                        if not isinstance(data[4], int):
                            return 'Cfailure@1003 - invalid record_id data type'
                        
                        #create a cursor
                        cursor = con.cursor()

                        #make the insertion
                        cursor.execute(
                            """UPDATE medical_records SET
                            patient_id = %s,
                            diagnoses = %s,
                            med_hist = %s,
                            medication = %s
                            WHERE record_id = %s""", 
                            data
                        )

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - updated medical record'

                    #detect invalid data format
                    else:
                        return 'Cfailure@1030 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@1034 - invalid data format'

            #detect an invalid act
            else:
                return 'Cfailure@1038 - invalid act'
            
        #detect a delete form
        elif form['type'] == 'delete':

            #detect an admin act
            if form['act'] == 'admin':

                #end the admin's session
                sessions.remove(str(user[0]))

                #create a cursor
                cursor = con.cursor()

                #delete their entry from the
                #admins table
                cursor.execute("""DELETE FROM admins WHERE user_id = %s""", (user[0],))

                #close the cursor
                cursor.close()

                #commit the changes
                con.commit()

                #report to the front end
                return 'success - admin deleted'

            #detect an appointment act
            elif form['act'] == 'appointment':

                #try to package the 
                #recieved form data
                data = None
                try:
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@1075 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@1084 - patient not bound to admin'

                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 2:

                        #validate the appt_id type
                        if not isinstance(data[1], int):
                            return 'Cfailure@1092 - invalid appt_id data type'                                 

                        #create a cursor
                        cursor = con.cursor()

                        #delete the appointment
                        cursor.execute("""DELETE FROM appointments WHERE appt_id = %s""", (data[1]))

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()
                    
                        #report to the front end
                        return 'success - deleted appointment'
                    
                    #detect invalid data format
                    else:
                        return 'Cfailure@1111 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@1115 - invalid data format'

            #detect a patient act
            elif form['act'] == 'patient':

                #try to package the 
                #recieved form data
                data = None
                try:
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@1127 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@1136 - patient not bound to admin'
                    
                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 1:

                        #validate the patient_id type
                        if not isinstance(data[0], int) or notin('patient_id', data[0], 'patients', con):
                            return 'Cfailure@1144 - invalid patient_id data type'
                    
                        #create a cursor
                        cursor = con.cursor()

                        #delete the patient
                        cursor.execute("""DELETE FROM patients WHERE patient_id = %s""", (data[0],))

                        #update the admin's patient list
                        patient_list.remove(data[0])
                        cursor.execute("""UPDATE admins SET patients = %s WHERE user_id = %s""", (str(patient_list), user[0]))

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end
                        return 'success - deleted patient'

                    #detect invalid data format
                    else:
                        return 'Cfailure@1163 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@1167 - invalid data format'

            #detect a medical record act
            elif form['act'] == 'medical_record':

                #try to package the 
                #recieved form data
                data = None
                try:
                    data = tuple(form['data'])
                except Exception as e:
                    print(e)
                    return 'Cfailure@1179 - packaging failure'
                
                #handle the recieved data
                if data != None:

                    #check that the provided 
                    #patient id is contained within
                    #the admin's patient list
                    if data[0] not in patient_list:
                        return 'Cfailure@1188 - patient not bound to admin'
                    
                    #check that the proper number
                    #of parameters have been sent
                    if len(data) == 2:

                        #validate the record_id
                        if not isinstance(data[1], int):
                            return 'Cfailure@1196 - invalid record_id data type'

                        #create a cursor
                        cursor = con.cursor()

                        #delete the record
                        cursor.execute(""""DELETE FROM medical_records WHERE record_id = %s""", (data[1],))

                        #close the cursor
                        cursor.close()

                        #commit the changes
                        con.commit()

                        #report to the front end                
                        return 'success - deleted record'
                
                    #detect invalid data format
                    else:
                        return 'Cfailure@1215 - invalid data format'
                    
                #detect invalid data format
                else:
                    return 'Cfailure@1219 - invalid data format'

            #detect an invalid act
            else:
                return 'Cfailure1223 - invalid act'
            
        #detect an invalid type
        else:
            return 'Cfailure1227 - invalid type'

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
    cursor.execute('SELECT * FROM admins WHERE email = %s', (username,))

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