from threading import Thread
from pycurl import Curl, URL, POSTFIELDS, USERAGENT, COOKIE, SSL_VERIFYPEER, SSL_VERIFYHOST, NOSIGNAL
from os import system, urandom
from random import choice
from hashlib import sha1
from queue import Queue
from time import sleep
from httpx import post
from uuid import uuid4

class Uitlities(object):
    def __init__(self):
        super(Uitlities, self).__init__()
        self.queue = Queue()

    def newFile(self, list, fileName):
        file = open("./data/" + fileName + ".txt", "w+")
        file.truncate(0)

        for strip in list:
            file.write(strip + "\n")

        return

    def appendFile(self, string, fileName):
        file = open("./data/" + fileName + ".txt", "a+")
        file.write(string + "\n")

        return

    def fillQueue(self, list):
        for rstrip in list:
            self.queue.put(rstrip.strip())
        
        return

    def gen_csrf_token(self):
        return sha1(urandom(64)).hexdigest()

class HTTP(object):
    def __init__(self):
        super(HTTP, self).__init__()
        self.url = "https://i.instagram.com/api/v1"
        self.uuid = uuid4()

    def createHTTPConfiguration(self):
        self.httpConfig = Curl()
        self.httpConfig.setopt(SSL_VERIFYHOST, 0)
        self.httpConfig.setopt(SSL_VERIFYPEER, 0)
        self.httpConfig.setopt(NOSIGNAL, 15)
        
        return self.httpConfig

    def httpLogin(self, username, password):

        JSON = post(self.url + "/accounts/login/", headers = {"Accept": "/","Accept-Encoding": "gzip, deflate", "Accept-Language": "en-US","X-IG-Capabilities": "3brTvw==","X-IG-Connection-Type": "WIFI","Content-Type": "application/x-www-form-urlencoded","User-Agent": "Instagram 84.0.0.21.105 Android (24/7.0; 240dpi; 720x1280; samsung; SM-G935F; SM-G935F; intel; en_US; 321039115)",
        }, data = {"uuid": self.uuid, "username": username, "password": password, "device_id": self.uuid, "_csrftoken": Uitlities().gen_csrf_token(),"login_attempt_countn": "0"}, timeout = 5)

        return JSON.cookies["sessionid"] if b"logged_in_user" in JSON.content else ""

    def httpRetrieveUserID(self, username, session):
        self.httpConfig.setopt(URL, self.url + "/users/" + username + "/usernameinfo/")
        self.httpConfig.setopt(USERAGENT, "Instagram 84.0.0.21.105 Android (24/7.0; 240dpi; 720x1280; samsung; SM-G935F; SM-G935F; intel; en_US; 321039115)")
        self.httpConfig.setopt(COOKIE, "sessionid=" + session)
    
        JSON = self.httpConfig.perform_rs()

        if "user_not_found" in JSON:
            return "No userID"
        
        elif username in JSON:
            return JSON.split('{"pk":')[1].split(',"')[0]

        else:
            return "Rate Limited!"

class Instagram(object):
    def __init__(self):
        super(Instagram, self).__init__()
    
        self.accounts = open("./data/accounts.txt", "r+").read().splitlines()
        self.usernames = open("./data/usernames.txt", "r+").read().splitlines()
        self.sessions = list()

        self.utilities = Uitlities()
        self.http = HTTP()

        self.http.createHTTPConfiguration()

    def loadAccounts(self):
        self.utilities.fillQueue(self.accounts)

        for _ in range(len(self.accounts)):
            account = self.utilities.queue.get()
            username, password = account.split(":")[0], account.split(":")[1]

            sleep(.100)
            session = self.http.httpLogin(username, password)

            if len(session) < 1:
                self.accounts.remove(account)
                
                if self.utilities.queue.empty() and not self.sessions:
                    return False

            else:
                self.sessions.append(session)
                self.accounts.remove(account)

                if self.utilities.queue.empty():
                    return True

    def scrapeUserID(self):
        self.utilities.fillQueue(self.usernames)

        while not self.utilities.queue.empty():
            username = self.utilities.queue.get()
            session = choice(self.sessions)

            sleep(.350) ## UPDATE THIS DELAY FOR HIGHER SPEEDS
            userID = self.http.httpRetrieveUserID(username, session)

            if "No userID" in userID:
                print("Username: " + username + "| Banned" + "\n")

                self.usernames.remove(username)
                self.utilities.appendFile(username, "banned")

            elif "Rate Limited!" in userID:
                self.sessions.remove(session)

                if not self.sessions:
                    print("Rate Limited!")
                    
                    return exit(1)

            else:
                print("Username: " + username + "| UID: " + userID + "\n")
                self.usernames.remove(username)
                
                self.utilities.appendFile(username + ":" + userID, "scraped")
                self.utilities.newFile(self.usernames, "usernames")

                if self.utilities.queue.empty():
                    print("Finished!")
                    
                    return exit(1)

    def createThreads(self, threads):
        for _ in range(threads):
            t = Thread(target = self.scrapeUserID)
            t.start()

def main():
    instagram = Instagram()
    instagram.loadAccounts()

    if not instagram.sessions:
        print("Error - Need at least one session to run tool!")
        sleep(1)
        exit(1)
    print("Loaded Sessions: " + str(len(instagram.sessions)))

    threads = input("Threads: ")
    print("\n")

    instagram.createThreads(int(threads))
    
if __name__ == "__main__":
    main()
