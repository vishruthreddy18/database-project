from django.db import connection

def insert_row(table_name, row_values):
    insert_str = "insert into {} values(".format(table_name)
    for ele in row_values:
        if ele == "NULL":
            insert_str += "NULL, "
        elif type(ele) == str:
            insert_str += "'{}', ".format(ele)
        else:
            insert_str += "{}, ".format(ele)
    
    insert_str = insert_str.rsplit(',', 1)[0]
    insert_str += ");"

    return run_query(insert_str)

def update_where(table_name, set_str, where_str=""):
    update_str = "update {} set {} ".format(table_name, set_str)
    if where_str != "":
        update_str += "where {}".format(where_str)
    return run_query(update_str)

def select_where(table_name, where_str = "", cols=[]):
    select_str = "select "
    if len(cols) == 0:
        select_str += "* "
    else:
        for coloumn_name in cols:
            select_str += "{}, ".format(coloumn_name)
        select_str = select_str.rsplit(',', 1)[0]
    
    select_str += "from {} ".format(table_name)
    if where_str != "":
        select_str += "where {};".format(where_str)

    return run_query(select_str)

def del_where(table_name, where_str = ""):
    delete_str = "delete from {}".format(table_name)
    if where_str != "":
        delete_str += " where {}".format(where_str)
    
    return run_query(delete_str)

def dict_fetch(cursor):
    cursor_desc = cursor.description
    items = cursor.fetchall()
    if len(items) == 0:
        return []
    columns = [col[0] for col in cursor_desc]
    return [
        dict(zip(columns, row))
        for row in items
    ]

def get_unique_id(table_name, key):
    for i in range(1, 100):
        if len(select_where(table_name, "{} = {}".format(key, i))) == 0:
            return i
    return -1


def run_query(query_str):
    print(query_str)
    res = None
    with connection.cursor() as cursor:
            cursor.execute(query_str)
            if query_str.split(' ', 1)[0] == "select":
                res = dict_fetch(cursor)
    return res
