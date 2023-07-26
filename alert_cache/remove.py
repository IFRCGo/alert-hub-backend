with open('models.py', 'r', encoding='utf-16') as file:
    line = file.readlines()
    for l in line:
        l.replace(chr(0), '')
        print(l)