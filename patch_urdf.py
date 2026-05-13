import numpy as np

res_mj = np.zeros((10, 6, 3))
res_dk = np.ones((10, 6, 3)) * 0.6467

diff = res_mj - res_dk
rmse = np.sqrt(np.mean(diff**2, axis=0))
max_rmse = np.max(np.linalg.norm(rmse, axis=1))

print(max_rmse)
