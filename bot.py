import webbrowser
import requests
import time
from steampy.client import SteamClient
from tkinter import *
from tkinter import messagebox, filedialog
import shelve
import schedule
import functools


def catch_exceptions(cancel_on_failure=False):
    def catch_exceptions_decorator(job_func):
        @functools.wraps(job_func)
        def wrapper(*args, **kwargs):
            try:
                return job_func(*args, **kwargs)
            except:
                pass
                if cancel_on_failure:
                    return

        return wrapper

    return catch_exceptions_decorator


@catch_exceptions(cancel_on_failure=False)
def Exchange():
    response_steamtrader = requests.get(
        "https://api.steam-trader.com/exchange/?key={}".format(market_api_key))  # отправляю запрос на получение трейда
    response_steamtrader_json = response_steamtrader.json()

    success_steamtrader = response_steamtrader_json.get("success", "")
    if success_steamtrader:  # если ответ success
        offer = (response_steamtrader_json["offerId"])  # получаю из response_steamtrader_json offerID
        try:
            client.accept_trade_offer(offer)  # принимаю обмен с данными offerID
            print(f"Обмен {str(offer)} принят.")  # ответ что обмен принят успешно
            update_inventory()  # обновление инвентаря
            get_userbalance()   # баланс пользователя
        except:
            print(f"Не удалось принять обмен {str(offer)}.")  # ответ что не вышло принять обмен
            pass


def update_inventory():  # обновление инвентаря
    response_steamtrader_inventory = requests.get(
        "https://api.steam-trader.com/updateinventory/?key={}&gameid=440".format(market_api_key))
    response_steamtrader_inventory_json = response_steamtrader_inventory.json()

    success_steamtrader_inventory_json = response_steamtrader_inventory_json.get("success", "")
    if success_steamtrader_inventory_json:  # если ответ success
        print("Инвентарь TF2 обновлен")


def get_userbalance():  # баланс пользователя
    response_steamtrader_balance = requests.get(
        "https://api.steam-trader.com/getbalance/?key={}".format(market_api_key))
    response_steamtrader_balance_json = response_steamtrader_balance.json()

    success_steamtrader_balance_json = response_steamtrader_balance_json.get("success", "")
    if success_steamtrader_balance_json:  # если ответ success
        balance = (response_steamtrader_balance_json["balance"])
        print(f" Баланс {float(balance)} руб.")  # отображает баланс пользователя


def are_credentials_filled() -> bool:
    return api_key != '' or steamguard_path != '' or username != '' or password != '' or market_api_key != ''


def print_time():
    print(time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()))


def market_scheduler():
    print_time()
    update_inventory()
    get_userbalance()
    Exchange()

    schedule.every(2).minutes.do(print_time)

    schedule.every(120).seconds.do(Exchange)

    while True:
        schedule.run_pending()


win = Tk()
win.geometry("380x500")
win.maxsize(width=380, height=425)
win.title("Login on bot")
win.configure(bg="pink")


def create_widgets():
    root = Tk()
    root.title("ADLtradebot")
    root.configure(bg="#808080")
    root.maxsize(width=360, height=200)  # 230
    root.geometry("360x200")

    market_label = Label(root, text="ADLtradebot", font="Arial 24", padx=3, pady=5, bg="#808080", borderwidth=1)
    market_label.grid(row=0, column=0, padx=5, pady=10)

    text = """
    ADLtradebot made by mxINI
    Automatic Trading on Steam-Trader
    """

    about_label = Label(root, text=text, font="Arial 14", bg="#808080")
    about_label.grid(row=1, column=0, columnspan=2)

    start_btm = Button(root, bg="#C0C0C0", text="Start", activebackground="grey", command=market_scheduler)
    start_btm.grid(row=0, column=1, padx=5, pady=10, ipadx=60, ipady=15)


def browse():  # кнопка browse чтобы указать путь до стимгуарда
    path_to_steam = filedialog.askopenfilename(initialdir="/", title="Select file", filetypes=[("txt files", ".txt")])
    if path_to_steam == "":
        return
    entry_path.delete(0, END)
    entry_path.insert(0, path_to_steam)


def save_data():
    with shelve.open("data") as data:
        data["username"] = login_entry.get()
        data["password"] = password_entry.get()
        data["market_api_key"] = market_api_entry.get()
        data["api_key"] = steam_api_entry.get()
        data["steamguard_path"] = entry_path.get()


def log_in():
    # noinspection PyGlobalUndefined
    global username
    global password
    global market_api_key
    global api_key
    global steamguard_path
    global client
    username = login_entry.get()
    password = password_entry.get()
    market_api_key = market_api_entry.get()
    api_key = steam_api_entry.get()
    steamguard_path = entry_path.get()
    if not are_credentials_filled():
        messagebox.showerror("Ошибка", "Вы должны заполнить учетные данные.")
        return
    try:
        client = SteamClient(api_key)
        client.login(username, password, steamguard_path)
        messagebox.showinfo("Success",
                            'Бот вошел в систему:' + time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()))
        save_data()
        create_widgets()
        global win
        win.destroy()
    except:
        messagebox.showerror("Error", "Имя учетной записи или пароль, которые вы ввели, неверны или вы слишком"
                                      "предприняли слишком много попыток для входа в систему.")


def insert_data():
    with shelve.open("data") as data:
        try:
            entry_login.delete(0, END)
            entry_login.insert(0, data["username"])

            entry_password.delete(0, END)
            entry_password.insert(0, data["password"])

            entry_market_api.delete(0, END)
            entry_market_api.insert(0, data["market_api_key"])

            entry_steam_api.delete(0, END)
            entry_steam_api.insert(0, data["api_key"])

            entry_path.delete(0, END)
            entry_path.insert(0, data["steamguard_path"])
        except KeyError:
            pass


def find_shared_secret():
    result = webbrowser.open(
        "https://github.com/SteamTimeIdler/stidler/wiki/Getting-your-%27shared_secret%27-code-for-use-with-Auto-Restarter-on-Mobile-Authentication",
        new=1)
    return result


label = Label(win, text="Steam-Trader.com", font=("arial", 20, "bold"), bg="pink", justify=CENTER, padx=10, pady=10)
label.grid(row=0, column=0, columnspan=3, sticky="w")

label_login = Label(win, text="Login (Steam): ", bg="pink", font=("arial", 10), padx=10, pady=10)
label_login.grid(row=1, column=0, sticky="e")

login_entry = StringVar()
entry_login = Entry(win, textvariable=login_entry)
entry_login.grid(row=1, column=1)

label_password = Label(win, text="Password (Steam): ", bg="pink", font=("arial", 10), padx=10, pady=10)
label_password.grid(row=2, column=0, sticky="e")

password_entry = StringVar()
entry_password = Entry(win, textvariable=password_entry)
entry_password.grid(row=2, column=1)

label_market_api = Label(win, text="Steam-Trader API: ", bg="pink", font=("arial", 10), padx=10, pady=10)
label_market_api.grid(row=3, column=0, sticky="e")

market_api_entry = StringVar()
entry_market_api = Entry(win, textvariable=market_api_entry)
entry_market_api.grid(row=3, column=1)

label_steam_api = Label(win, text="Steam API: ", bg="pink", font=("arial", 10), padx=10, pady=10)
label_steam_api.grid(row=4, column=0, sticky="e")

steam_api_entry = StringVar()
entry_steam_api = Entry(win, textvariable=steam_api_entry)
entry_steam_api.grid(row=4, column=1)

label_steam_guard_path = Label(win, text="Steamguard file path: ", bg="pink", font=("arial", 10), padx=10, pady=10)
label_steam_guard_path.grid(row=5, column=0, sticky="e")

entry_path = Entry(win)
entry_path.grid(row=5, column=1)

btn_login = Button(win, text="Log in", command=log_in, pady=5, padx=10, bg="skyblue")
btn_login.grid(row=6, column=1, sticky="w")

btn_insert_data = Button(win, text="Insert data", command=insert_data, pady=5, padx=10, bg="skyblue")
btn_insert_data.grid(row=6, column=2, sticky="w")

entry_path = Entry(win)
entry_path.grid(row=5, column=1)

entry_path_button = Button(win, text="?", command=find_shared_secret, bg="skyblue")
entry_path_button.grid(row=5, column=3, columnspan=2, sticky="w")

btn = Button(win, text="Browse", command=browse, padx=10, bg="skyblue")
btn.grid(row=5, column=2)

lbl = Label(win, text="Нужно создать txt файл и Вложить в него данные снизу ", bg="pink")
lbl.grid(row=7, column=0, columnspan=3)

a = """
{
    "steamid": "YOUR_STEAM_ID_64",
    "shared_secret": "YOUR_SHARED_SECRET",
    "identity_secret": "YOUR_IDENTITY_SECRET"
}
"""

lbl2 = Label(win, text=a, bg="pink")
lbl2.grid(row=8, column=0, columnspan=4)

win.mainloop()
