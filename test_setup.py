import csv
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


print("Python environment works")
print("NumPy:", np.__version__)
print("Pandas:", pd.__version__)

x = np.array([[1], [2], [3]])
y = np.array([2, 4, 6])

model = LinearRegression()
model.fit(x, y)

print("Scikit-learn works")
print("Prediction for 4:", model.predict([[4]])[0])

print("Setup successful")