class A:
    x = list()
    y = 0

    def __init__(self, x, y):
        self.x.append(x)
        y = 0


a1 = A(5, 5)
a1_copy = a1

a1 = A(7, 7)
print(a1_copy.x)
print(a1.x)

