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
