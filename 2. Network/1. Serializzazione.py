"""
Abbiamo già creato un sacco di classi, tra cui PrivateKey, S256Point e Signature. C'è ora bisogno di cominciare a pensare a un modo per trasmettere questi
oggetti a altri computer nel network. è qui che entra in gioco la cosiddetta serializzazione, Ci serve comunicare o storare un S256Point o una firma o una
chiave privata, e vorremmo farlo in modo efficiente.

Uncompressed SEC Format
comincieremo dalla classe S256Point, che è quella relativa alla chiave pubblica. Ricordiamo che quest'ultima non è altro che una coordinata nella forma (x,y).
Come possiamo serializzare questo dato? Beh, esiste già uno standard per serializzare le chiavi pubbliche ECDSA, chiamato "Standards for Efficient 
Cryptography (SEC)" e, come suggerisce il nome, ha costi minimali in termini di risorse. Ci sono due tipi di formato SEC: compressed e uncompressed.
Vedremo per primo quest'ultimo.
Così è come l'uncompressed SEC format per un dato punto P=(x,y) è generato:
1. Inizia con il byte di prefisso, che è 0x04
2. Dopodiché viene attaccata la coordinata x come un intero big-endian
3. Infine allo stesso modo biene attaccata la coordinata x

Programmare la serializzazione nel formato SEC uncompressed è abbastanza diretto. La parte un attimo più complicata è la conversione di un numero di 256bit
in uno di 32byte, big-endian. Questo il codice:
"""

class S256Point(Point):
  #...
  def sec(self):
  #returns the binary version of the SEC format
    return b'\x04' + self.x.num.to_bytes(32, 'big') + self.y.num.to_bytes(32, 'big')    
    #to_bytes è un metodo di python3 per convertire un numero in byte. il primo argomento è la quantità di byte, la seconda specifica il tipo di "endian".
    
"""
Compressed SEC format
Ricordiamo che per ogni coordinata x, ci sono al massimo 2 coordinate y a essa relative, a causa del termine y^2 nell'equazione della curva ellittica, questo
sia nel campo R che in un campo finito. Se conosciamo x, la coordinata y deve essere y o p-y. Dal momento che p è un numero primo maggiore di 2, p è per
forza dispari. Di conseguenza, se y è pari, (p-y) è dispari, e viceversa. Questo è qualcosa che possiamo usare a nostro vantaggio per accorciare 
l'uncompressed SEC format: possiamo fornire la coordinata x e la parità della coordinata y, comprimendo quest'ultima a un singolo byte di informazione.
Questa la serializzazione del compressed SEC format per un dato punto P=(x,y):
1. Si parte col byte di prefisso: se y è pari, si userà il byte 0x02, altrimenti 0x03
2. Si aggiunge poi in coda la coordinata in 32byte come intero big-endian.

La procedura è nuovamente banale, si può aggiornare il metodo precedente per far sì che possa trattare il formato compresso.
"""

class S256Point(Point):
  # ...
  def sec(self, compressed=True):
    if compressed:
      if self.y.num % 2 == 0:
        return b'\x02' + self.x.num.to_bytes(32, 'big')
      else:
        return b'\x03' + self.x.num.to_bytes(32, 'big')
    else:
      return b'\x04' + self.x.num.to_bytes(32, 'big') + self.y.num.to_bytes(32, 'big')
    
"""
Il grande vantaggio del formato compresso è che necessita di soli 33 bytes invece di 65. Un risparmio non da poco, se esteso a milioni di transazioni.
A questo punto, c'è da chiedersi come calcolare analiticamente y data la coordinata x. Per farlo, serve calcolare la radice quadrata in un campo finito.
Matematicamente: trova w tale che w^2 = v quando conosciamo v.
Si scopre che se l'ordine del campo finito p % 4 = 3, la si calcol abbastanza facilmente:
Innanzitutto, conosciamo p%4=3, che implica (p+1)%4=0, ovvero (p+1)%4 è un intero.
Per definizione, w^2=v. Dal piccolo teorema di Fermat, w^(p–1) % p = 1, che significa 
w^2 = w^2*1 = w^2*w^(p–1) = w^(p+1). Dal momento che p è dispari (numero primo), possiamo dividere (p+1) per due e ottenere ancora un intero, il che implica: w = w^((p+1)/2).
Possiamo ora sfruttare il fatto che (p+1)/a sia intero in questo modo:
w = w^((p+1)/2) = w^(2(p+1)/4) = (w^2)^((p+1)/4) = v^((p+1)/4).
Abbiamo quindi trovato che se w^2=v e  p%4=3, allora w=v^((p+1)/4).

L'ordine usato in secp256k1 è tale che la seconda condizione è soddisfatta, quindi possiamo usare questa fomula per la radice. 
Il w così trovato è una delle due possibili soluzioni, l'altra è (p-w). Questo perché nel calcolo del quadrato, la base positiva e quella negativa hanno lo stesso risultato. 
Possiamo quindi aggiungere un metodo generale alla classe S256Field:
"""
class S256Field(FieldElement):
  def sqrt(self):
    return self**((P + 1) // 4)
  
"""
Quando ci viene fornita una chiave pubblica serializzata in formato SEC, possiamo scrivere un metodo di parsing per capire quale y ci serve:
""" 
  
class S256Point:
  def parse(self, sec_bin):
    #ritorna un oggetto "Point" a partire da un SEC binario (non esadecimale)
    if sec_bin[0] == 4:   #il formato non compresso è banale
      x = int.from_bytes(sec_bin[1:33], 'big')
      y = int.from_bytes(sec_bin[33:65], 'big')
      return S256Point(x=x, y=y)
    is_even = sec_bin[0] == 2   #la parità è data dal primo byte
    x = S256Field(int.from_bytes(sec_bin[1:], 'big'))
    # lato destro dell'equazione y^2 = x^3 + 7
    alpha = x**3 + S256Field(B)
    # risoluzione del lato sinistro
    beta = alpha.sqrt()   #facciamo la radice del lato destro dell'equazione per ottenere y
    if beta.num % 2 == 0: #determiniamo la parità, restituendo il punto corretto
      even_beta = beta
      odd_beta = S256Field(P - beta.num)
    else:
      even_beta = S256Field(P - beta.num)
      odd_beta = beta
    if is_even:
      return S256Point(x, even_beta)
    else:
      return S256Point(x, odd_beta)

"""
DER SIGNATURES
Un'altra classe di cui abbiamo bisogno per la serializzazione è SIGNATURE. Come il formato SEC, deve codificare due diversi numeri: r e s.
Sfortunatamente, a differenza di S256Point, Signature non può essere conpressa, dal momento che s non può essere derivata dalla sola r.
Il formato standard per la serializzazione delle firme si chiama "Distinguished Encoding Rules" (DER). Ed è proprio il formato scelto da Satoshi, probabilmente
erché era già esistente nel 2008, era supportato nella libreria di OpenSSL (usata in Bitcoin al tempo) e era abbastanza facile per essere adottato, meglio di crearne
uno nuovo da zero. 
Il formato DER è così definito:
1. inizia con il byte 0x30
2. codifica la lunghezza del resto della firma (di nora 0x44 o 0x45) e la aggiunge in coda
3. aggiunge in coda il byte marcatore 0x02
4. Codifica r come un intero big-endian, Converte r in un intero big-endian, ma aggiunge il byte 0x00 in testa se il primo byte di r è maggiore o uguale a 0x80. Poi, prepone la lunghezza risultante a r e lo aggiunge al risultato.
5. Aggiunge in coda il byte marcatore 0x02
6. Converte s in un intero big-endian, ma aggiunge il byte 0x00 in testa se il primo byte di s è maggiore o uguale a 0x80. Poi, prepone la lunghezza risultante a s e lo aggiunge al risultato.

Le regole "strane" dei punti 4 e 6 con il primo byte che inizia con un valore maggiore o uguale a 0x80 sono necessarie poiché DER è un formato di codifica generale che consente di codificare anche numeri negativi. 
Il primo bit uguale a 1 indica che il numero è negativo. Tutti i numeri di una firma ECDSA sono però positivi, quindi è necessario aggiungere il byte 0x00 in testa se il primo bit è zero, il che equivale a dire che il primo byte è maggiore o uguale a 0x80.
Dal momento che sappiamo che r è un intero di 256 bit, r sarà espresso con al massimo 32 byte, in formato big-endian. Può capitare che il primo byte sia maggiore o uguale a 0x80, da cuiabbiamo che il punto 4 può essere lungo al massimo 33 byte. 
Al contempo, se r è un numero relativamente piccolo, potrebbe essere inferiore a 32 byte. Lo stesso vale per s e per il punto 6.
"""
"""
Questo il relativo codice in py:
"""
    class Signature:
    #...
      def der(self):
        rbin = self.r.to_bytes(32, byteorder='big')
        # remove all null bytes at the beginning
        rbin = rbin.lstrip(b'\x00')
        # if rbin has a high bit, add a \x00
        if rbin[0] & 0x80:
          rbin = b'\x00' + rbin
        result = bytes([2, len(rbin)]) + rbin 
          #In Python 3, è possibile convertire una lista di numeri 
          #in corrispondenti byte utilizzando la funzione 
          #bytes([some_integer1, some_integer2]).
        sbin = self.s.to_bytes(32, byteorder='big')
        # remove all null bytes at the beginning
        sbin = sbin.lstrip(b'\x00')
        # if sbin has a high bit, add a \x00
        if sbin[0] & 0x80:
          sbin = b'\x00' + sbin
        result += bytes([2, len(sbin)]) + sbin
        return bytes([0x30, len(result)]) + result

"""
In generale, questo è un modo inefficiente per codificare r e s poiché ci sono almeno 6 byte che non sono strettamente necessari.

Base58

Nei primi giorni di Bitcoin, i bitcoin erano assegnati alle chiavi pubbliche specificate nel formato SEC non compresso e venivano poi riscattati utilizzando le firme DER. 
Per ragioni che vedremo nel Capitolo 6, l'utilizzo di questo particolare script molto semplice si è rivelato sia spreco per la memorizzazione degli UTXO che leggermente meno sicuro rispetto 
agli script in uso ora più comunemente. Per ora, esamineremo cosa sono gli indirizzi e come vengono codificati.

Trasmissione della Chiave pubblica
Perché Alice possa pagare Bob, deve sapere dove inviare i soldi. 
Questo è vero tanto per Bitcoin, quanto per qualsiasi metodo di pagamento. Poiché Bitcoin è una forma di pagamento digitale "al portatore", l'indirizzo può essere qualcosa come una chiave pubblica in un sistema di crittografia asimmetrica. 
Purtroppo, il formato SEC, in particolare quello non compresso, è un po' troppo lungo (65 o 33 byte). Inoltre, i 65 o 33 byte sono in formato binario, che si può dire non sia molto facile da leggere, almeno in forma grezza
Per essere umanamente utilizzabile, ci sono tre considerazioni principali da fare.
La prima è che la chiave pubblica sia leggibile (facile da scrivere a mano e non troppo difficile da confondere, ad esempio al telefono). La seconda è che sia sufficientemente breve. 
La terza è che sia sicura (così che sia più difficile commettere errori).
Quindi, come otteniamo leggibilità, compressione e sicurezza? Se esprimiamo il formato SEC in esadecimale (4 bit per carattere), 
la sua lunghezza è raddoppiata (130 o 66 caratteri). Possiamo fare di meglio?
Potremmo utilizzare qualcosa come Base64, che può esprimere 6 bit per carattere. Questo si tradurrebbe in 87 caratteri per il formato SEC non compresso e 44 caratteri per quello compresso. 
L'inconveniente è che Base64 è incline a errori, poiché molte lettere e numeri si assomigliano (0 e O, l e I, - e _). Rimuovendo questi caratteri, otteniamo un risultato che ha una buona leggibilità e 
una compressione decente (circa 5,86 bit per carattere). Infine, possiamo aggiungere un checksum alla fine per garantire che gli errori siano facili da rilevare. Questa costruzione si chiama Base58. 
Riassumendo, quindi, invece degli esadecimali (base 16) o di Base64, codifichiamo i numeri in Base58.
La meccanica effettiva dell'encoding in Base58 è la seguente. Si utilizzano tutti i numeri, le lettere maiuscole e minuscole, ad eccezione di 0/O e l/I, che si confondono facilmente. Ciò ci lascia con 10 + 26 + 26 - 4 = 58 caratteri.
Ciascuno di questi caratteri rappresenta una cifra in Base58. Possiamo codificare utilizzando una funzione che fa esattamente questo:
"""
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
# ...
def encode_base58(s):
  #This function will take any bytes and convert them to Base58.
  count = 0
  for c in s:
    #Lo scopo di questo ciclo è determinare quanti dei byte all'inizio sono byte 0. 
    #Vogliamo aggiungerli di nuovo alla fine.
    if c == 0:
      count += 1
    else:
      break
  num = int.from_bytes(s, 'big')
  prefix = '1' * count
  result = ''
  while num > 0:
    #questo è il loop che identifica quale carattere Base58 usare
    num, mod = divmod(num, 58)
    result = BASE58_ALPHABET[mod] + result
  return prefix + result
  #Infine, anteponiamo tutti gli zeri che abbiamo contato all'inizio, 
  #perché altrimenti non comparirebbero come "prefisso". 

"""
Perché Base58 sta diventando obsoleto
Base58 è stato utilizzato per molto tempo e, sebbene renda la comunicazione un po' più facile rispetto a qualcosa come Base64, non è poi così conveniente. 
La maggior parte delle persone preferisce copiare e incollare gli indirizzi e se hai mai provato a comunicare un indirizzo Base58 vocalmente, sai che può diventare un incubo.
Di gran lunga migliore è il nuovo standard Bech32, definito nel BIP0173. Bech32 utilizza un alfabeto di 32 caratteri solo numeri e lettere minuscole, esclusi 1, b, i e o. 
Per ora, utilizzato solo per Segwit (Capitolo 13).

Formato dell'indirizzo
I 264 bit del formato SEC compresso sono ancora un po' troppo lunghi, e un po' meno sicuri (vedi Capitolo 6). Per accorciare l'indirizzo e aumentare la sicurezza, possiamo usare l'hash ripemd160.
Non utilizzando direttamente il formato SEC, possiamo passare da 33 a 20 byte, accorciando significativamente l'indirizzo. Ecco come viene creato un indirizzo Bitcoin:

    1. Per gli indirizzi di Mainnet, iniziare con il prefisso 0x00, per la testnet 0x6f.
    2. Prendere il formato SEC (compresso o non compresso) e fare un'operazione sha256 seguita dall'operazione di hash ripemd160, 
      la combinazione di queste due operazioni è chiamata operazione hash160.
    3. Combinare il prefisso del punto 1 e l'hash risultante del punto 2.
    4. Fare un hash256 del risultato del punto 3 e prendere i primi 4 byte.
    5. Prendere la combinazione di #3 e #4 e codificarla in Base58.
    Il risultato del passaggio 4 di questo processo è chiamato checksum. 
    Possiamo fare i passaggi 4 e 5 in una sola volta in questo modo:
"""

  def encode_base58_checksum(b):
    return encode_base58(b + hash256(b)[:4])

"""
possiamo anche implementare direttamente l'operazione hash160 in helper.py :
"""
def hash160(s):
  #sha256 followed by ripemd160
  return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()

"""
Possiamo anche aggiornare la classe S256Point con i metodi hash160 e address:
"""

  class S256Point:
    #...
    def hash160(self, compressed=True):
      return hash160(self.sec(compressed))
    def address(self, compressed=True, testnet=False):
      #Returns the address string
      h160 = self.hash160(compressed)
      if testnet:
        prefix = b'\x6f'
      else:
        prefix = b'\x00'
      return encode_base58_checksum(prefix + h160)

"""
Il formato WIF (Wallet Import Format) è una serializzazione della chiave privata progettata per essere leggibile dall'uomo. 
Utilizza la stessa codifica Base58 usata per gli indirizzi. Per creare il formato WIF:

    1. Per le chiavi private di mainnet, iniziare con il prefisso 0x80, per testnet 0xef.
    2. Codificare il segreto in big-endian di 32 byte.
    3. Se il formato SEC utilizzato per l'indirizzo della chiave pubblica era compresso, aggiungere un suffisso di 0x01.
    4. Combinare il prefisso del punto 1, il segreto serializzato del punto 2 e il suffisso del punto 3.
    5. Eseguire un hash256 del risultato del punto 4 e prendere i primi 4 byte.
    6. Prendere la combinazione del punto 4 e del punto 5 e codificarla in Base58.

Ora possiamo creare il metodo wif sulla classe PrivateKey:
"""


class PrivateKey
  #...
  def wif(self, compressed=True, testnet=False):
    secret_bytes = self.secret.to_bytes(32, 'big')
    if testnet:
      prefix = b'\xef'
    else:
      prefix = b'\x80'
    if compressed:
      suffix = b'\x01'
    else:
      suffix = b''
    return encode_base58_checksum(prefix + secret_bytes + suffix)

  """
È importante sapere come vengono fatti i byte big-endian e little-endian in Python, poiché nei prossimi capitoli analizzeranno 
abbastanza spesso il parsing e la serializzazione di numeri in big-endian/little-endian. 
In particolare, Satoshi ha utilizzato molto la codifica little-endian per Bitcoin e, sfortunatamente, non c'è una regola facile da imparare 
su dove viene utilizzato il little-endian e dove viene utilizzato il big-endian. Ricorda che il formato SEC utilizza la codifica big-endian, 
così come gli indirizzi e WIF. A partire dal Capitolo 5, useremo molto di più la codifica little-endian.


In questo capitolo abbiamo imparato come serializzare molte diverse strutture che abbiamo creato nei capitoli precedenti. 
Adesso ci concentreremo sul parsing e sulla comprensione delle transazioni.
"""

