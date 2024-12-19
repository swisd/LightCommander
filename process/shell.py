import basic
import os

print("CubicIV Shell")
print("PyRUN v3")
print("Stable 1.5.2")
print("CS: 0x0616")
while True:
    text = input('->')
    if text.strip() == '':
        continue
    if text[0] == "#":
        continue
    result, error = basic.run('<stdin>', text)

    if error:
        print((error.as_string()))
    else:
        if len(result.elements) == 1:
            print(repr(result.elements[0]))
        else:
            print(repr(result))

