# TLS Checker 🌐

TLS Checker is a Python script for checking the Transport Layer Security (TLS) version and security settings of a list of websites. The script uses multithreading to speed up the process of checking a large number of websites.


:paperclip:  [نمونه خروجی آماده‌ی استفاده](https://github.com/ImanMontajabi/TLS-Checker/blob/master/result.json)


:package:  حجم فایل‌ها تقریبا 33mb است.:warning:


📌 [رفع مشکل pip](https://camelcase.ir/pip-in-cmd/)


🐍 [رفع مشکل python](https://sabzdanesh.com/set-python-path/)

🚧 در ویندوز ترجیحا از [این نسخه‌ی پاورشل](https://github.com/PowerShell/PowerShell) به همراه [این برنامه‌ی ترمینال](https://github.com/microsoft/terminal) استفاده کنید 🙂
<details dir="rtl">
 <summary>
  ❌ رفع مشکل کار نکردن برنامه در MacOS
 </summary>
 <br>
  در حالت عادی برنامه هیچ دامنه ای رو اسکن نمیکنه و بعد از چند ثانیه اسکن بدون هیچ نتیجه ای تموم میشه که دلیلش لود نشدن لایبرری های ssl هست. برای حل این مشکل کافیه دستور زیر رو داخل ترمینال وارد کنید و دوباره اسکریپت رو اجرا کنید :

```bash
ln -s /etc/ssl/* /Library/Frameworks/Python.framework/Versions/Current/etc/openssl
```
 </details>

# Installation
To use TLS Checker, you will need Python 3.7 or later. You can download Python from the official website: 

https://www.python.org/downloads/

☑️ هنگام نصب پایتون گزینه‌ی **set python ... to PATH** فعال باشد.


# Usage
- Download or clone the repository to your local machine.<br>
- Open a terminal and navigate to the directory containing the script.<br>
- Run the script with the following command:


برای اجرا، در محل فایل های برنامه از دستور زیر استفاده کنید:


```
python tls-checker.py
```


 :moyai: ترجیحا موقع اجرا فیلترشکن خاموش باشد.

- The script will prompt you for the name of the CSV file containing the list of websites you want to check. The CSV file should contain one website per row, with no headers.
- The script will then prompt you for the number of websites you want to check. This number should be between 1 and the total number of websites in the CSV file.
- The script will then prompt you for the iso-code of server location (Iran = IR, Germany = DE,....)
- You can leave this field blank and just press "Enter"
- Guide: https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes
- The script will then begin checking the websites and print the results to the console.
- The script will also create a JSON file named "result.json" in the same directory as the script. This file will contain the results of the website checks.
- CSV files sources: [here](https://www.domcop.com/top-10-million-websites) and [here](https://tranco-list.eu/)

<details>
 <summary>
  ❌ Fix script's issues on MacOS
 </summary>
 <br>
 If you ran into problems using the script, the reason is that MacOS's ssl libraries aren't defined for python, just paste the command below into your terminal and run the script again.
 
```bash
ln -s /etc/ssl/* /Library/Frameworks/Python.framework/Versions/Current/etc/openssl
```
 </details>
 
# Screenshots


![Screenshot (103)](https://github.com/ImanMontajabi/TLS-Checker/assets/52942515/d57f619b-5bb3-4ded-85a3-8976cfe24c5d)
![Screenshot (99)](https://github.com/ImanMontajabi/TLS-Checker/assets/52942515/04bb5e03-24f3-4917-af56-dbbfa4bb2524)


# video

- The following tutorial video can be a good guide for using this script:

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/QNbeYkGIiA4/0.jpg)](https://youtu.be/QNbeYkGIiA4)


# License
TLS Checker is licensed under the MIT License. See [LICENSE](https://github.com/ImanMontajabi/TLS-Checker/blob/master/LICENSE) for [more information](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).
