from os import remove
from re import X
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
from pygraphviz import AGraph

class etichetta:
    
    def __init__(self, valore):
        self.valore=valore
        self.antenati=list()
        self.discendenti=list()
        self.conviventi=list()
        self.non_rel=list()

    def aggiungi_relazione(self, relazione, valore):
        if relazione=="Antenato":
            self.antenati += valore
        elif relazione=="Discendente":
            self.discendenti += valore
        elif relazione=="Convivente":
            self.conviventi += valore
        elif relazione=="Non relazionato":
            self.non_rel += valore

class terna_compatibile:
    def __init__(self, valore, configurazioni):
        self.valore = valore
        self.configurazioni = configurazioni

   
def read_dotfile(path, labeled_only=False, exclude=None): #Legge il file dell'albero
    T = nx.DiGraph(nx.drawing.nx_agraph.read_dot(path))
    return build_tree(T, labeled_only=labeled_only, exclude=exclude)

def build_tree(T, labeled_only=False, exclude=None): #Costruisce l'albero
    if not nx.is_tree(T):
        raise ValueError("Not a valid tree.")

    label_to_nodes = defaultdict(set)
    label_set = set()
    node_to_labels = defaultdict(set)

    for node in T.nodes(data=True):
        id_node = node[0]

        if not 'label' in node[1] and not labeled_only:
            node[1]['label'] = str(node[0])
        if not 'label' in node[1] and labeled_only:
            node[1]['label'] = ''
            continue

        labels = node[1]['label'].split(',')
        for l in labels:
            if exclude:
                if l in exclude:
                    continue

            label_set.add(l)
            label_to_nodes[l].add(id_node)
            node_to_labels[id_node].add(l)

    label_set = sorted(list(label_set))

    return Tree(T, label_to_nodes, node_to_labels, label_set)

class Tree:
    def __init__(self, T, label_to_nodes, node_to_labels, label_set): #Classe albero
        self.T = T
        self.label_to_nodes = label_to_nodes
        self.node_to_labels = node_to_labels
        self.label_set = label_set
        self.label_list = self.build_etichette()

        self.LCA = LCA(self.T,
                       self.label_to_nodes,
                       self.node_to_labels)
    
    def build_etichette(self):
        x=list()
        for e in self.label_set:
            if e != "root":
                x.append(etichetta(e))
        return x
                
class LCA:
    def __init__(self, T, T_label_to_node, T_node_to_labels): #Classe LCA
        self.LCA_dict = dict()
        self.LCA_label_dict = T_label_to_node
        self.LCA_node2lbl = T_node_to_labels
        for lca in nx.tree_all_pairs_lowest_common_ancestor(T):
            self.LCA_dict[(lca[0][0], lca[0][1])] = lca[1]

    def lca_nodes(self, node1, node2):
        try:
            return self.LCA_dict[node1, node2]
        except:
            return self.LCA_dict[node2, node1]

    def lca_labels(self, label1, label2):
        nodes1 = self.LCA_label_dict[label1]
        nodes2 = self.LCA_label_dict[label2]

        lca_mset = Counter()
        for n1 in nodes1:
            for n2 in nodes2:
                lca_mset.update(self.lca_nodes(n1, n2))

        return lca_mset

    def label_to_node(self, label):
        return self.LCA_label_dict[label]

    def node_to_labels(self, node):
        return self.LCA_node2lbl[node]

    def __str__(self):
        return str(self.LCA_dict)

#Metodi per relazioni
def build_relazioni_ricorsione(tree, nodo): #Aggiunta di relazioni
    lista_discendenti=list()
    
    for figlio in tree.T.successors(nodo):
        lista_aggiornamento = build_relazioni_ricorsione(tree, figlio)
        lista_discendenti += lista_aggiornamento
        #Non Relazionati
        for figlio2 in tree.T.successors(nodo):
            if figlio != figlio2:
                build_non_relazionate(tree, figlio2, lista_aggiornamento)

    for eti_in_nodo in tree.node_to_labels[nodo]:
        if eti_in_nodo != "root":
            for eti_in_oggetto in tree.label_list:
                if (eti_in_nodo == eti_in_oggetto.valore):
                    #Discendenti
                    eti_in_oggetto.discendenti += lista_discendenti
                    #Conviventi
                    lista_conviventi=list(tree.node_to_labels[nodo])
                    lista_conviventi.remove(eti_in_oggetto.valore)
                    eti_in_oggetto.conviventi += lista_conviventi
                for elemento in lista_discendenti:
                    if (eti_in_oggetto.valore == elemento):
                        #Antenati
                        eti_in_oggetto.antenati += eti_in_nodo
            

    for etichetta_in_nodo in tree.node_to_labels[nodo]:
        lista_discendenti += etichetta_in_nodo
    
    return lista_discendenti
    
def build_non_relazionate(tree, nodo, lista): #Aggiunta di etichette non relazionate
    for eti_in_nodo in tree.node_to_labels[nodo]:
        for eti_in_oggetto in tree.label_list:
            if (eti_in_nodo == eti_in_oggetto.valore):
                eti_in_oggetto.non_rel += lista
    
    for figlio in tree.T.successors(nodo):
        build_non_relazionate(tree, figlio, lista)

def build_relazioni(tree): #Metodo per la chiamata ai metodi che aggiungono relazioni
    iterator = iter(tree.label_to_nodes['root'])
    nodo_radice = next(iterator, None)
    build_relazioni_ricorsione(tree, nodo_radice)

def visualizza_relazioni(tree): #Visualizzazione delle relazioni
    for x in tree.label_list: 
        print("Relazioni di " + x.valore)
        print("Antenati: ")
        print(x.antenati)
        print("Discendenti: ")
        print(x.discendenti)
        print("Conviventi: ")
        print(x.conviventi)        
        print("Non relazionati: ")
        print(x.non_rel)
        print("-------------------------------")

def mp3_relazioni(tree): 
    build_relazioni(tree)
    #visualizza_relazioni(tree)

#Metodi per MTT
def MTT_date_3_etichette(a, b, c): #Comprensione della configurazione MTT con 3 etichette
    configurazione = 0;
    if len(a.discendenti) == 2 or len(b.discendenti) == 2 or len(c.discendenti) == 2 : #tutte
        #1,5,7
        if len(a.conviventi) == 1 or len(b.conviventi) == 1 or len(c.conviventi) == 1:
            #7
            configurazione = 7
        elif len(a.non_rel) == 1 or len(b.non_rel) == 1 or len(c.non_rel) == 1:
            #5
            configurazione = 5
        else:
            #1
            configurazione = 1    
    elif len(a.non_rel) == 0 or len(b.non_rel) == 0 or len(c.non_rel) == 0: #2,3,4,6,8,9
        if len(a.non_rel) == 0 and len(b.non_rel) == 0 and len(c.non_rel) == 0: #2,3,4,8
            #2,4
            #uso di LCA
            configurazione = 24
        elif len(a.conviventi) > 0 or len(b.conviventi) > 0 or len(c.conviventi) > 0: #3,8
            #8
            configurazione = 8
        else:
            #3   
            configurazione = 3  
    elif len(a.conviventi) == 2 and len(b.conviventi) == 2 and len(c.conviventi) == 2: #6,9
        #9
        configurazione = 9
    else:
        #6
        configurazione = 6
    return configurazione    

def filtro_condivise(lista_etichette1, lista_etichette2): #ritorna elementi condivisi tra due liste
    lista_etichette_condivise = list()
    for eti1 in lista_etichette1:
        for eti2 in lista_etichette2:
            if eti1.valore == eti2.valore and eti1.valore != "root":
                lista_etichette_condivise += eti1.valore
    
    return lista_etichette_condivise

def etichetta_in_relazione(etichetta1, etichetta2, valore): #dice se è con che relazione un valore è relazionato con un'etichetta
    è_presente = False
    relazione = ""
    if (valore in etichetta1.antenati and valore in etichetta2.antenati):
        è_presente = True
        relazione = "Antenato"
    elif (valore in etichetta1.discendenti and valore in etichetta2.discendenti):
        è_presente = True
        relazione = "Discendente"
    elif (valore in etichetta1.conviventi and valore in etichetta2.conviventi):
        è_presente = True
        relazione = "Convivente"
    elif (valore in etichetta1.non_rel and valore in etichetta2.non_rel):
        è_presente = True
        relazione = "Non relazionato"

    return è_presente, relazione

def etichetta_in_antenati(etichetta1, etichetta2, valore): #dice quante volta il valore è nella relazione
    è_presente = False
    cont1 = 0
    cont2 = 0
    for x in etichetta1.antenati:
        if x == valore:
            cont1 += 1
    for x in etichetta2.antenati:
        if x == valore:
            cont2 += 1
    if cont1 > 0 or cont2 > 0:
        è_presente = True
    
    return è_presente,min(cont1,cont2)

def etichetta_in_discendenti(etichetta1, etichetta2, valore):
    è_presente = False
    cont1 = 0
    cont2 = 0
    for x in etichetta1.discendenti:
        if x == valore:
            cont1 += 1
    for x in etichetta2.discendenti:
        if x == valore:
            cont2 += 1
    if cont1 > 0 or cont2 > 0:
        è_presente = True
    
    return è_presente,min(cont1,cont2)

def etichetta_in_conviventi(etichetta1, etichetta2, valore):
    è_presente = False
    cont1 = 0
    cont2 = 0
    for x in etichetta1.conviventi:
        if x == valore:
            cont1 += 1
    for x in etichetta2.conviventi:
        if x == valore:
            cont2 += 1
    if cont1 > 0 or cont2 > 0:
        è_presente = True
    
    return è_presente,min(cont1,cont2)

def etichetta_in_non_rel(etichetta1, etichetta2, valore):
    è_presente = False
    cont1 = 0
    cont2 = 0
    for x in etichetta1.non_rel:
        if x == valore:
            cont1 += 1
    for x in etichetta2.non_rel:
        if x == valore:
            cont2 += 1
    if cont1 > 0 or cont2 > 0:
        è_presente = True
    
    return è_presente,min(cont1,cont2)

def build_compatibilità_a_2(lista_etichette1, lista_etichette2): #compatibilità a 2 tra due liste di etichette
    lista_etichette_condivise = filtro_condivise(lista_etichette1, lista_etichette2)
    lista_compatibili = list()
    for e in lista_etichette_condivise:
       if e != "root":
          lista_compatibili.append(etichetta(e))

    for x in lista_etichette1:
        for y in lista_etichette2:
            if x.valore==y.valore:
                for z in lista_etichette_condivise:
                    for w in lista_compatibili:
                        if w.valore == x.valore:
                            #qui sotto posso predictare le configurazioni MTT comp3
                            a,quantità = etichetta_in_antenati(x,y,z)
                            if a:
                                for _ in range(quantità):
                                    w.antenati += z
                            a,quantità = etichetta_in_discendenti(x,y,z)
                            if a:
                                for _ in range(quantità):
                                    w.discendenti += z
                            a,quantità = etichetta_in_conviventi(x,y,z)
                            if a:
                                for _ in range(quantità):
                                    w.conviventi += z
                            a,quantità = etichetta_in_non_rel(x,y,z)
                            if a:
                                for _ in range(quantità):
                                    w.non_rel += z
                            
    return lista_compatibili
    
def build_compatibilità_a_3_dalla_2(lista_compatibili_a_2): #compatibilità a 3 data quella a 2
    terne_compatibili = list()
    terne_di_ritorno = list()
    for x in lista_compatibili_a_2:
        for y in lista_compatibili_a_2:
            for z in lista_compatibili_a_2:
                if (x.valore != y.valore) and (x.valore != z.valore) and (y.valore != z.valore):
                    """
                    #Devo contare quante in quali relazioni
                    a1,a_b=valore_in_relazioni(x, y.valore)
                    a2,a_c=valore_in_relazioni(x, z.valore)
                    b1,b_a=valore_in_relazioni(y, x.valore)
                    b2,b_c=valore_in_relazioni(y, z.valore)
                    c1,c_a=valore_in_relazioni(z, x.valore)
                    c2,c_b=valore_in_relazioni(z, y.valore)
                    print(a_b)
                    print(a_c)
                    print(b_a)
                    print(b_c)
                    print(c_a)
                    print(c_b)
                    # solo in fratelli e non relazionati ho 6 relazioni uguali
                    
                    if a1 and a2 and b1 and b2 and c1 and c2  and (z != x.valore and z != y.valore and x.valore != y.valore):
                        a=etichetta(x.valore)
                        b=etichetta(y.valore)
                        c=etichetta(z.valore)
                        a.aggiungi_relazione(a_b, y.valore)
                        a.aggiungi_relazione(a_c, z.valore)
                        b.aggiungi_relazione(b_a, x.valore)
                        b.aggiungi_relazione(b_c, z.valore)
                        c.aggiungi_relazione(c_a, x.valore)
                        c.aggiungi_relazione(c_b, y.valore)
                        configurazione = MTT_date_3_etichette(a, b, c)  
                    """   

                    terna = x.valore + y.valore + z.valore
                    terna = (','.join(sorted(terna))) #.replace(',','')  
                    configurazioni = configurazione_da_comp2_e_etichetta(x, y, z)
                    if terna not in terne_compatibili and configurazioni != []:
                        terne_compatibili.append(terna)
                        nuova_terna = terna_compatibile(terna, configurazioni)
                        terne_di_ritorno.append(nuova_terna)
    return terne_di_ritorno

def configurazione_da_comp2_e_etichetta(a, b, c): #configurazione con uso di logica booleana
    configurazioni = list() 
    if a.valore in b.antenati or a.valore in b.discendenti:
        if (a.valore in c.conviventi and b.valore in c.discendenti):# or (b.valore in c.conviventi and a.valore in c.discendenti):
            configurazioni.append(6)
        if (a.valore in c.antenati and b.valore in c.conviventi):# or (b.valore in c.antenati and a.valore in c.conviventi):
            configurazioni.append(7)
        if (a.valore in c.antenati and b.valore in c.non_rel):# or (b.valore in c.antenati and a.valore in c.non_rel):
            configurazioni.append(5)
        if (a.valore in c.antenati and b.valore in c.antenati) or (a.valore in c.discendenti and b.valore in c.discendenti):
            configurazioni.append(1)
        if (a.valore in c.non_rel and b.valore in c.non_rel):
            configurazioni.append(3)
    if a.valore in b.non_rel:
        if (a.valore in c.non_rel and b.valore in c.non_rel):
            configurazioni.append(24)
        if (a.valore in c.antenati and b.valore in c.non_rel):# or (b.valore in c.antenati and a.valore in c.non_rel):
            configurazioni.append(3)
        if (a.valore in c.discendenti and b.valore in c.discendenti):
            configurazioni.append(5)
        if (a.valore in c.conviventi and b.valore in c.non_rel):# or (b.valore in c.conviventi and a.valore in c.non_rel):
            configurazioni.append(8)
    if a.valore in b.conviventi:
        if (a.valore in c.antenati and b.valore in c.antenati):
            configurazioni.append(6)
        if (a.valore in c.discendenti and b.valore in c.discendenti):
            configurazioni.append(7)
        if (a.valore in c.non_rel and b.valore in c.non_rel):
            configurazioni.append(8)
        if (a.valore in c.conviventi and b.valore in c.conviventi):
            configurazioni.append(9)
    return configurazioni


def valore_in_relazioni(etichetta, valore):
    x=False
    relazione=""
    if valore in etichetta.antenati:
        x=True
        relazione="Antenato"
    elif valore in etichetta.discendenti:
        x=True
        relazione="Discendente"
    elif valore in etichetta.conviventi:
        x=True
        relazione="Convivente"
    elif valore in etichetta.non_rel:
        x=True
        relazione="Non relazionato"

    return x,relazione     

#Main
tree1 = read_dotfile('trees/tree30.gv')
tree2 = read_dotfile('trees/treeEz1.gv')
mp3_relazioni(tree1)
mp3_relazioni(tree2)
comp2 = build_compatibilità_a_2(tree1.label_list, tree2.label_list)
comp3 = build_compatibilità_a_3_dalla_2(comp2)

for x in comp3:
    print("Terna compatibile:")
    print(x.valore)
    print("Configurazioni:")
    for y in x.configurazioni:
        print(y)
    print("---------------------")
    


 