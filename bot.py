import functools
import logging
import shelve
import time
import webbrowser
from tkinter import *
from tkinter import messagebox, filedialog
import requests
import schedule
from steampy.client import SteamClient
import json

logger = logging.getLogger('')
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("schedule").setLevel(logging.WARNING)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler('logs.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


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
# client.accept_trade_offer(offer) спасибо за решение пробелемы vk > https://vk.com/ilay1999xp
def Exchange():
    response_steamtrader = requests.get(
        "https://api.steam-trader.com/exchange/?key={}".format(market_api_key))  # отправляю запрос на получение трейда
    response_steamtrader_json = response_steamtrader.json()
    logger.info('Отправлен запрос на проверку Купленных/Проданных предметов на сайте')  # логирование

    success_steamtrader = response_steamtrader_json.get("success", "")
    if success_steamtrader:  # если ответ success
        logger.info('Exchange: success - OfferID получен')  # логирование
        offer = (response_steamtrader_json["offerId"])  # получаю из response_steamtrader_json offerID
        try:
            client.accept_trade_offer(offer)  # принимаю обмен с данными offerID
            print(f"Обмен {str(offer)} принят.")  # ответ что обмен принят успешно
            logger.info(f"Обмен {str(offer)} принят.")  # логирование
            update_inventory()  # обновление инвентаря
            get_userbalance()  # баланс пользователя
        except:
            print(f"Не удалось принять обмен {str(offer)}.")  # ответ что не вышло принять обмен
            logger.warning(f"Не удалось принять обмен {str(offer)}.")  # логирование
            pass


def update_inventory():  # обновление инвентаря
    response_steamtrader_inventory = requests.get(
        "https://api.steam-trader.com/updateinventory/?key={}&gameid=440".format(market_api_key))
    response_steamtrader_inventory_json = response_steamtrader_inventory.json()

    success_steamtrader_inventory_json = response_steamtrader_inventory_json.get("success", "")
    if success_steamtrader_inventory_json:  # если ответ success
        logger.info('Inventory: success - Инвентарь получен')  # логирование
        print("Инвентарь TF2 обновлен")
        logger.info('Inventory updated')  # логирование


def get_userbalance():  # баланс пользователя
    response_steamtrader_balance = requests.get(
        "https://api.steam-trader.com/getbalance/?key={}".format(market_api_key))
    response_steamtrader_balance_json = response_steamtrader_balance.json()

    success_steamtrader_balance_json = response_steamtrader_balance_json.get("success", "")
    if success_steamtrader_balance_json:  # если ответ success
        logger.info('Balance: success - Баланс получен')  # логирование
        balance = (response_steamtrader_balance_json["balance"])
        print(f" Баланс {float(balance)} руб.")  # отображает баланс пользователя
        logger.info('Balance has been updated')  # логирование


# вывод buy order
def get_buyorders():
    response_steamtrader_buyorders = requests.get(
        "https://api.steam-trader.com/getbuyorders/?key={}".format(market_api_key))
    response_steamtrader_buyorders_json = response_steamtrader_buyorders.json()

    success_steamtrader_buyorders_json = response_steamtrader_buyorders_json.get("success", "")
    if success_steamtrader_buyorders_json:  # если ответ success
        logger.info('buyorders: success - Список предметов получен')  # логирование
        # спасибо за решение пробелемы vk.com/ilay1999xp
        offers = (response_steamtrader_buyorders_json["data"])  # беру инфу из data
        for offer in offers:
            offer1 = (offer["hash_name"])  # имя предмета
            offer2 = (offer["position"])  # позиция предмета
            print(f"Предмет:{str(offer1)} Позиция:{int(offer2)}")


def get_iteminfo():
    with open('chprices.json', 'r') as f:  # открываю файл с gid
        pricecfg = json.load(f)  # закинул данные в переменую
        items = (pricecfg["items"])  # инфа цифр из строки items
        gidNumbers = items["gid"]
        for gidNum in gidNumbers:  # проходимся по всем элементам массива items["gid"], с помощью цикла for in
            print(gidNum)
            time.sleep(3)  # спим 3 секунды
            response_steamtrader_itemprices = requests.get(
                "https://api.steam-trader.com/iteminfo/?key={}&gid={}".format(market_api_key, gidNum))
            response_steamtrader_itemprices_json = response_steamtrader_itemprices.json()

            success_steamtrader_itemprices_json = response_steamtrader_itemprices_json.get("success", "")
            if success_steamtrader_itemprices_json:
                logger.info('iteminfo: success - Цены на предметы получены')  # логирование
                market_name = (response_steamtrader_itemprices_json["name"])  # steamtrader имя предмета
                market_priceorder = (response_steamtrader_itemprices_json["buy_price"])
                offerssell = (response_steamtrader_itemprices_json["sell_offers"])[0]
                offer1 = (offerssell["price"])  # цена с инфы выще
                try:
                    print(f"Название предмета: {str(market_name)}.")
                    print(f"Минимальная цена продажи на сайте: {float(offer1)} Rub.")
                    print(f"Максимальная цена заявки на покупку: {float(market_priceorder)} Rub.")
                except:
                    pass


def are_credentials_filled() -> bool:
    return api_key != '' or steamguard_path != '' or username != '' or password != '' or market_api_key != ''


def print_time():
    print(time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()))
    logger.info(time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()))  # логирование


def market_scheduler():
    print_time()
    update_inventory()
    get_userbalance()
    Exchange()
    get_buyorders()
    get_iteminfo()

    schedule.every(2).minutes.do(print_time)

    schedule.every(180).seconds.do(Exchange)

    schedule.every(180).seconds.do(get_buyorders)

    schedule.every(180).seconds.do(get_iteminfo)

    while True:
        schedule.run_pending()


win = Tk()
win.geometry("380x295")
win.maxsize(width=380, height=295)
win.title("Login on bot")
win.configure(bg="pink")


def create_widgets():
    root = Tk()
    root.title("ADLmarketbot")
    root.configure(bg="#808080")
    root.maxsize(width=360, height=200)
    root.geometry("360x200")

    market_label = Label(root, text="ADLmarketbot", font="Arial 24", padx=3, pady=5, bg="#808080", borderwidth=1)
    market_label.grid(row=0, column=0, padx=5, pady=10)

    text = """
    ADLmarketbot made by mxINI
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
        logger.info("Неудачная попытка авторизации/нужно заполнить учетные данные")  # логирование
        return
    try:
        client = SteamClient(api_key)
        client.login(username, password, steamguard_path)
        messagebox.showinfo("Success",
                            'Бот вошел в систему:' + time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime()))
        logger.info("Бот вошел в систему")  # логирование
        save_data()
        create_widgets()
        global win
        win.destroy()
    except:
        messagebox.showerror("Error", "Имя учетной записи или пароль, которые вы ввели, неверны или вы "
                                      "предприняли слишком много попыток для входа в систему.")
        logger.error("Неудачная попытка авторизации")  # логирование


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


def find_market_api():
    result = webbrowser.open("http://api.steam-trader.com", new=1)
    return result


def find_steam_api():
    result = webbrowser.open("https://steamcommunity.com/dev/apikey", new=1)
    return result


def find_shared_secret():
    result = webbrowser.open(
        "https://github.com/SteamTimeIdler/stidler/wiki/Getting-your-%27shared_secret%27-code-for-use-with-Auto"
        "-Restarter-on-Mobile-Authentication",
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

market_api_button = Button(win, text='?', command=find_market_api, bg="skyblue")
market_api_button.grid(row=3, column=3, columnspan=2, sticky="w")

label_steam_api = Label(win, text="Steam API: ", bg="pink", font=("arial", 10), padx=10, pady=10)
label_steam_api.grid(row=4, column=0, sticky="e")

steam_api_entry = StringVar()
entry_steam_api = Entry(win, textvariable=steam_api_entry)
entry_steam_api.grid(row=4, column=1)

steam_api_button = Button(win, text="?", command=find_steam_api, bg="skyblue")
steam_api_button.grid(row=4, column=3, columnspan=2, sticky="w")

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

win.mainloop()
