import pymongo, datetime, threading, os, colorama, requests, proxy_checker, bs4, re

class Database:
    def __init__(self, connection_string):
        self.client = pymongo.MongoClient(connection_string)
        self.database = self.client['proxies']['alive']
    
    def get_proxies(self):
        proxy_list = []

        for proxy in self.database.find({}):
            proxy_list.append(f'{proxy["ip"]}:{proxy["port"]}')
            
        return list(set(proxy_list))
    
    def save_proxy(self):
        proxy_list = []

        for proxy in self.database.find({}):
            proxy_list.append(f'{proxy["protocols"][0]}://{proxy["ip"]}:{proxy["port"]}')
        
        with open('./save.txt', 'a+') as file:
            file.truncate(0) 

        with open('./save.txt', 'a+') as pf:
            for proxy in list(set(proxy_list)):
                pf.write(proxy + '\n')
    
    def add_raw_proxy(self, proxy_list):
        for proxy in proxy_list:
            try:
                self.database.insert_one(proxy)
            except Exception:
                pass
    
    def update_database(self, proxy_list):
        self.client.drop_database('proxies')
        self.client['proxies']['info'].insert_one({'updated_at': datetime.datetime.utcnow()})
        self.add_raw_proxy(proxy_list)
    
        print(f'{colorama.Fore.WHITE}[{colorama.Fore.GREEN}+{colorama.Fore.WHITE}] Proxy added to database.')

class Console:
    def __init__(self):
        os.system('cls && title ProxyHeast' if os.name == 'nt' else 'clear')
        print(f'''{colorama.Style.BRIGHT}{colorama.Fore.WHITE}     
        ______                    _   _                _   
        | ___ \                  | | | |              | |  
        | |_/ / __ _____  ___   _| |_| | ___  __ _ ___| |_ 
        |  __/ '__/ _ \ \/ / | | |  _  |/ _ \/ _` / __| __|
        | |  | | | (_) >  <| |_| | | | |  __/ (_| \__ \ |_ 
        \_|  |_|  \___/_/\_\\\\__, \_| |_/\___|\__,_|___/\__|
                            __/ |                         
                           |___/   https://github.com/{colorama.Fore.RED}Its-Vichy{colorama.Fore.WHITE}\n\n''')
    
    def printer(self, color, past, text):
        #with threading.Lock():
        print(f'{colorama.Fore.WHITE}[{color}{past}{colorama.Fore.WHITE}] {text}.')
    
class Scrapper:
    def __init__(self, console, database):
        self.database = database
        self.console = console
        self.scraped_source = 0
        self.scraped_proxy = []
        self.url = []
        self.load_url()
    
    def load_url(self):
        with open('./url.txt', 'r+') as url_file:
            for url in url_file:
                self.url.append(url.split('\n')[0])
        
        self.url = list(set(self.url))
    
    def scrape_file(self):
        proxy_list = []
        with open('./proxy.txt', 'r+') as proxy_file:
            for proxy in proxy_file:
                if '://' in proxy:
                    proxy_list.append(proxy.split('://')[1].split('\n')[0])
                else:
                    proxy_list.append(proxy.split('\n')[0])
        
        self.scraped_source += 1
        for proxy in list(set(proxy_list)):
            self.scraped_proxy.append(proxy)

    def scrape_with_regex(self):
        proxy_w_regex = [
            # Credit to https://github.com/NightfallGT/X-Proxy for regex scrape 
            
            ["http://spys.me/proxy.txt","%ip%:%port% "],
            ["http://www.httptunnel.ge/ProxyListForFree.aspx"," target=\"_new\">%ip%:%port%</a>"],
            ["https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.json", "\"ip\":\"%ip%\",\"port\":\"%port%\","],
            ["https://raw.githubusercontent.com/fate0/proxylist/master/proxy.list", '"host": "%ip%".*?"country": "(.*?){2}",.*?"port": %port%'],
            ["https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list.txt", '%ip%:%port% (.*?){2}-.-S \\+'],
            ["https://www.us-proxy.org/", "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
            ["https://free-proxy-list.net/", "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
            ["https://www.sslproxies.org/", "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
            ['https://www.socks-proxy.net/', "%ip%:%port%"],
            ['https://free-proxy-list.net/uk-proxy.html', "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
            ['https://free-proxy-list.net/anonymous-proxy.html', "<tr><td>%ip%<\\/td><td>%port%<\\/td><td>(.*?){2}<\\/td><td class='hm'>.*?<\\/td><td>.*?<\\/td><td class='hm'>.*?<\\/td><td class='hx'>(.*?)<\\/td><td class='hm'>.*?<\\/td><\\/tr>"],
            ["https://www.proxy-list.download/api/v0/get?l=en&t=https", '"IP": "%ip%", "PORT": "%port%",'],
            ["https://api.proxyscrape.com/?request=getproxies&proxytype=http&timeout=6000&country=all&ssl=yes&anonymity=all", "%ip%:%port%"],
            ["https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt", "%ip%:%port%"],
            ["https://raw.githubusercontent.com/shiftytr/proxy-list/master/proxy.txt", "%ip%:%port%"],
            ["https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", "%ip%:%port%"],
            ["https://www.hide-my-ip.com/proxylist.shtml", '"i":"%ip%","p":"%port%",'],
            ["https://raw.githubusercontent.com/scidam/proxy-list/master/proxy.json", '"ip": "%ip%",\n.*?"port": "%port%",'],
            ['https://www.freeproxychecker.com/result/socks4_proxies.txt', "%ip%:%port%"],
            ['https://proxy50-50.blogspot.com/', '%ip%</a></td><td>%port%</td>'], 
            ['http://free-fresh-proxy-daily.blogspot.com/feeds/posts/default', "%ip%:%port%"],
            ['http://free-fresh-proxy-daily.blogspot.com/feeds/posts/default', "%ip%:%port%"],
            ['http://www.live-socks.net/feeds/posts/default', "%ip%:%port%"],
            ['http://www.socks24.org/feeds/posts/default', "%ip%:%port%"],
            ['http://www.proxyserverlist24.top/feeds/posts/default',"%ip%:%port%" ] ,
            ['http://proxysearcher.sourceforge.net/Proxy%20List.php?type=http',"%ip%:%port%"],
            ['http://proxysearcher.sourceforge.net/Proxy%20List.php?type=socks', "%ip%:%port%"],
            ['http://proxysearcher.sourceforge.net/Proxy%20List.php?type=socks', "%ip%:%port%"], 
            ['https://www.my-proxy.com/free-anonymous-proxy.html', '%ip%:%port%'],
            ['https://www.my-proxy.com/free-transparent-proxy.html', '%ip%:%port%'],
            ['https://www.my-proxy.com/free-socks-4-proxy.html', '%ip%:%port%'],
            ['https://www.my-proxy.com/free-socks-5-proxy.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-2.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-3.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-4.html', '%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-5.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-6.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-7.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-8.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-9.html','%ip%:%port%'],
            ['https://www.my-proxy.com/free-proxy-list-10.html','%ip%:%port%'],
        ]
        
        found_proxy = []

        def scrape(url, custom_regex):
            self.scraped_source += 1
            proxylist = requests.get(url, timeout=5).text
            custom_regex = custom_regex.replace('%ip%', '([0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3})')
            custom_regex = custom_regex.replace('%port%', '([0-9]{1,5})')

            for proxy in re.findall(re.compile(custom_regex), proxylist):
                found_proxy.append(proxy[0] + ":" + proxy[1])

        def scrape_regex():
            for source in proxy_w_regex:
                try:
                    scrape(source[0], source[1])
                except:
                    pass

        scrape_regex()
        for proxy in list(set(found_proxy)):
            self.scraped_proxy.append(proxy)

    def scrape_proxylist_live(self):
        thread_list = []
        
        def scrape_protocol(protocol):
            proxy_found = []
            page = 0
            while True:
                try:
                    page += 1
                    self.scraped_source += 1
                    proxies = bs4.BeautifulSoup(requests.get(f'https://proxylist.live/dashboard/{protocol}?page={page}').text, features= 'lxml')('table',{'class':'table'})[0].findAll('tr')

                    for i in range(len(proxies)):
                        res = proxies[i].findChildren(recursive = False)[0].text.strip()

                        if res != 'Proxy':
                            proxy_found.append(res)
                        
                    if len(proxies) == 1:
                        break
                except:
                    pass

            for proxy in list(set(proxy_found)):
                self.scraped_proxy.append(proxy)
        
        for protocol in [ 'proxylist', 'socks4', 'socks5' ]:
            thread_list.append(threading.Thread(target= scrape_protocol, args= (protocol,)))

        for thread in thread_list:
            thread.start()
        
        for thread in thread_list:
            thread.join()

    def scrape_url(self, url):
        found_proxy = []
        try:
            for proxy in requests.get(url).text.split('\n'):
                found_proxy.append(proxy.split('\n')[0].replace('\r', ''))
            
            self.scraped_source += 1
        except:
            pass
            
        for proxy in list(set(found_proxy)):
            self.scraped_proxy.append(proxy)

    def scrape_proxies(self):
        thread_list = [
            threading.Thread(target= self.scrape_file),
            threading.Thread(target= self.scrape_with_regex),
            threading.Thread(target= self.database.get_proxies),
            threading.Thread(target= self.scrape_proxylist_live)
        ]

        proxy_list  = []

        for url in self.url:
            thread_list.append(threading.Thread(target= self.scrape_url, args=(url,)))
        
        for thread in thread_list:
            thread.start()
        
        for thread in thread_list:
            thread.join()

        for proxy in list(set(self.scraped_proxy)):
            proxy_list.append(proxy)
            
        proxy_list = list(set(proxy_list))
        self.console.printer(colorama.Fore.GREEN, '+', f'Found {len(proxy_list)} proxies from {self.scraped_source} sources')
    
        return proxy_list

class Checker:
    def __init__(self, console, proxy_list, database):
        self.proxy_list = proxy_list
        self.database = database
        self.console = console
        self.proxy = []
    
    def checker_thread(self, proxy_list):
        checker = proxy_checker.ProxyChecker()
        for proxy in proxy_list:
            result = checker.check_proxy(proxy)
            
            if result != False:
                self.console.printer(colorama.Fore.GREEN, '+', f"{proxy} | {result['protocols'][0]} | {result['timeout']}ms")
                self.proxy.append({
                    'ip': proxy.split(':')[0],
                    'port': proxy.split(':')[1],
                    'country_code': result['country_code'],
                    'protocols': result['protocols'],
                    'anonymity': result['anonymity'],
                    'timeout': int(result['timeout']),
                    'country': result['country'],
                })

    def create_thread(self, proxy_list):
        thread_list = []

        for proxys in list(zip(*[iter(proxy_list)] * 2)):
            thread_list.append(threading.Thread(target= self.checker_thread, args=(list(proxys),)))
        
        self.console.printer(colorama.Fore.YELLOW, '*', f'Starting {len(thread_list)} threads with 2 proxies')
        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()
        
        self.database.update_database(self.proxy)

    def start_checker(self):
        self.create_thread(self.proxy_list)

if __name__ == '__main__':
    console = Console()
    database = Database('database url')
    scraper = Scrapper(console, database)

    database.save_proxy()
    while True:
        Checker(console, scraper.scrape_proxies(), database).start_checker()
        database.save_proxy()
