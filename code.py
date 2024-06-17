# example_code.py

import math

class Circle:
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return math.pi * (self.radius ** 2)

    def circumference(self):
        return 2 * math.pi * self.radius

def find_largest_circle(circles):
    largest = None
    for circle in circles:
        if largest is None or circle.area() > largest.area():
            largest = circle
    return largest

def duplicated_function():
    return "This is a duplicated function."

def duplicated_function():
    return "This is a duplicated function."
