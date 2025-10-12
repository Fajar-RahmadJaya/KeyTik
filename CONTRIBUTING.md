# Contributing to KeyTik

Pull requests are welcome!
We welcome contributions of all kinds, including bug fixes, features, improvements, documentation improvement and more. 

## Setting up Workplace
1. Download and install Python on your machine.
2. Clone the repository.
4. Install requirements with ```pip install -r requirements.txt```

## Folder Structures
All code is stored inside the src folder.
```
src/    ; Source Floder
    ├── _internal/    ; Data Folder
    ├── logic/
        └── logic.py
    ├── ui/
        ├── edit_script/
            ├── choose_key.py
            ├── edit_frame_row.py
            ├── edit_script_logic.py
            ├── edit_script_main.py
            ├── parse_script.py
            ├── select_device.py
            ├── select_program.py
            └── write_script.py
        ├── setting.py
        └── welcome.py
    ├── utility/ 
        ├── constant.py
        ├── icon.py
        └── utils.py
    └── main.py    ; Initialization Code
```

## License
By contributing, you agree that your contributions will be licensed under the terms of the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).
