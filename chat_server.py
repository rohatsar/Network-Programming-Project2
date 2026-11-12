import socket
import threading
import datetime
import time
from websocket_server import WebsocketServer 

kullanicilar = {} # Bağlanan kişileri isim ve conn olarak burada tutacağım.
kilit = threading.Lock() # Aynı anda iki kişi bağlanırsa sözlük karışmasın diye kilitliyoruz.
toplam_mesaj = 0 # İşlenen geçerli mesaj sayısını tutmak için sayaç tanımlıyoruz.
ws_server = None # WebSocket sunucusunu global olarak tutacağız.

def canli_gonder(log_metni): # İzleme sayfasına güncel sayıları ve log metnini gönderen bir fonksiyon oluşturduk.
    if ws_server != None: # Web socket sunucusunu var mı yok mu diye kontrol ediyoruz
        aktif_sayisi = len(kullanicilar) # İçeride aktif kaç kişi varsa sayıyoruz.
        paket = f"{aktif_sayisi}|{toplam_mesaj}|{log_metni}" # Tek bir yerde bu üçünü birleştiriyoruz.
        ws_server.send_message_to_all(paket) # Herkese aynı anda yolluyor.

def sohbet_kaydet(metin): # Hem server hemde client tarafından her mesajları tek bir dosyaya yazdırmak için fonksiyon tanımlıyoruz.
    saat = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("sohbet_kayitlari.txt", "a") as f: # Txtimizi oluşturuyoruz.
        f.write(f"[{saat}] {metin}") # Gelen mesajı dosyaya yazdırıyoruz.
        f.write("\n")
    canli_gonder(f"[{saat}] {metin}")# Dosyaya yazdığımız log satırını canlı izleme sayfasını da gönderiyoruz.    

def istemci_islemleri(conn, addr): # Connla istemciyle sunucu arasındaki bağlantıyı tutarız, addr ile sistemcinin Ip ve port bilgilerini tutarız.
    global toplam_mesaj # Sayacı artırmak için global olarak çağırıyoruz.
    isim ="" # Kullanıcının ismini buraya kaydedeceğiz.
    mesaj = "" # Mesaj hiç atanmadan kontrol edilirse NameError çıkmasın diye başta boş tanımlarız.
    biriken_veri = "" # Mesajlar bazen yarım veya birleşik gelebildiği için burada biriktiriyorz.
    mesaj_sayisi = 0 # Kullanıcının attığı mesajları saymak için sayaç tutuyoruz.
    ilk_mesaj_zamani = time.time() # Süre aralığını kontrol etmek için başlangıç zamanını alıyoruz.
    ceza_bitis_zamani = 0 # Kullanıcı çok hızlı yazarsa susturulacağı süreyi burada tutacağız.
    
    while True:
        try:
            gelen = conn.recv(1024).decode('utf-8') # Karşıdan gelen veriyi 1024 byte olarak alıp çözüyorum.
        except:
            break # Kullanıcı aniden çıkarsa hata vermesin, döngüyü kırsın.
        
        if not gelen: # Bağlantı koptuysa döngüyü kırıyoruz.
            break

        biriken_veri = biriken_veri + gelen # Gelen veriyi biriken veriye ekleriz.

       
        while "\n" in biriken_veri: # Mesajın bittiğini anlamak için \n karakterini bekliyorum. Eğer varsa mesajı alıp işleme sokuyorum.
            parcalar = biriken_veri.split("\n", 1) #  Veriyi iki parçaya ayırır.
            mesaj = parcalar[0].strip() 
            biriken_veri = parcalar[1] 

            if mesaj == "":
                continue # Boş mesaj gelirse döngüyü kırmadan devam eder.

           
            if isim == "": #  Kullanıcın ismi girmemişse, ilk olarak isim girmesini isteriz.
                if mesaj.startswith("NICK:") or mesaj.startswith("RELAY_NICK:"): # Gelen mesajın uygun olup olmadığını kontrol ederiz.
                    istenen_isim = mesaj.split(":", 1)[1].strip() 
                    relay_mi = mesaj.startswith("RELAY_NICK:") # Startswithle bağlantının relay üzerinden gelip gelmediğini kontrol ederiz.
                    
                    if istenen_isim == "" or ( relay_mi== False and istenen_isim.startswith("*")): # startwithle yıldız işaretiyle başlayan kullanıcı adlarını engelleriz. İstenen isimlede boş isimleri engeller.
                        cevap = "HATA:İsim * ile başlayamaz veya boş olamaz.\n"
                        print(f"\n{cevap}")
                        conn.sendall(cevap.encode('utf-8')) 
                        conn.close() # Bağlantıyı kapatırız.
                        return

                    kilit.acquire() # Sözlüğe bakarken başka thread araya girmesin diye kilitliyorum.
                    kontrol_isim = istenen_isim 
                    sayac = 1
                    while kontrol_isim in kullanicilar: # Kullanıcı adı varsa yeni isim oluşturulur.
                        kontrol_isim = f"{istenen_isim}{sayac}"
                        sayac = sayac + 1
                    
                    isim = kontrol_isim
                    kullanicilar[isim] = conn # Kullanıcı isimlerini ve bağllantılarını soketini sözlüğe kaydederiz.
                    kilit.release() # İşim bitince kilidi açıyorum.

                    cevap = f"OK:{isim}\n" # Kullanıcının kayıt işleminin başarılı diye mesaj hazırlarız.
                    print(f"\n{cevap}")
                    conn.sendall(cevap.encode('utf-8')) # Sendalle kullancıya onay mesajını istemciye göndeririz.
                    print(f"Connected by {addr}. Kullanici adi: {isim}")
                    sohbet_kaydet(f"BAGLANTI: {isim} ({addr}) sohbete katildi.") # Kullanıcın katılımını kayıt dosyasına yazarız.
                    herkese_gonder(f"[SISTEM] {isim} sohbete katildi.") # Herkese yeni kişinin katıldığını duyuruyoruz.
                    liste_guncelle() # Kullanıcı listesini güncelliyoruz.
                else:
                    conn.sendall("HATA:Önce isim girmelisiniz.\n".encode('utf-8')) 
                    # Kullanıcı ilk mesaj olarak "NICK" göndermemişse hata mesajı göndeririz.Buradaki amacım kullanıcılar kayıt yapmadan sohbet işlemlerine geçmesini engellemek.
            else: 
                # Kullacının daha önce isim kaydı yaptığını anlarız.
                
                if mesaj.lower() == 'cikis': # Kullanıcının çıkış yapmak ya da yapmamak istediğini kontrol ederiz.
                    print(f"{isim} chatten ayrıldı.")
                    sohbet_kaydet(f"CIKIS: {isim} sohbetten ayrildi.") # Mesajı kayıt dosyasına yazarız.
                    break
                
                if len(mesaj) > 500: # Mesajın 500'den büyük olup olmadığını kontrol ederiz.
                    conn.sendall("HATA:Mesaj çok uzun.\n".encode('utf-8')) # Sendal ile mesaj uzunsa kullanıcıya hata göndeririz.
                    sohbet_kaydet(f"HATA: {isim} cok uzun mesaj gondermeye calisti.")
                    continue

                if mesaj.lower() == '/liste': 
                    kilit.acquire() # Sözlüğe bakmadan önce kilidi alırız.
                    isim_listesi = ",".join(kullanicilar.keys()) # Virgülle ayırarak tek bir metin haline getiririz.
                    kilit.release() # Liste alındıktan sonra kilidi bırakırız.
                    conn.sendall(f"[SISTEM] Aktif Kullanicilar: {isim_listesi}\n".encode('utf-8')) # Hazırlanan kulalanıcı listesini yalnzıca komutu yazan istemciye göndeririz.
                    continue # Döngünü başına döneriz ve / liste komutunu normal sohbet mesajı olarak gönderilmez.

               
                su_anki_zaman = time.time() # Bilgisayarın şu anki zamanını veririz.

                
                if su_anki_zaman < ceza_bitis_zamani: # Kontrol ediyoruz ceza bitiş zamanı önce mi sonra mı diye.
                    kalan_sure = int(ceza_bitis_zamani - su_anki_zaman) # Cezanın bitmesine ne kadar kaldığını hesaplıyoruz.
                    conn.sendall(f"HATA:Çok hızlı mesaj gönderdiniz! {kalan_sure} saniye boyunca susturuldunuz.\n".encode('utf-8')) # Kalan süreyi bildirir.
                    continue # Mesajı durdurur ve döngünün başına döneriz.

              
                if su_anki_zaman - ilk_mesaj_zamani > 10: # Zaman farkını hesaplarız ve 10 saniyeyi geçmiş mi geçmemiş mi dye kontrol ederiz.
                    ilk_mesaj_zamani = su_anki_zaman # Yeni aralığı belirleriz.
                    mesaj_sayisi = 0 # Önceki zaman aralığındaki sayacı sıfırlarız.

                mesaj_sayisi = mesaj_sayisi + 1 # Her mesajda sayacı 1 artırıyoruz.

               
                if mesaj_sayisi > 5: # Mesaj 10 saniyede 5 mesaj sınırını aşmış mı aşmamış mı diye kontrol ederiz.
                    ceza_bitis_zamani = su_anki_zaman + 15 # Ceza biteceği zamana 15 saniye ekleriz.
                    conn.sendall("HATA:Hız sınırını aştınız. 15 saniye susturuldunuz.\n".encode('utf-8'))# Kullanıcıya 15 saniye susturulduğunu bildiririz.
                    print(f"[RATE LIMIT] {isim} cok hizli mesaj attigi icin 15 saniye susturuldu.") 
                    sohbet_kaydet(f"RATE_LIMIT: {isim} hiz sinirini astigi icin 15 saniye susturuldu.") 
                    continue # Mesaj işlemini durduruz.

                saat_kisa = datetime.datetime.now().strftime("%H:%M:%S") # Mesajların yanına koymak için saati çekiyorum.
                
                if mesaj.startswith("/msg "): # Kullanıcı özel mesaj göndermek isteyip istemediğini kontrol ederiz.
                    bolumler = mesaj.split(" ", 2) # Mesajı '/msg', 'hedef_isim' ve 'içerik' olarak 3 parçaya ayırıyoruz.
                    if len(bolumler) < 3 or bolumler[2].strip() == "": # Eksik yazdıysa uyarıyoruz.
                        conn.sendall("HATA:Özel mesaj için '/msg isim mesaj' şeklinde yazın.\n".encode('utf-8')) # Sendall ile kullanıcıya doğru komut formatını bildiriyoruz.
                    else:
                        hedef_isim = bolumler[1].strip() # Özel mesajın hedef ismini tutar.
                        ozel_icerik = bolumler[2].strip()# Özel mesajın içeriğini tutar.

                        kilit.acquire() # Hedef kişi içeride mi diye bakarken sözlüğü kilitliyorum.
                        if hedef_isim in kullanicilar: # Kullanıcının sunucuya bağlı olup olmadığını kontrol ederiz.
                            hedef_conn = kullanicilar[hedef_isim] # Hedef kullanıcının socket bağlantısını alırız.
                            kilit.release() # Kontrol tamamlandığından kilidi serbest bırakırız.

                            
                            hedef_conn.sendall(f"[{saat_kisa}] [OZEL - {isim} -> {hedef_isim}]: {ozel_icerik}\n".encode('utf-8')) # Hedef_conn ile özel mesajı alıcıya göndeririz.
                            conn.sendall(f"[{saat_kisa}] [OZEL - {isim} -> {hedef_isim}]: {ozel_icerik}\n".encode('utf-8')) # Aynı mesajı gönderen kişinin ekranınıda göndeririz.
                            
                            
                            print(f"[OZEL] {isim} -> {hedef_isim}: {ozel_icerik}")
                            toplam_mesaj = toplam_mesaj + 1 # Özel mesaj iletildiği için toplam mesaj sayısını 1 artıyorum.
                            sohbet_kaydet(f"PRIVATE | Gonderen: {isim} | Alici: {hedef_isim} | Mesaj: {ozel_icerik}") # Dosyaları kaydederiz.
                        else:
                            kilit.release() # Kullanıcı bulunmasada kilidi serbest bırakrıız.
                            conn.sendall(f"HATA:'{hedef_isim}' isimli kullanıcı şu an bağlı değil.\n".encode('utf-8')) # Sendall ile kullanıcıya hedefin bağlı olmadığını bildiririz.
                            sohbet_kaydet(f"HATA: {isim}, bagli olmayan '{hedef_isim}' kullanicisina ozel mesaj denedi.")
               
                else: # Mesaj özel mesaj veya liste komutu değilse genel mesaj olarak kabul ederiz.
                    genel_mesaj = f"[{saat_kisa}] [GENEL] {isim}: {mesaj}" # Saat ve kullanıcı adını mesajın başına ekleriz.
                    print(genel_mesaj)
                    toplam_mesaj = toplam_mesaj + 1 # Genel mesaj geldiği için toplam mesaj sayısını 1 arttıyorum.
                    sohbet_kaydet(f"PUBLIC | Gonderen: {isim} | Alici: ALL | Mesaj: {mesaj}")
                    herkese_gonder(genel_mesaj) # Gönderen dahil herkese iletiyoruz.

        if mesaj.lower() == 'cikis':  #"cikis" yazılırsa ana dinleme döngüsü de sonlandırırız.
            break

    
    if isim != "": # Kullanıcının gerçekten kayıtlı olup olmadığını kontrol ederiz.
        kilit.acquire() # Acquire ile sözlük üzerinden işlem yapmadan önce kilidi alırız.
        if isim in kullanicilar: # Kullanıcının ismi sözlükte var mı yok mu diye kontrol ederiz.
            del kullanicilar[isim] # Kullanıcıyı sözlükten sileriz.
        kilit.release() # Kilidi serbest bırakırız.
        
        sohbet_kaydet(f"AYRILMA: {isim} baglantisi kapandi, listeden silindi.") # İzleme sayfasında kullanıcı sayısı güncellensin diye kaydediyoruz.
        herkese_gonder(f"[SISTEM] {isim} sohbetten ayrildi.") # Kalan kullanıcılara çıktığını haber veriyoruz.
        liste_guncelle() # Yeni listeyi kalanlara gönderiyoruz.
    conn.close() # İstemci bağlantısını kapatıyorum.

def chat_server():
    global ws_server
    r = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    my_pc_name = socket.gethostname() # Bilgisayarımdan hostname çekiyorum.
    Ip_address = socket.gethostbyname(my_pc_name) # Hostname ile ip adresimi çekiyorum.

    
    secilen_ip = input(f"Server IP ({Ip_address} icin bos birakin): ").strip() # Kullanıcı boş bırakırsa bizm belirlediğimiz Ip adresini kullanılırız.
    if secilen_ip != "": # Kullanıcı Ip adresi girdiyse Ip Adresini güncelleriz.
        Ip_address = secilen_ip

    secilen_port = input("Port: ").strip() # Sohbet sunucusunun port numarasını istiyoruz.
    if secilen_port != "": #Port girilmişse int türüne dönüştürerek kullanıyoruz.
        port = int(secilen_port)
    else:
        port = 1903 # Port boş bırakılırsa belirlediğimiz 1903 değerine atarız.
        
    sectiğimiz_ws_port = input("Monitoring WebSocket Port: ").strip() # Canlı izleme için sunucudan ayrı bir port numarası istiyoruz.
    if sectiğimiz_ws_port != "": # Kullanıcı port girdiyse onu kullanırız girmediyse de belirledeğimiz port sayısını kullanırlar.
        ws_port = int(sectiğimiz_ws_port)
    else:
        ws_port = 2182 # 2182 değerine atarız.

    
    ws_server = WebsocketServer(host=Ip_address, port=ws_port) # Belirlenen Ip ve port üzerinden oluşturup, canlı izleme bağlantısının portlarına ayırıyoruz.
    ws_thread = threading.Thread(target=ws_server.run_forever) # Bağımsız olsun diye thread oluşturuyoruz.
    ws_thread.daemon = True # Ana program kapandığında bu thread'ın kapanmasını sağlıyoruz.
    ws_thread.start() # Oluşturduğumuz thread'ı başlatarak websocket sunucusunu çalıştırıyoruz.
    print(f"Monitoring WebSocket started on ws://{Ip_address}:{ws_port}")
    
    r.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Port takılı kalmasın, hemen tekrar açabilsin diye ayar yapıyorum.
    r.bind((Ip_address, port)) # Oluşturduğum soketi ip adresime ve 1903 portuna bağlıyorum.
    r.listen(5) # Gelen bağlantı isteklerini dinlemeye başlıyorum.

    print(f"Server started on {Ip_address}:{port}. Waiting for client...") # Client'tan bağlanırken görebilmek için IP'yi ekrana yazdırıyorum.
    sohbet_kaydet(f"SERVER: {Ip_address}:{port} uzerinde baslatildi.")

    while True:
        conn, addr = r.accept() 
        t = threading.Thread(target=istemci_islemleri, args=(conn, addr))
        t.daemon = True
        t.start()
        
def herkese_gonder(mesaj_metni): # Sunucuya bağlı olan bütün kullanıcılara aynı mesajı göndermek için fonksiyon yarattık.
    silinecekler=[] # Bağlantısı kopanlar için boş bir liste oluşturduk.
    kilit.acquire() # Kullanıcı sözlüğüne erişirken başka thread'in araya girmesini önlüyorum.
    for k_adi in list(kullanicilar.keys()): # Sözlükteki bütün kullanıcı adlarını tek tek dolaşıyorum.
        bagli_soket = kullanicilar[k_adi] # Kullanıcının bağlantı soketini alıyorum.
        try:
           bagli_soket.sendall((mesaj_metni + "\n").encode('utf-8')) # Mesajı byte formatına çevirerek gönderiyorum.
        except:
           silinecekler.append(k_adi) # Kullanıcının soketi koptuysa hata vermesin,listeden sileceğiz.
           
    for k_adi in silinecekler:  # # Bağlantısı kopan kullanıcıların listesini tek tek dolaşıyoruz.
        if k_adi in kullanicilar:  # Kullanıcının hâlâ sözlükte bulunup bulunmadığını kontrol ediyoruz.
            del kullanicilar[k_adi]  # Bağlantısı kopan kullanıcıyı aktif kullanıcılar sözlüğünden siliyoruz.     
    kilit.release() # Gönderim işlemi bitince kilidi serbest bırakıyorum.
    
def liste_guncelle(): # Kullanıcı giriş veya çıkış yaptığında aktif kullanıcı listesini güncelliyorum.
    kilit.acquire()
    isim_listesi = ",".join(kullanicilar.keys()) # Kullanıcı isimlerini virgülle ayırarak tek bir metin haline getiriyorum.
    kilit.release()
    herkese_gonder(f"[SISTEM] Aktif Kullanicilar: {isim_listesi}") # Hazırladığım güncel listeyi bütün kullanıcılara gönderiyorum.
    
if __name__ == "__main__":
    chat_server()