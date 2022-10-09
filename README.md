SHCI-SCF module for PySCF
=========================

2021-06-22

* Version 0.1

Install
-------
* Install to python site-packages folder
```bash
pip install git+https://github.com/pyscf/shciscf
```

* Install in a custom folder for development
```bash
git clone https://github.com/pyscf/shciscf /home/abc/local/path

C_INCLUDE_PATH=$C_INCLUDE_PATH:/path_to_pyscf/pyscf/pyscf/lib/build/ python -m pip install .

# Set pyscf extended module path
echo 'export PYSCF_EXT_PATH=/home/abc/local/path:$PYSCF_EXT_PATH' >> ~/.bashrc

# Setup settings file
cp shciscf/pyscf/shciscf/settings.py.example shciscf/pyscf/shciscf/settings.py
```

* Modify `shciscf/pyscf/shciscf/settings.py`

```python
SHCIEXE = "/your_path_to_Dice/Dice/Dice"
SHCISCRATCHDIR = "/path_your_tmp_dir"
SHCILIB = "/your_path_to_shciscf/shciscf/pyscf/shciscf/libSHCITools.so" 

```


You can find more details of extended modules in the document
[extension modules](https://pyscf.org/install.html#extension-modules)


