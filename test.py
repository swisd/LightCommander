class MyClass:
    def __init__(self, value):
        self.instance_value = value

    def print_value(self):
        print(f"Instance value: {self.instance_value} {self}")

# Create an instance of MyClass
my_instance = MyClass(10)

# 'my_instance' now holds a reference to the object (the 'self' of that instance)
# You can now use 'my_instance' to access its attributes and call its methods
my_instance.print_value()

# You can also assign 'my_instance' to another variable
another_variable = my_instance
another_variable.print_value()