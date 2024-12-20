import interpreter

while True:
    text = input('LCMD >')
    result, error = interpreter.run('<stdin>', text)

    if error: print(error.as_string())
    else: print(result)