def parse(data):
    special_chars  = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!','@','\\']
    data = str(data)
    res = ''
    for char in data:
        if char in special_chars:
            res += '\\'
        res += char
    
    return res
        

