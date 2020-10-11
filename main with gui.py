import pyodbc
import pandas as pd
from tkinter import *
from tkinter import messagebox
import time
import datetime
import pickle
import threading
#from base_funcs import *

conn = pyodbc.connect('Driver={SQL Server};'
                      r'Server=SJHELLOMSI\TEW_SQLEXPRESS;'
                      'Database=Books;'
                      'Trusted_Connection=yes;')
cursor = conn.cursor()

XWidth = 750
YHeight = 500

charMaxLength = 100
maxLoanLength = 10
maxBooksPerChild = 1

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

books = read_data_base('dbo.Book')
children = read_data_base('dbo.Child')
book_history = read_data_base('dbo.Book_History1')


#print(book_history)
check_late_books()
print(find_book("333"))
#print(child_loan_history("Sam Jones"))
#print(books)
#print(children)
#print(book_history)
#take_out_book()
#return_book()
#print(str(datetime.date.today()))
#add_book()
#add_child()
#test()

def add_child_com():
    root2 = Tk()
    root2.geometry("150x200")
    #root2.resizable(height = False, width = False)
    top_lbl = Label(root2, text = "Add Child")
    top_lbl.grid(column = 0, row = 0)
    cfname_lbl = Label(root2, text = "First Name")
    cfname_lbl.grid(column = 0, row = 1) 
    cfname_en = Entry(root2)
    cfname_en.grid(column = 0, row = 2)
    clname_lbl = Label(root2, text = "Last Name")
    clname_lbl.grid(column = 0, row = 3)
    clname_en = Entry(root2)
    clname_en.grid(column = 0, row = 4)
    cyear_lbl = Label(root2, text = "Year Group")
    cyear_lbl.grid(column = 0, row = 5)
    cyear_en = Entry(root2)
    cyear_en.grid(column = 0, row = 6)
    def getValues():
        cFirstName = cfname_en.get()
        cLastName = clname_en.get()
        cYear = cyear_en.get()
        try:
            add_child(cFirstName, cLastName, cYear)
            root2.destroy()
        except:
            messagebox.showerror("Nope", "Nah")
    add_btn = Button(root2, text = "Add Child", command = getValues)
    add_btn.grid(column = 0, row = 7)
    root2.mainloop()

def take_out_book_com():
    root2 = Tk()
    root2.geometry("150x200")
    root2.resizable(height = False, width = False)
    top_lbl = Label(root2, text = "Take out Book")
    top_lbl.grid(column = 0, row = 0)
    book_barcode_lbl = Label(root2, text = "Book Barcode")
    book_barcode_lbl.grid(column = 0, row = 1)
    book_barcode_en = Entry(root2)
    book_barcode_en.grid(column = 0, row = 2)
    child_name_lbl = Label(root2, text = "Child Name")
    child_name_lbl.grid(column = 0, row = 3)
    child_name_en = Entry(root2)
    child_name_en.grid(column = 0, row = 4)
    def getValues():
        book_barc = book_barcode_en.get()
        child_name = child_name_en.get()
        res = take_out_book(book_barc, child_name)
        if res == None:
            root2.destroy()
        else:
            messagebox.showerror("Error", res)
    borrow_btn = Button(root2, text = "Borrow", command = getValues)
    borrow_btn.grid(column = 0, row = 5)
    root2.mainloop()


add_child_btn = Button(root, text = "Add Child", command = add_child_com)
add_child_btn.place(x = 0, y = 0)
add_book_btn = Button(root, text = "Add Book", command = add_book)
add_book_btn.place(x = 0, y = 30)
take_out_book_btn = Button(root, text = "Borrow Book", command = take_out_book_com)
take_out_book_btn.place(x = 0, y = 60)
return_book_btn = Button(root, text = "Return Book", command = return_book)
return_book_btn.place(x = 0, y = 90)

def refresh():
    global books
    del books
    books = read_data_base('dbo.book')
    print(books)

refresh_btn = Button(root, text = "Refresh", command = refresh)
refresh_btn.place(x = 0, y = 120)

search_entryb = Entry(root)
search_entryb.place(x = 200, y = 10, width = 100)
search_resultsb = Text(root, state = DISABLED)
search_resultsb.place(x = 200, y = 50, height = 100, width = 250)

search_entryc = Entry(root)
search_entryc.place(x = 200, y = 170, width = 100)
search_resultsc = Text(root, state = DISABLED)
search_resultsc.place(x = 200, y = 210, height = 100, width = 250)
 
def add_to_log(msg, tbox):
    tbox.config(state = NORMAL)
    tbox.insert(END, str(msg) + '\n')
    tbox.config(state = DISABLED)

def testfunc(event):
    print(search_resultsc.get(1.0, 2.0))

def search():
    search_things = ([search_entryb, search_resultsb, "", "B", None, 1], [search_entryc, search_resultsc, "", "C", True, 1])
    for search in search_things:
        search[1].tag_config("Highlight", background = 'light blue')

    def new_highlight(cur_pair):
        if cur_pair == "C":
            search_resultsc.tag_remove("Highlight", 1.0, END)
            search_resultsc.tag_add("Highlight", f"{search_things[1][5]}.0", f"{search_things[1][5] + 1}.0")
        elif cur_pair == "B":
            search_resultsb.tag_remove("Highlight", 1.0, END)
            search_resultsb.tag_add("Highlight", f"{search_things[0][5]}.0", f"{search_things[0][5] + 1}.0")

    def child_upA(event):
        search_things[1][5] -= 1
        new_highlight("C")
    
    def child_downA(event):
        search_things[1][5] += 1
        new_highlight("C")

    def book_upA(event):
        search_things[0][5] -= 1
        new_highlight("B")
    
    def book_downA(event):
        search_things[0][5] += 1
        new_highlight("B")

    def getBook(event):
        try:
            print(search_resultsb.get(f"{search_things[0][5]}.0", f"{search_things[0][5] + 1}.0").split()[0][:-1])
        except IndexError:
            print("No selection")

    def getChild(event):
        try:
            print(search_resultsc.get(f"{search_things[1][5]}.0", f"{search_things[1][5] + 1}.0").split()[0][:-1])
        except IndexError:
            print("No selection")

    search_entryb.bind('<Up>', book_upA)
    search_entryb.bind('<Down>', book_downA)
    search_entryb.bind('<Return>', getBook)
    search_entryc.bind('<Up>', child_upA)
    search_entryc.bind('<Down>', child_downA)
    search_entryc.bind('<Return>',getChild)

    while running:
        for search in search_things:
            phrase = search[0].get().upper()
            if search[2] == phrase:
                continue
            if phrase == " ":
                continue
            search[2] = phrase
            search[1].config(state = NORMAL)
            search[1].delete(1.0, END)
            search[1].config(state = DISABLED)
            if search[3] == "B":
                table = books
            elif search[3] == "C":
                table = children
            added = 0
            for i in table.values():
                if search[4]:
                    to_check = f"{i[0]}| {i[1]} {i[2]}"
                else:
                    to_check = f"{i[0]}| {i[2]}"
                if phrase in to_check.upper():
                    search[5] = 1
                    add_to_log(to_check, search[1])
                    added += 1
            # if search[5] > added:
            #     search[5] = added
            # if search[5] <= 0:
            #     search[5] = 0
            if added == 0:
                search[1].tag_remove("Highlight", 1.0, END)
            else:
                search[1].tag_add("Highlight", f"{search[5]}.0", f"{search[5] + 1}.0")
        search_resultsb.see(f"{search_things[0][5]}.0")
        search_resultsc.see(f"{search_things[1][5]}.0")

running = True
search_thread = threading.Thread(target = search)
search_thread.start()

root.mainloop()
running = False