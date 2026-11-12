import socket
import threading

def sunucudan_aktar(v, conn): # Ana sunucudan gelen mesajları dinleyip istemciye yollamak için fonksiyon kurduk.
    durum = 1
    while durum == 1:
        try:
            gelen_veri = v.recv(1024) # Recv(1024) ile ana sunucudan en fazla 1024 byte veri alırız.
            if not gelen_veri: # Eğer veri gelmezse bağlantının kapandığunı kontrol ederiz.
                durum = 0
                break
            conn.sendall(gelen_veri) # Sendalle gelen veriyi direkt istemciye göndeririz.
        except:
            durum = 0
            break # Biz çıkış yapınca soket kapandığı için hata vermeden durduruz.
            
    conn.close() # İstemci bağlantısını kapatırız.
    v.close() # Ana sunucu bağlantısını kapatıyorum.

def kopru_islemleri(conn, addr, hedef_ip, hedef_port): # Connla istemciyle relay arasındaki bağlantıyı tutarız, addr ile Ip ve port bilgilerini tutarız.
    v = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Ana sunucu için socket oluşturuyoruz.
    v.connect((hedef_ip, hedef_port)) # Ana sunucunun portuna bağlanıyorum.
    
    print("Relay connected by", addr)

    dinleyici = threading.Thread(target=sunucudan_aktar, args=(v, conn)) # Threading ile thread oluştururuz. Targetta hangi fonksiyonun çalışacığını belirler.
    dinleyici.daemon = True # Daemon ile threadin ana program kapandığında kapanmasını sağlarız.
    dinleyici.start() # Threadi başlatırız.

    biriken_veri = "" # Mesajlar bazen yarım veya birleşik gelebildiği için burada biriktiriyorz.
    while True:
        try:
            gelen = conn.recv(1024).decode('utf-8') # Karşıdan gelen veriyi 1024 byte olarak alıp çözüyorum.
        except:
            break # Kullanıcı aniden çıkarsa hata vermesin döngüyü kırsın.

        if not gelen: # Bağlantı koptuysa döngüyü kırıyoruz.
            break

        biriken_veri = biriken_veri + gelen # Gelen veriyi biriken veriye ekleriz.

        while "\n" in biriken_veri: # Mesajın bittiğini anlamak için \n karakterini bekliyorum.
            parcalar = biriken_veri.split("\n", 1) # Veriyi iki parçaya ayırır.
            mesaj = parcalar[0].strip() 
            biriken_veri = parcalar[1] 
            if mesaj == "":
                continue # Boş mesaj gelirse döngüyü kırmadan devam eder.

            if mesaj.startswith("NICK:"): # Startswithle ilk gelen mesajın isim kaydı olup olmadığını kontrol ederiz.
                istenen_isim = mesaj.split(":", 1)[1].strip()
                
                if istenen_isim != "" and istenen_isim.startswith("*") == False: # İsim boş değilse ve yıldızla başlamıyorsa başına yıldız ekleriz.
                    gidecek_isim = "RELAY_NICK:*" + istenen_isim + "\n" # Ana sunucu relay olduğunu anlasın diye başına yıldız koyup hazırlarız.
                    print("Kullanici adina * eklendi -> *" + istenen_isim)
                else:
                    gidecek_isim = "NICK:" + istenen_isim + "\n"
                    
                v.sendall(gidecek_isim.encode('utf-8')) # Sendalle takma adı ana sunucuya göndeririz. Encodeyle de metni byte'a dönüştürürüz.
            else:
                v.sendall((mesaj + "\n").encode('utf-8')) # Normal mesajları ana sunucuya göndeririz. \n ile bitişi belirtiriz.

            if mesaj.lower() == 'cikis' or mesaj == 'EXIT': # Lower ile mesajı küçük harfe çeviririz. Çıkış yazılırsa döngüyü sonlandırırız.
                break

    print(addr, "relay uzerinden ayrildi.")
    v.close() # İstemci çıkınca ana sunucu soketini de kapatırız ki listeden silinsin.
    conn.close() # İstemci bağlantısını kapatıyorum.

def relay_baslat(): # Relayin bütün işlemlerini yöneten bir ana fonksiyon kurduk.
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    my_pc_name = socket.gethostname() # Bilgisayarımdan hostname çekiyorum.
    Ip_address = socket.gethostbyname(my_pc_name) # Hostname ile ip adresimi çekiyorum.

    secilen_ip = input(f"Ana Server IP ({Ip_address} icin bos birakin): ").strip() # Bağlanacağımız ana sunucunun IP adresini alıyorum.
    if secilen_ip != "": # Kullanıcı Ip adresi girdiyse Ip Adresini güncelleriz.
        hedef_ip = secilen_ip
    else:
        hedef_ip = Ip_address

    girilen_port = input("Ana Server Port : ").strip() # Kullanıcıdan ana sunucu portu girmesini isteriz.
    if girilen_port != "": # Kullancı port girerse onu kullanılır eğer boş bıraksa 1903 portunu seçeriz.
        hedef_port = int(girilen_port)
    else:
        hedef_port = 1903

    secilen_relay_port = input("Relay Port : ").strip() # Relay sunucusunun kendi port numarasını istiyoruz.
    if secilen_relay_port != "": # Port girilmişse int türüne dönüştürerek kullanıyoruz.
        relay_port = int(secilen_relay_port)
    else:
        relay_port = 2003 # Boş bırakılırsa belirlediğimiz 2003 değerine atarız.

    r.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Port takılı kalmasın, hemen tekrar açabilsin diye ayar yapıyorum.
    r.bind((Ip_address, relay_port)) # Oluşturduğum soketi ip adresime ve 1904 portuna bağlıyorum.
    r.listen(5) # Gelen bağlantı isteklerini dinlemeye başlıyorum.

    print(f"Relay started on {Ip_address}:{relay_port}. Forwarding to {hedef_ip}:{hedef_port}...")

    while True:
        conn, addr = r.accept() # İstemciden gelen bağlantıyı kabul ediyorum.
        t = threading.Thread(target=kopru_islemleri, args=(conn, addr, hedef_ip, hedef_port))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    relay_baslat()