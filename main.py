import pyodbc
import pandas as pd
from tkinter import *
import time
import datetime

conn = pyodbc.connect('Driver={SQL Server};'
                      r'Server=SJHELLOMSI\TEW_SQLEXPRESS;'
                      'Database=Books;'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

XWidth = 750
YHeight = 500

charMaxLength = 100
maxLoanLength = 10

root = Tk()
root.geometry(f"{XWidth}x{YHeight}")
root.resizable(width = False, height = False)
#mainBox = Text(root)
# mainBox.place(x = 0, y = 0, width = XWidth, height = YHeight)

# def add_to_log(text):
#     mainBox.config(state = NORMAL)
#     mainBox.insert(END, text + '\n')
#     mainBox.config(font = ('Arial', 16))
#     mainBox.config(state = DISABLED)

#add_to_log("Hello")

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
    for row in books.values():
        if row[1] == barcode:
            bookid = row[0]
            break
    return bookid

def get_childid(child_name):
    child_name = child_name.split()
    for row in children.values():
        if row[1] == child_name[0] and row[2] == child_name[1]:
            child_id = row[0]
            break
    return child_id

def take_out_book():
    ballow = False
    callow = False
    barcode = getBarcode()
    bookid = None
    if barcode == None:
        bookid = input("Book id? \n")
    else:
        bookid = get_bookid(barcode)

    child_name = input("Name? \n")
    if child_name.isdigit():
        child_id = child_name
    else:
        child_id = get_childid(child_name)
            
    if books[bookid][4]:
        print("Book already on loan")
        raise Exception("I needed to stop the program here", "Book already on loan")

    if children[child_id][4]:
        print("Child already has book on loan")
        raise Exception("STOP THE PROGRAM")

    if not children[child_id][4]:
        children[child_id][4] = True
        cursor.execute(f"UPDATE Child SET Has_Book = 1 WHERE Child_id = {child_id}")
        conn.commit()

    if not books[bookid][4]:
        books[bookid][4] = True
        cursor.execute(f"UPDATE Book SET Book_On_Loan = 1 WHERE Book_id = {bookid}")
        conn.commit()
    
    cursor.execute(f"INSERT INTO dbo.Book_History1 (Book_id, Child_id, Date_Borrowed, Max_Loan_Length, Date_Returned) VALUES ({bookid}, {child_id}, '{str(datetime.date.today())}', {maxLoanLength}, Null)")
    conn.commit()

def return_book():
    barcode = getBarcode()
    if barcode == None:
        bookid = input("Book id? \n")
    else:
        bookid = get_bookid(barcode)

    for row in book_hisory.values():
        if row[5] == None and row[1] == bookid:
            child_id = row[2]
            break

    if books[bookid][4]:
        books[bookid][4] = False
        cursor.execute(f"UPDATE Book SET Book_On_Loan = 0 WHERE Book_id = {bookid}")
        for row in book_hisory.values():
            if row[5] == None and row[1] == bookid and row[2] == child_id:
                loanid = row[0]
                break
        cursor.execute(f"UPDATE Book_History1 SET Date_Returned = '{str(datetime.date.today())}' WHERE Loan_id = {loanid} ")
        cursor.execute(f"UPDATE Child SET Has_Book = 0 WHERE Child_id = {child_id}")
        conn.commit()   
    else:
        print("Book not currently on loan")
    

def test():
    cursor.execute(f"INSERT INTO dbo.Book_History1 (Book_id, Child_id, Date_Borrowed, Max_Loan_Length, Date_Returned) VALUES (1, 2, '{str(datetime.date.today())}', 10, Null)")
    conn.commit()
    
def add_child():
    c_first_name = input("First name? \n")
    c_last_name = input("Last name? \n")
    c_year = input("Year? \n")
    if c_year == "":
        c_year = None
    else:
        c_year = int(c_year)
    cursor.execute(f"INSERT INTO dbo.Child (Child_First_Name, Child_Last_Name, Child_Year, Has_Book) VALUES ('{c_first_name}', '{c_last_name}', {c_year}, 0)")
    conn.commit()

books = read_data_base('dbo.Book')
children = read_data_base('dbo.Child')
book_hisory = read_data_base('dbo.Book_History1')

print(books)
#print(children)
#print(book_hisory)
#take_out_book()
#return_book()
#print(str(datetime.date.today()))
#add_book()
#add_child()
#test()

add_child_btn = Button(root, text = "Add Child", command = add_child)
add_child_btn.place(x = 0, y = 0)
add_book_btn = Button(root, text = "Add Book", command = add_book)
add_book_btn.place(x = 0, y = 30)
take_out_book_btn = Button(root, text = "Borrow Book", command = take_out_book)
take_out_book_btn.place(x = 0, y = 60)
return_book_btn = Button(root, text = "Return Book", command = return_book)
return_book_btn.place(x = 0, y = 90)
root.mainloop()