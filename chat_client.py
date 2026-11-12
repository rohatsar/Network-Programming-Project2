import socket
import threading

calisiyor = True # İstemcinin çalışma durumunu kontrol eden değikendir.

def sunucudan_dinle(v): # Sunucudan gelen mesajları dinlemek için oluşturduğumuz bir fonksiyondur.
    
    global calisiyor # Fonksiyon içerisinde global değişkeni değiştiririz.
    tampon = "" # Parçalı gelen verileri biriktirmek için kullanılır.
    while calisiyor: # İstemci çalıştığı sürece sunucudan veri bekleriz.
        try:
            
            veri = v.recv(1024).decode('utf-8') # Sunucudan en fazla 1024 byte veri alırız.
        except:
            break # Biz çıkış yapınca soket kapandığı için hata vermeden durduruz.
        if not veri: # Eğer veri gelmezse bağlantının kapandığunı kontrol ederiz.
            print("\n[!] Sunucu ile baglanti koptu.")
            calisiyor = False # İstemcinin çalışmasını durdururuz.
            break # Döngüyü kırarız.
        
        tampon += veri # Gelen veriyi tampona ekleriz.
        while "\n" in tampon: # Tamponda tamamlanmış mesaj olup olmadığını kontrol ederiz.
            satir, tampon = tampon.split("\n", 1) # Splitle ilk satır sonu karakterinden mesajı ayırırız.
            satir = satir.strip() # Satırla tamamlanmış mesahı tutarız.
            if satir: # Mesaj boş değilse ekrana yazdırırız.
                print(f"\n{satir}")

def istemci_baslat(): # İstemcinin bütün işlemlerini yöneten bir ana fonksiyon kurduk.
    global calisiyor # Ana fonksiyon içinde çalışma durumunu değiştiririz.
    hedef_ip = input("Enter server IP address: ").strip() # Bağlanacağımız sunucunun IP adresini alıyorum.
    if not hedef_ip: # Kullanıcı IP girmezse kontrol ederiz.
        hedef_ip = "127.0.0.1"

    girilen_port = input("Enter server port : ").strip() # Kullanıcıdan sunucu portu girmesini isteriz. Striple ise gereksiz boşlukları temizleriz.
    if girilen_port != "": # Kullancı port girerse onu kullanılır eğer boş bıraksa 1903 portunu seçeriz.
      port = int(girilen_port)
    else:
      port = 1903

    istenen_isim = input("Takma adinizi girin: ").strip() # Takma adı alırız striple baştaki ve sondaki boşlukları tenizleriz.

    v = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Socket oluşturuyoruz.
    v.connect((hedef_ip, port)) # Sunucunun portuna bağlanıyorum.

    v.sendall(f"NICK:{istenen_isim}\n".encode('utf-8')) ## NICK komutuyla takma adı göndeririz. \n bitişi belirtiriz, encode byte'a çeviririz.
     
    
    ilk_cevap = v.recv(1024).decode('utf-8').split("\n")[0].strip() # recv(1024) ile sunucudan kayıt cevabı alırız. Decode ile byte verisini metre dönüştürürüz.
    if ilk_cevap.startswith("HATA:"):# Sunucudan hata var mı yok mu diye kontrol ederiz.
        print("Sunucu Hatasi:", ilk_cevap.split(":", 1)[1])# Hata mesajının içeriğini ayıklar.
        v.close() # Hata durumunda soketi kapatırız.
        return
    elif ilk_cevap.startswith("OK:"):# Kullanıcı adı başarılı olduğunu kontrol ederiz.
        atanan_isim = ilk_cevap.split(":", 1)[1] # Sunucunun kullanıcıya atadığı gerçek kullanıcı adını tutarız.
        print(f"Connected to server. Atanan takma adiniz: {atanan_isim} (Çıkmak için 'cikis' yazın)")

   
    dinleyici = threading.Thread(target=sunucudan_dinle, args=(v,), daemon=True) # Threading ile thread oluştururuz.Targetta hangi fonksiyonun çalışacığını belirler. sunucudan_dinle fonksiyonuna v soketini argüman olarak göndeririz. Daemon ile threadin ana program kapandığında kapanmasını sağlarız. 
    dinleyici.start()# Threadi başlatırız.

    while calisiyor: # İstemci çalıştığı sürece kullanıcıdan mesaj alırız.
        mesaj = input() # Göndermek istediğimiz mesajı alırız.
        if not calisiyor: # Sunucu bağlantısının kopup kopmadığını kontrol ederiz.
            break

        if mesaj.lower() == 'cikis': # Lower ile mesajı küçük harfe çeviririz. Kullanıcı çıkmak isterse sunucuya "EXIT" komutu göndeririz.
            v.sendall(("EXIT" + "\n").encode('utf-8')) # Çıkış komutunu sunucuya göndeririz.
            calisiyor = False # İstemcinin çalışmasını durdururuz.
            break

        v.sendall((mesaj + "\n").encode('utf-8')) # Sunucuya mesajı göndeririz. \n ile bitişi belirtiriz.
    v.close() # Bağlantıyı kapatırız.

  

if __name__ == "__main__":
    istemci_baslat()