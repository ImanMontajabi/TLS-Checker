# TLS Checker 🚬
TLS Checker is a Python script for checking the Transport Layer Security (TLS) version and security settings of a list of websites. The script uses multithreading to speed up the process of checking a large number of websites.

:paperclip:  [نمونه خروجی آماده‌ی استفاده](https://github.com/ImanMontajabi/TLS-Checker/blob/master/result.json)

:package:  حجم فایل‌ها تقریبا 33mb است.



# Installation
To use TLS Checker, you will need Python 3.7 or later. You can download Python from the official website: https://www.python.org/downloads/

# Usage
- Download or clone the repository to your local machine.<br>
- Open a terminal and navigate to the directory containing the script.<br>
- Run the script with the following command:

first:
```
pip install -r requirements.txt
```
then:
```
python tls-checker.py
```

- The script will prompt you for the name of the CSV file containing the list of websites you want to check. The CSV file should contain one website per row, with no headers.
- The script will then prompt you for the number of websites you want to check. This number should be between 1 and the total number of websites in the CSV file.
- The script will then prompt you for the iso-code of server location (Iran = IR, Germany = DE,....)
- You can leave this field blank and just press "Enter"
- Guide: https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
- The script will then begin checking the websites and print the results to the console.
- The script will also create a JSON file named "result.json" in the same directory as the script. This file will contain the results of the website checks.
- CSV files sources: [here](https://www.domcop.com/top-10-million-websites) and [here](https://tranco-list.eu/)

# Screenshot

![Screenshot (92)](https://github.com/ImanMontajabi/TLS-Checker/assets/52942515/fd776019-d08c-4509-a5e8-5ee8d3abe202)

# video

- The following tutorial video can be a good guide for using this script:

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/QNbeYkGIiA4/0.jpg)](https://youtu.be/QNbeYkGIiA4)


# License
TLS Checker is licensed under the MIT License. See [LICENSE](https://github.com/ImanMontajabi/TLS-Checker/blob/master/LICENSE) for [more information](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).


