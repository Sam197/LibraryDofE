import pyodbc
import time
import datetime

conn = pyodbc.connect('Driver={SQL Server};'
                      r'Server=SJHELLOMSI\TEW_SQLEXPRESS;'
                      'Database=Books;'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

charMaxLength = 100
maxLoanLength = 10
maxBooksPerChild = 1

def read_data_base(toRead):
    cursor.execute(f'SELECT * FROM {toRead}')
    lis = {}
    for row in cursor:
        row1 = []
        for element in row:
            if isinstance(element, str):
                row1.append(element.strip())
            else:
                row1.append(element)
        lis[row[0]] = row1
        del row1
    return lis

def getBarcode():
    return int(input("Barcode? \n"))

def add_book():
    exe = True
    barcode = getBarcode()
    bName = input("BName? \n")
    aName = input("AName? \n")
    if len(bName) >= charMaxLength:
        print(f"Book name exceeds maximum lenght of {charMaxLength} characters")
        exe = False
    if len(bName) >= charMaxLength:
        print(f"Author name exceeds maximum lenght of {charMaxLength} characters")
        exe = False
    if exe:
        cursor.execute(f"INSERT INTO dbo.book (Book_Barcode, Book_Name, Book_Author, Book_On_Loan) VALUES ('{barcode}', '{bName}', '{aName}', 0)")
        conn.commit()

def get_bookid(barcode):
    barcode = str(barcode)
    bookid = None
    for row in books.values():
        if row[1] == barcode:
            bookid = row[0]
            break
    return bookid

def get_childid(child_name):
    child_name = child_name.split()
    child_id = None
    for row in children.values():
        if row[1] == child_name[0] and row[2] == child_name[1]:
            child_id = row[0]
            break
    if child_id == None:
        return None
    return child_id

def take_out_book(barcode, child_name):
    bookid = None
    bookid = get_bookid(barcode)
    if child_name.isdigit():
        child_id = child_name
    else:
        child_id = get_childid(child_name)
            
    if books[bookid][4]:
        print("Book already on loan")
        return f"Book (id{bookid}) is already on loan"

    if children[child_id][4] >= maxBooksPerChild:
        print("Child already has book on loan")
        return f"Child ({children[child_id][1]} {children[child_id][2]}) already has {children[child_id][4]} books on loan"
    
    if children[child_id][4] < maxBooksPerChild and not books[bookid][4]:
        books[bookid][4] = True
        cursor.execute(f"UPDATE Book SET Book_On_Loan = 1 WHERE Book_id = {bookid}")
        children[child_id][4] += 1
        cursor.execute(f"UPDATE Child SET Has_Book = {children[child_id][4]} WHERE Child_id = {child_id}")
        cursor.execute(f"INSERT INTO dbo.Book_History1 (Book_id, Child_id, Date_Borrowed, Max_Loan_Length, Date_Returned) VALUES ({bookid}, {child_id}, '{str(datetime.date.today())}', {maxLoanLength}, Null)")
        conn.commit()
    return None

def return_book():
    barcode = getBarcode()
    child_id = None
    if barcode == None:
        bookid = input("Book id? \n")
    else:
        bookid = get_bookid(barcode)

    for row in book_history.values():
        if row[5] == None and row[1] == bookid:
            child_id = row[2]
            break

    if books[bookid][4]:
        loanid = None
        books[bookid][4] = False
        cursor.execute(f"UPDATE Book SET Book_On_Loan = 0 WHERE Book_id = {bookid}")
        for row in book_history.values():
            if row[5] == None and row[1] == bookid and row[2] == child_id:
                loanid = row[0]
                break
        children[child_id][4] -= 1
        cursor.execute(f"UPDATE Book_History1 SET Date_Returned = '{str(datetime.date.today())}' WHERE Loan_id = {loanid} ")
        cursor.execute(f"UPDATE Child SET Has_Book = {children[child_id][4]} WHERE Child_id = {child_id}")
        conn.commit()   
    else:
        print("Book not currently on loan")
    

def test():
    cursor.execute(f"INSERT INTO dbo.Book_History1 (Book_id, Child_id, Date_Borrowed, Max_Loan_Length, Date_Returned) VALUES (1, 2, '{str(datetime.date.today())}', 10, Null)")
    conn.commit()
    
def add_child(c_first_name, c_last_name, c_year):
    # c_first_name = input("First name? \n")
    # c_last_name = input("Last name? \n")
    # c_year = input("Year? \n")
    if c_year == "":
        c_year = None
    else:
        c_year = int(c_year)
    cursor.execute(f"INSERT INTO dbo.Child (Child_First_Name, Child_Last_Name, Child_Year, Has_Book) VALUES ('{c_first_name}', '{c_last_name}', {c_year}, 0)")
    conn.commit()

def child_loan_history(name):
    if name.isdigit():
        child_id = name
    else:
        child_id = get_childid(name)
    if child_id == None:
        return "No Child"
    cursor.execute(f"SELECT * FROM dbo.Book_History1 WHERE Child_id = {child_id}")
    pl = []
    for row in cursor: pl.append(row)
    return pl

def check_late_books():
    for row in book_history.values():
        if row[5] != None or row[4] == None:
            continue
        max_loan = row[4]
        b_date = datetime.datetime.strptime(row[3][2:], r'%y-%m-%d')
        r_date = b_date + datetime.timedelta(days = max_loan)
        if r_date < datetime.datetime.strptime(str(datetime.date.today())[2:], r'%y-%m-%d'):
            print(f"{children[row[2]][1]} {children[row[2]][2]} has not returned book ({books[row[1]][2]}) on time")

def find_book(barcode):
    book_id = get_bookid(barcode)
    for row in book_history.values():
        if row[5] != None:
            continue
        if row[1] == book_id:
            return f"{children[row[2]][1]} {children[row[2]][2]} has book"
