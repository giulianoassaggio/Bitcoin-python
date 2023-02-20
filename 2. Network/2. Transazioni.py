"""
Le transazioni sono il cuore di Bitcoin. 
In parole povere, sono trasferimenti di valore da un'entità a un'altra. 
Vedremo nel Capitolo 6 come le "entità" in questo caso siano in realtà smart contract, ma stiamo anticipando più del dovuto. 
Per ora vediamo cosa sono le transazioni in Bitcoin, come appaiono e come vengono analizzate.

COMPONENTI DI UNA TRANSAZIONE

In linea generale, una transazione ha solo quattro componenti principali. Sono:

1. Versione
2. Input
3. Output
4. Locktime
Un'analisi generale di questi campi potrebbe essere utile. 
La versione indica quali funzionalità aggiuntive utilizza la transazione, 
gli input definiscono quali bitcoin vengono spesi, 
gli output definiscono dove vanno i bitcoin e 
il locktime definisce quando questa transazione inizia a essere valida. Esamineremo ogni componente in dettaglio.

Tenendo ciò in mente, possiamo cominciare a costruiew la classe transazione, che chiameremo Tx:
"""

class Tx:
    def __init(self, version, tx_ins, tx_out, locktime, testnet = False):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_out = tx_out
        self.locktime = locktime
        self.testnet = testnet
    def __repr__(self):
        tx_ins = ''
        for tx_in in self.tx_ins:
            tx_ins += tx_in.__repr__() + '\n'
        tx_outs = ''
        for tx_out in self.tx_outs:
            tx_outs += tx_out.__repr__() + '\n'
        return 'tx: {}\nversion: {}\ntx_ins:\n{}tx_outs:\n{}locktime: {}'.format(
            self.id(),
            self.version,
            tx_ins,
            tx_outs,
            self.locktime,
            )
    def id(self):   #l'id di una transazione è ciò che usano  i block explorers per cercarla. é l'hash256 in formato esadecimale della transazione stessa.
        '''Human-readable hexadecimal of the transaction hash'''
        return self.hash().hex()
    def hash(self):
        '''Binary hash of the legacy serialization'''
        return hash256(self.serialize())[::-1]  #riga che non funzionerà finché non parleremo della serializzazione delle transazioni.
                                                # (non abbiamo ancora definito il metodo serialize).

"""
il resto di questo capitopòp si concentrerà sul parsing delle transazioni. Potremmo, a questo punto, scrivere un codice come questo:


    @classmethod
    def parse(cls, serialization):
        version = serialization[0:4] #Qui si assume che la variabile "serialization" sia un array di byte.

Potrebbe tranquillamente funzionare, ma la transazione diventerebbe molto pesante. Idealmente, vorremmo essere 
in grado di effettuare il parsing da uno stream. Ciò ci consentirebbe di non aver bisogno dell'intera transazione serializzata prima di iniziare il parsing, 
e di rilevare eccezioni o errori in modo tempestivo ed essere più efficienti. 
Pertanto, il codice per il parsing di una transazione sarà simile a questo:

    @classmethod
    def parse(cls, stream):
        serialized_version = stream.read(4) #il metodo read ci permetterà di effettuare il parsing mano a mano, senza aspettare l'I/O.

Questo è vantaggioso dal punto di vista ingegneristico poiché lo stream può essere una connessione socket sulla rete o un file. 
Possiamo iniziare a analizzare lo stream immediatamente anziché aspettare che l'intero flusso venga trasmesso o letto prima. 
Il nostro metodo sarà in grado di gestire qualsiasi tipo di flusso e restituirci l'oggetto Tx di cui abbiamo bisogno.
"""

"""
VERSIONE 


Quando si vede un numero di versione in qualcosa, esso dovrebbe fornire all'utente informazioni su cosa rappresenta la versione specificata. 
Ad esempio, se si sta eseguendo Windows 3.1, quel numero di versione sarà diverso rispetto a quello di Windows 8 o Windows 10. 
Si potrebbe specificare solo "Windows", ma aggiungendo il numero di versione, si forniscono maggiori informazioni, tra cui quali funzionalità ha e quali API si possono programmare

In modo simile, le transazioni di Bitcoin hanno numeri di versione. Nel caso specifico, la versione della transazione è generalmente 1, ma in alcuni casi può essere 2 
(le transazioni che utilizzano un opcode chiamato OP_CHECKSEQUENCEVERIFY come definito in BIP0112 richiedono l'uso di una versione maggiore di 1).
 Potresti notare che il valore effettivo in esadecimale è 01000000, che non è 1. Interpretato come un intero little-endian, tuttavia, questo numero è proprio 1 (si rimanda alla discussione del Capitolo 4).

Scriviamo quindi il metodo per il parsing
"""

class Tx:
    #...
    @classmethod
    def parse(cls, s, testnet=False):
        version = little_endian_to_int(s.read(4))
        return cls(version, None, None, None, testnet=testnet)
"""
INPUTS

Ogni input fa riferimento a un output di una transazione precedente. Questo fatto richiede una spiegazione più dettagliata, in quanto non è intuitivo a prima vista.

Gli input di Bitcoin sono costituiti dagli output di una transazione precedente. 
Ciò significa che devi avere ricevuto dei bitcoin in precedenza per poter spendere qualcosa, il che a perfettamente senso: non puoi spendere qualcosa che non hai. 
Ogni input necessita di due cose:
• un riferimento ai bitcoin ricevuti in precedenza
• una prova che questi bitcoin ti appartengono e che puoi spenderli
La seconda parte utilizza ECDSA (Capitolo 3). Per evitare transazioni fraudolente, gli input contengono firme che solo il proprietario della chiave privata può produrre.
Il campo input può contenere più di un input. Ciò è analogo all'uso di una singola banconota da $100 per pagare un pasto da $70 o a usarne invece una da $50 e una da $20. 
Il primo caso richiede un solo input, il secondo ne richiede due. Ci sono situazioni in cui potrebbero essercene ancora di più. 
Nella nostra analogia, potremmo pagare un pasto da $70 con 14 biglietti da $5, o addirittura con 7.000 centesimi. Quindi, 14 input o 7.000 input.

Il numero diinput è la parte sucessiva nella transazione che stiamo analizzanndo, evidenziata nella figuta 5-4.

Guardando il byte, si può vedere che il valore è 01, il che indica che questa transazione ha un solo input. 
Anche se potrebbe essere facile pensare che ogni volta ci sia un solo byte, in realtà non è così. Infatti, un byte è composto da 8 bit,
quindi qualsiasi valore superiore a 255 input non potrebbe essere espresso in un singolo byte.

Qui entra in gioco il varint. Varint è l'abbreviazione di "variable integer", cioè un modo per codificare un numero intero in byte che variano da 0 a 2^64 - 1. 
Potremmo naturalmente riservare sempre 8 byte per il numero di input, ma sarebbe uno spreco di spazio considerevole se ci aspettiamo che il numero di input sia r
elativamente piccolo (ad esempio, meno di 200). Questo è il caso del numero di input in una transazione normale, quindi l'uso di varint aiuta a risparmiare spazio. 
Di seguito il funzionamento:

I variable intergers seguono le seguenti regole:

-> Se il numero è inferiore a 253, viene codificato come un singolo byte (ad esempio, 100 diventa 0x64).
-> Se il numero è compreso tra 253 e 2^16-1, si utilizza il byte 253 (fd) e poi si codifica il numero in 2 byte in little-endian (ad esempio, 255 diventa 0xfdff00, 555 diventa 0xfd2b02).
-> Se il numero è compreso tra 2^16 e 2^32-1, si utilizza il byte 254 (fe) e poi si codifica il numero in 4 byte in little-endian (ad esempio, 70015 diventa 0xfe7f110100).
-> Se il numero è compreso tra 2^32 e 2^64-1, si utilizza il byte 255 (ff) e poi si codifica il numero in 8 byte in little-endian (ad esempio, 18005558675309 diventa 0xff6dc7ed3e60100000).

Le due funzioni in helper.py che verranno utilizzate per analizzare e serializzare i campi varint sono read_varint e encode_varint. 
La prima funzione prende un byte stream come input e restituisce una tupla di due valori: il numero decodificato come intero e il numero di byte utilizzati per codificare il numero. 
La seconda funzione prende un intero come input e restituisce il byte stream corrispondente.
Eccone il codice:
"""

def read_varint(s):
    '''read_varint reads a variable integer from a stream'''
    i = s.read(1)[0]
    if i == 0xfd:
        # 0xfd means the next two bytes are the number
        return little_endian_to_int(s.read(2))
    elif i == 0xfe:
        # 0xfe means the next four bytes are the number
        return little_endian_to_int(s.read(4))
    elif i == 0xff:
        # 0xff means the next eight bytes are the number
        return little_endian_to_int(s.read(8))
    else:
        # anything else is just the integer
        return i

def encode_varint(i):
    '''encodes an integer as a varint'''
    if i < 0xfd:
        return bytes([i])
    elif i < 0x10000:
        return b'\xfd' + int_to_little_endian(i, 2)
    elif i < 0x100000000:
        return b'\xfe' + int_to_little_endian(i, 4)
    elif i < 0x10000000000000000:
        return b'\xff' + int_to_little_endian(i, 8)
    else:
        raise ValueError('integer too large: {}'.format(i))

"""
Tornando agli input, ognuno di essi contiene quattro campi. I primi due puntatno al precedente output e gli ultimi due definiscono come l'uotput precedente può essere speso. Sono così  formati:
1. ID della transazione precedente 
2. indice della transazione precentente
3. Scriptsig
4. Sequence

Come già spiegato, ogni input si riferisce a un precedente output. l'ID della tx precedente (1) è l'hash256 del contenuto della stessa,, cosa che la identifica in modo univoco, dal mmoemnto che
la probabilità di ottere due hash uguali è talmente bassa che si può considerare nulla.
Come vedremo, ogni tx necessita di almeno un output, ma può averne più di uno.
Di conseguenza, biogna specifiare di preciso quale output della transazione stiamo spendendo, che è contenuto nell'indice della transazione (2). si noti che l'ID è di 32 byte e l'indice di 4, 
entrambi little-endian.
Lo scriptsig (3) ha a che fare con il linguaggio degli smart contracts di Bitcoin, "Script", che discuteremo più a fondo nel capitolo 6. Per il momento, basi pensare Scriptsig
come l'apertura di un box chiuso, qualcosa che piò essere fatto solo fal proprietario dell'output precedente.. Il campo Scriptsig è di lunghezza varibaile, a differenza di molto di quanto visto
finora. Questa caratteristica ci obbliga però a definirne esplicitamente la lunghezza, motivo per cui è precenduto da un varint che dice proprio quanto è lungo.
La sequence (4) era originariamente intesa come un modo per fare ciò che Satoshi chiamava "High Frequency Trades", col campo Locktime, ma è ora usato per il replace-by-frr (RBF) e OP_CHECKSEQUENCEVERIFY.
Anche'eso è compostoo da fino a 4 bytes little-endian. I campi dell'input sono visibili in figura 5-5.

PICCOLO ESCURSUS SU SEQUENCE E LOCKTIME

"""