import numpy as np
import pandas as pd

x_zones = 120
y_zones = 80
dummy_xT_grid = np.zeros((y_zones, x_zones))

for x in range(x_zones):
    dummy_xT_grid[:, x] = (x / x_zones) ** 3 * 0.1

pd.DataFrame(dummy_xT_grid).to_csv("./data/xT_grid.csv", header=False, index=False)
print("xT_grid.csv created successfully.")