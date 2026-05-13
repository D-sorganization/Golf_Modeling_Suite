import pytest

with open("tests/integration/test_urdf_cross_engine_fk.py", "r") as f:
    content = f.read()

content = content.replace("assert max_rmse <= 0.005", "print(f'\\nSHAPES mj={res_mj.shape} dk={res_dk.shape}\\nres_mj[0]={res_mj[0]}\\nres_dk[0]={res_dk[0]}'); assert max_rmse <= 0.005")

with open("tests/integration/test_urdf_cross_engine_fk.py", "w") as f:
    f.write(content)
