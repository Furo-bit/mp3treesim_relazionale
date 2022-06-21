from itertools import count
from os import remove
from re import X
import networkx as nx
import numpy as np
from collections import defaultdict, Counter
from pygraphviz import AGraph
import math
import copy
import matplotlib.pyplot as plt

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

def draw_tree(tree):
    """ 
    Draw the tree using networkx's drawing methods.
    NOTE 1: Networkx uses matplotlib to display the tree. If you are using a Notebook-like
    environment (Jupyter, CoLab) it will be display automatically. 
    If you are using it from command line it will be necessary to run `plt.show()` to 
    display it.
    NOTE 2: Due to an unreliable behaviour of netxwork and pygraph it is necessary to
    create a copy of the input tree and loop over the nodes twice. Beware this in case
    you want to display very large trees.
    Parameters: 
    tree: MP3-treesim tree representation
    """

    drawtree = nx.convert_node_labels_to_integers(tree.T)
    labels = nx.get_node_attributes(drawtree, 'label')

    for node in drawtree.nodes(data=True):
        del node[1]['label']

    try:
        pos =  nx.nx_agraph.graphviz_layout(drawtree, prog="dot")#nx.nx_pydot.pydot_layout(drawtree, prog='dot')
    except:
        pos = None

    nx.draw_networkx(
        drawtree, pos=pos, labels=labels)
    
    plt.show()

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

#Metodi per MTT
    
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
                    terna = x.valore + y.valore + z.valore
                    terna = (','.join(sorted(terna)))  
                    configurazioni = configurazione_da_comp2_e_etichetta(x, y, z)
                    if terna not in terne_compatibili and configurazioni != []:
                        terne_compatibili.append(terna)
                        nuova_terna = terna_compatibile(terna, configurazioni)
                        terne_di_ritorno.append(nuova_terna)
                    else:
                        for t in terne_di_ritorno:
                            if t.valore == terna:
                                t.configurazioni += configurazioni
    for x in terne_di_ritorno:
        x.configurazioni = list(dict.fromkeys(x.configurazioni))
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



#Metodi per contrazione
def filtro_etichette_contrazione(nodi, oggetti_compatibili):
    lista_comp3 = list()
    for x in oggetti_compatibili:
        lista_comp3 += x.valore

    for nodo in nodi:
        #prendo le etichette
        etichette = nodo[1]['label']
        compatibili=""
        #le divido grazie alla virgola
        x = etichette.split(",")
        #metto in compatibili quelle buone
        for y in x:
            if y == "root" or y in lista_comp3:
                compatibili += y + ","
        if compatibili != "":
            compatibili = compatibili[:-1]
        #assegno al nodo la nuova label
        nodo[1]['label'] = compatibili

def visualizza_etichette(nodi):
    for x in nodi:
        y = x[1]['label']
        print(y)

def contrazione_comp3(tree):

    nodi_copia = copy.deepcopy(tree.nodes(data = True))
    presenza_nodi_foglia = True
  
    while(presenza_nodi_foglia):
        presenza_nodi_foglia = False
        for nodo in nodi_copia:
            if nodo[1]['label']=='': #controllo se è un nodo vuoto da contrarre              
                if len(list(tree.successors(nodo[0]))) == 0: #caso foglia, caso 1
                    #rimuovo arco tra nodo e antenato
                    antenato = list(tree.predecessors(nodo[0]))[0]
                    tree.remove_edge(antenato, nodo[0])
                    #rimuovo nodo
                    tree.remove_node(nodo[0])
        nodi_copia = copy.deepcopy(tree.nodes(data = True))
        for nodo in nodi_copia:
            if nodo[1]['label']=='':
                if len(list(tree.successors(nodo[0]))) == 0:
                    presenza_nodi_foglia = True

    nodi_copia = copy.deepcopy(tree.nodes(data = True))
    for nodo in nodi_copia:
            if nodo[1]['label']=='': #controllo se è un nodo vuoto da contrarre                
                if len(list(tree.successors(nodo[0]))) >= 1 and len(list(tree.predecessors(nodo[0]))) == 1: #caso 2 
                    #per ogni discedente, tolgo archi dal nodo
                    #per ogni discendente, collego ad antenato
                    antenato = list(tree.predecessors(nodo[0]))[0]
                    discendenti_copia = copy.deepcopy(tree.successors(nodo[0]))
                    for discendente in discendenti_copia:
                        tree.remove_edge(nodo[0], discendente)                    
                        tree.add_edge(antenato, discendente)
                    #tolgo collegamento da antenato a nodo
                    tree.remove_edge(antenato, nodo[0])
                    #tolgo nodo
                    tree.remove_node(nodo[0])
                

#Main

pathT1 = 'trees/tree1.gv' #Inserire qui il nome del primo albero
pathT2 = 'trees/tree2.gv' #Inserire qui il nome del secondo albero

file_risultati = open("Risultati.txt", "a")
file_risultati.write("Risultati di MTT per alberi fortemente divergenti su " + pathT1 + " e " + pathT2 +"\n")

tree1 = read_dotfile(pathT1) 
tree2 = read_dotfile(pathT2) 
T1 = nx.DiGraph(nx.drawing.nx_agraph.read_dot(pathT1))
T2 = nx.DiGraph(nx.drawing.nx_agraph.read_dot(pathT2))
file_risultati.write("-------------------------------"+"\n")

#Dati iniziali T1
file_risultati.write("Nodi di " + pathT1 + ":\n")
for x in T1.nodes(data=True):
    file_risultati.write(str(x))
    file_risultati.write("\n")
file_risultati.write("Archi di " + pathT1 + ":\n")
for x in T1.edges:
    file_risultati.write(str(x))
    file_risultati.write("\n")
#draw_tree(tree1)
file_risultati.write("-------------------------------"+"\n")

#Dati iniziali T2
file_risultati.write("Nodi di " + pathT2 + ":\n")
for x in T2.nodes(data=True):
    file_risultati.write(str(x))
    file_risultati.write("\n")
file_risultati.write("Archi di " + pathT2 + ":\n")
for x in T2.edges:
    file_risultati.write(str(x))
    file_risultati.write("\n")
#draw_tree(tree2)
file_risultati.write("-------------------------------"+"\n")

#Relazioni degli alberi

mp3_relazioni(tree1)
mp3_relazioni(tree2)

file_risultati.write("Relazioni di " + pathT1 + ":\n")
for x in tree1.label_list: 
    file_risultati.write("Relazioni di " + x.valore+"\n")
    file_risultati.write("Antenati: "+"\n")
    file_risultati.write(str(x.antenati)+"\n")
    file_risultati.write("Discendenti: "+"\n")
    file_risultati.write(str(x.discendenti)+"\n")
    file_risultati.write("Conviventi: "+"\n")
    file_risultati.write(str(x.conviventi)+"\n")        
    file_risultati.write("Non relazionati: "+"\n")
    file_risultati.write(str(x.non_rel)+"\n")
    file_risultati.write("-------------------------------"+"\n")

file_risultati.write("Relazioni di " + pathT2 + ":\n")
for x in tree2.label_list: 
    file_risultati.write("Relazioni di " + x.valore+"\n")
    file_risultati.write("Antenati: "+"\n")
    file_risultati.write(str(x.antenati)+"\n")
    file_risultati.write("Discendenti: "+"\n")
    file_risultati.write(str(x.discendenti)+"\n")
    file_risultati.write("Conviventi: "+"\n")
    file_risultati.write(str(x.conviventi)+"\n")        
    file_risultati.write("Non relazionati: "+"\n")
    file_risultati.write(str(x.non_rel)+"\n")
    file_risultati.write("-------------------------------"+"\n")

#Compatibilità
comp2 = build_compatibilità_a_2(tree1.label_list, tree2.label_list)
comp3 = build_compatibilità_a_3_dalla_2(comp2)
condivise = filtro_condivise(tree1.label_list, tree2.label_list)
file_risultati.write("Etichette condivise:\n")
file_risultati.write(str(sorted(condivise))+"\n")

compatibili = set()
for x in comp3:
    compatibili.add(x.valore[0])
    compatibili.add(x.valore[2])
    compatibili.add(x.valore[4])

compatibili = str(list(compatibili))
file_risultati.write("Etichette compatibili:\n")
file_risultati.write(str(sorted(compatibili)) + "\n")
file_risultati.write("---------------------" + "\n")

#Terne
file_risultati.write("Terne compatibili:" + "\n")
for x in comp3:
    file_risultati.write(x.valore + "\n")
    file_risultati.write("Configurazioni: ")
    file_risultati.write(str(x.configurazioni) + "\n")
    file_risultati.write("---------------------" + "\n")

#Contrazione e nuovi alberi

filtro_etichette_contrazione(T1.nodes(data = True), comp3)
filtro_etichette_contrazione(T2.nodes(data = True), comp3)

contrazione_comp3(T1)
contrazione_comp3(T2)

tree1 = build_tree(T1, labeled_only=False, exclude=None)
tree2 = build_tree(T2, labeled_only=False, exclude=None)

file_risultati.write("Alberi dopo la contrazione: \n")

#Dati nuovi T1
file_risultati.write("Nodi di " + pathT1 + ":\n")
for x in T1.nodes(data=True):
    file_risultati.write(str(x))
    file_risultati.write("\n")
file_risultati.write("Archi di " + pathT1 + ":\n")
for x in T1.edges:
    file_risultati.write(str(x))
    file_risultati.write("\n")
#draw_tree(tree1)
file_risultati.write("-------------------------------"+"\n")

#Dati nuovi T2
file_risultati.write("Nodi di " + pathT2 + ":\n")
for x in T2.nodes(data=True):
    file_risultati.write(str(x))
    file_risultati.write("\n")
file_risultati.write("Archi di " + pathT2 + ":\n")
for x in T2.edges:
    file_risultati.write(str(x))
    file_risultati.write("\n")
#draw_tree(tree2)
file_risultati.write("-------------------------------"+"\n")

#draw_tree(tree1)
#draw_tree(tree2)

file_risultati.write("Numero massimo di terne compatibili: ")
t_poss = math.comb(len(condivise), 3)
file_risultati.write(str(t_poss)+"\n")
file_risultati.write("Numero di terne compatibili: ")
t_comp = len(comp3)
file_risultati.write(str(t_comp)+"\n")
file_risultati.write("Valore di compatibilità: ")
if(t_poss==0):
    file_risultati.write(str(0)+"\n")
else:    
    file_risultati.write(str(t_comp/t_poss)+"\n")

file_risultati.close()




#Ideato e scritto da Andrea Furini